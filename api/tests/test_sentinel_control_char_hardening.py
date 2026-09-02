from __future__ import annotations

import api_main
import pytest
from fastapi.testclient import TestClient

SAFE_HEADERS = {"origin": "http://localhost:5173"}


@pytest.fixture
def test_client(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_WRITE_KEY", "write-secret")
    monkeypatch.setenv("API_ADMIN_KEY", "admin-secret")
    return TestClient(api_main.app)


def test_api_login_rejects_control_characters(test_client):
    # Control character in email
    res1 = test_client.post(
        "/api/login",
        json={"email": "test\nemail@example.com", "password": "valid_password"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res1.status_code == 400
    assert "Email contains invalid control characters" in res1.json()["detail"]

    # Control character in password
    res2 = test_client.post(
        "/api/login",
        json={"email": "valid_email@example.com", "password": "password\x00withnull"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res2.status_code == 400
    assert "Password contains invalid control characters" in res2.json()["detail"]


def test_api_secrets_set_rejects_control_characters(test_client, monkeypatch):
    # Mocking os.path.exists and generate_key to avoid disk side effects
    monkeypatch.setattr("api_main.os.path.exists", lambda p: True)

    # Control character in secret value
    res = test_client.post(
        "/api/secrets/set",
        json={"key": "SOME_KEY", "value": "secret\rvalue"},
        headers={"x-api-key": "admin-secret", **SAFE_HEADERS},
    )
    assert res.status_code == 400
    assert "Secret value contains invalid control characters" in res.json()["detail"]


def test_api_transfer_update_rejects_control_characters(test_client, monkeypatch):
    # Mock _transfer_by_tag and tm.update
    monkeypatch.setattr("api_main.tm.update", lambda tag, vals: None)

    async def mock_transfer(tag):
        return {"tag": tag, "url": "http://safe.com", "driver": "http"}

    monkeypatch.setattr("api_main._transfer_by_tag", mock_transfer)

    # Control character in transfer update URL
    res = test_client.post(
        "/api/transfers/12345/update",
        json={"url": "http://example.com/file\tname.zip"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res.status_code == 400
    assert "URL contains invalid control characters" in res.json()["detail"]


def test_api_secrets_unlock_rejects_control_characters(test_client):
    # Control character in key_base64
    res = test_client.post(
        "/api/secrets/unlock",
        json={"key_base64": "invalid\nkey\x00data"},
        headers={"x-api-key": "admin-secret", **SAFE_HEADERS},
    )
    assert res.status_code == 400
    assert "Key contains invalid control characters" in res.json()["detail"]


def test_api_download_and_queue_reject_priority_control_characters(test_client):
    # Control character in priority field for download
    res1 = test_client.post(
        "/api/download",
        json={"url": "https://example.com/file.zip", "priority": "HIGH\nINJECTION"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res1.status_code == 400
    assert "Priority contains invalid control characters" in res1.json()["detail"]

    # Control character in priority field for queue add
    res2 = test_client.post(
        "/api/queue",
        json={"url": "https://example.com/file.zip", "priority": "LOW\x00INJECTION"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res2.status_code == 400
    assert "Priority contains invalid control characters" in res2.json()["detail"]


def test_api_queue_item_endpoints_reject_control_characters_in_item_id(test_client):
    # Test percent-encoded newline (%0A) in URL path parameter
    res1 = test_client.delete(
        "/api/queue/550e8400-e29b-41d4-a716-446655440000%0A",
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res1.status_code == 400
    assert "Invalid queue item id" in res1.json()["detail"]

    res2 = test_client.post(
        "/api/queue/550e8400-e29b-41d4-a716-446655440000%00/start",
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res2.status_code == 400
    assert "Invalid queue item id" in res2.json()["detail"]

    # Direct function test for _parse_queue_item_id with control characters
    with pytest.raises(api_main.HTTPException) as exc_info:
        api_main._parse_queue_item_id("550e8400-e29b-41d4-a716-446655440000\r\n")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid queue item id"

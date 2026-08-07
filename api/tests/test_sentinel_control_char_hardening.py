from __future__ import annotations

import os
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
import api_main
import pytest

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
        headers={"x-api-key": "write-secret", **SAFE_HEADERS}
    )
    assert res1.status_code == 400
    assert "Email contains invalid control characters" in res1.json()["detail"]

    # Control character in password
    res2 = test_client.post(
        "/api/login",
        json={"email": "valid_email@example.com", "password": "password\x00withnull"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS}
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
        headers={"x-api-key": "admin-secret", **SAFE_HEADERS}
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
        headers={"x-api-key": "write-secret", **SAFE_HEADERS}
    )
    assert res.status_code == 400
    assert "URL contains invalid control characters" in res.json()["detail"]

from __future__ import annotations

import asyncio

import api_main
import httpx
import pytest
from fastapi.testclient import TestClient
from services.webhook_service import SafeAsyncHTTPTransport

SAFE_HEADERS = {"origin": "http://localhost:5173"}


@pytest.fixture
def test_client(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_WRITE_KEY", "write-secret")
    monkeypatch.setenv("API_ADMIN_KEY", "admin-secret")
    return TestClient(api_main.app)


def test_api_transfer_update_rejects_unsafe_urls(test_client, monkeypatch):
    # Mock tm.update and _transfer_by_tag
    monkeypatch.setattr("api_main.tm.update", lambda tag, vals: None)

    async def mock_transfer(tag):
        return {"tag": tag, "url": "http://safe.com", "driver": "http"}

    monkeypatch.setattr("api_main._transfer_by_tag", mock_transfer)

    # SSRF host check (127.0.0.1) should be rejected
    res_ssrf = test_client.post(
        "/api/transfers/12345/update",
        json={"url": "http://127.0.0.1/malicious"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res_ssrf.status_code == 400
    assert "URL host is not allowed" in res_ssrf.json()["detail"]

    # Scheme check (gopher://) should be rejected
    res_scheme = test_client.post(
        "/api/transfers/12345/update",
        json={"url": "gopher://localhost/malicious"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res_scheme.status_code == 400
    assert "Only http/https URLs are allowed" in res_scheme.json()["detail"]


def test_api_transfers_bulk_rejects_unsupported_actions(test_client):
    res = test_client.post(
        "/api/transfers/bulk",
        json={"tags": ["12345"], "action": "invalid_action"},
        headers={"x-api-key": "write-secret", **SAFE_HEADERS},
    )
    assert res.status_code == 400
    assert "Unsupported bulk action" in res.json()["detail"]


def test_safe_async_http_transport_blocks_direct_ip():
    async def run_test():
        transport = SafeAsyncHTTPTransport()
        request = httpx.Request("POST", "http://127.0.0.1/webhook")
        with pytest.raises(httpx.ConnectError) as exc_info:
            await transport.handle_async_request(request)
        assert "Direct IP is blocked" in str(exc_info.value)

    asyncio.run(run_test())


def test_transfer_metadata_update_rejects_control_characters():
    import transfer_metadata as tm
    with pytest.raises(ValueError, match="Metadata value contains invalid control characters"):
        tm.update("12345", {"tags": ["valid", "invalid\x00tag"]})

    with pytest.raises(ValueError, match="Metadata value contains invalid control characters"):
        tm.update("12345", {"url": "http://example.com/file\r\n"})

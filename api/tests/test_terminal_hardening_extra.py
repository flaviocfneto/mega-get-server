from __future__ import annotations

import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient
from security import _rate_state

client = TestClient(app)


def test_terminal_wget2_path_traversal_arbitrary_attached_flag(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # Test with -i (input-file) attached flag, which was previously unhandled
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -i/etc/shadow http://example.com/file"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: local path access outside /data" in data["output"]
    assert data["blocked_reason"] == "path_traversal_attempt"


def test_terminal_wget2_ssrf_protocol_bypass(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # Test with file:// protocol which should now be explicitly blocked in the terminal
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 file:///etc/passwd"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: untrusted host or protocol" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_wget2_ssrf_protocol_bypass_embedded(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # Test with php:// protocol embedded in a flag
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 --config=php://filter/read=convert.base64-encode/resource=api_main.py"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: untrusted host or protocol" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"

from __future__ import annotations

import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient
from security import _rate_state

client = TestClient(app)


def test_terminal_wget2_path_traversal_attached_flag(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # This should be blocked but currently might bypass if heuristics only check positional args or split by '='
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -O/etc/passwd http://example.com/file"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: local path access outside /data" in data["output"]
    assert data["blocked_reason"] == "path_traversal_attempt"


def test_terminal_lfd_file_protocol(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 file:///etc/passwd"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: untrusted host" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_generic_attached_flag_path_traversal(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # Use a flag not explicitly handled before (like -C for config file)
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -C/etc/shadow http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: local path access outside /data" in data["output"]
    assert data["blocked_reason"] == "path_traversal_attempt"


def test_terminal_wget2_ssrf_attached_flag(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # This should be blocked but currently might bypass if it only checks starts with http://
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 --base=http://127.0.0.1/ http://example.com/file"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: untrusted host" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_mega_get_path_traversal_double_slash_bypass(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # This should be blocked after the fix; previously it might have been allowed by the '//' heuristic
    response = client.post(
        "/api/terminal",
        json={"command": "mega-get /Root/file //etc/passwd"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: local path access outside /data" in data["output"]
    assert data["blocked_reason"] == "path_traversal_attempt"

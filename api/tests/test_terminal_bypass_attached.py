from __future__ import annotations

import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_terminal_bypass_ssrf_attached_flag(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")

    # This should now be blocked by the improved logic
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 --base=http://127.0.0.1/ http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("blocked_reason") == "ssrf_attempt"
    assert "untrusted host" in data.get("output", "")


def test_terminal_bypass_path_attached_short_flag(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # This should now be blocked by detecting paths in short flags
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -o/etc/passwd http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("blocked_reason") == "path_traversal_attempt"
    assert "outside /data" in data.get("output", "")


def test_terminal_mega_ls_not_confused_by_root(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    # Heuristic for MEGA remote paths should still work
    response = client.post(
        "/api/terminal",
        json={"command": "mega-ls /Root"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("blocked_reason") is None

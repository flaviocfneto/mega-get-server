from __future__ import annotations

import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient
from security import _rate_state

client = TestClient(app)
SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_terminal_tilde_bypass_blocked(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # Test mega-ls with ~ path
    res = client.post(
        "/api/terminal",
        json={"command": "mega-ls ~/some_folder"},
        headers=SAFE_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is False
    assert data["blocked_reason"] == "path_traversal_attempt"
    assert "Blocked: local path access outside" in data["output"]

    # Test wget2 with ~ output path
    res2 = client.post(
        "/api/terminal",
        json={"command": "wget2 -O ~/secret.txt http://example.com/file"},
        headers=SAFE_HEADERS,
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["ok"] is False
    assert data2["blocked_reason"] == "path_traversal_attempt"
    assert "Blocked: local path access outside" in data2["output"]


def test_terminal_tilde_equals_bypass_blocked(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # Test wget2 with --output-document=~/secret.txt
    res = client.post(
        "/api/terminal",
        json={"command": "wget2 --output-document=~/secret.txt http://example.com/file"},
        headers=SAFE_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is False
    assert data["blocked_reason"] == "path_traversal_attempt"
    assert "Blocked: local path access outside" in data["output"]

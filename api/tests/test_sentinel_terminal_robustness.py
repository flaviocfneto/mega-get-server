from __future__ import annotations

from api_main import app
from fastapi.testclient import TestClient
from security import _rate_state

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_terminal_syntax_error_unclosed_quotes(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(app) as client:
        res = client.post(
            "/api/terminal",
            json={"command": 'wget2 "http://example.com'},
            headers=SAFE_HEADERS,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is False
        assert data["blocked_reason"] == "invalid_syntax"
        assert "Blocked: invalid command syntax" in data["output"]


def test_terminal_null_byte_rejection(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(app) as client:
        res = client.post(
            "/api/terminal",
            json={"command": "mega-whoami\x00extra"},
            headers=SAFE_HEADERS,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is False
        assert data["blocked_reason"] == "injection_attempt"
        assert "Blocked: command contains restricted characters." in data["output"]

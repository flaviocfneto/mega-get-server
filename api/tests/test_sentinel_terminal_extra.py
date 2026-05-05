from __future__ import annotations

import api_main
from fastapi.testclient import TestClient

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_terminal_wget2_ssrf_blocking(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(api_main.app) as client:
        # Try to hit localhost via wget2 in terminal
        res = client.post(
            "/api/terminal", json={"command": "wget2 http://localhost:8000/api/config"}, headers=SAFE_HEADERS
        )
        assert res.status_code == 200
        assert res.json()["ok"] is False
        assert res.json()["blocked_reason"] == "ssrf_attempt"
        assert "Blocked: untrusted host" in res.json()["output"]


def test_terminal_path_traversal_via_flag(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(api_main.app) as client:
        # Try to bypass via flag
        res = client.post(
            "/api/terminal",
            json={"command": "wget2 --output-document=/etc/passwd https://google.com"},
            headers=SAFE_HEADERS,
        )
        assert res.status_code == 200
        assert res.json()["ok"] is False
        assert res.json()["blocked_reason"] == "path_traversal_attempt"
        assert "Blocked: local path access outside" in res.json()["output"]


def test_terminal_path_traversal_via_dotdot_flag(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(api_main.app) as client:
        res = client.post(
            "/api/terminal", json={"command": "wget2 -O ../secret.key https://google.com"}, headers=SAFE_HEADERS
        )
        assert res.status_code == 200
        assert res.json()["ok"] is False
        assert res.json()["blocked_reason"] == "path_traversal_attempt"

from __future__ import annotations

try:
    import api_main
except ImportError:
    from api import api_main
from fastapi.testclient import TestClient

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_terminal_ssrf_bypass_flag(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")

    with TestClient(api_main.app) as client:
        # Currently, this might bypass SSRF check because it only checks if the part STARTS with http
        res = client.post(
            "/api/terminal",
            json={"command": "wget2 --base=http://127.0.0.1 http://google.com"},
            headers={"x-api-key": "secret-admin", **SAFE_HEADERS},
        )
    # If it's NOT blocked, it's a bypass. We want it to be blocked.
    # We expect blocked_reason: ssrf_attempt if we fix it.
    assert res.status_code == 200
    assert res.json().get("blocked_reason") == "ssrf_attempt"


def test_terminal_ssrf_bypass_case_insensitive(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")

    with TestClient(api_main.app) as client:
        res = client.post(
            "/api/terminal",
            json={"command": "wget2 HTTP://127.0.0.1"},
            headers={"x-api-key": "secret-admin", **SAFE_HEADERS},
        )
    assert res.status_code == 200
    assert res.json().get("blocked_reason") == "ssrf_attempt"


def test_terminal_ssrf_bypass_ftp(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")

    with TestClient(api_main.app) as client:
        res = client.post(
            "/api/terminal",
            json={"command": "wget2 ftp://127.0.0.1"},
            headers={"x-api-key": "secret-admin", **SAFE_HEADERS},
        )
    assert res.status_code == 200
    assert res.json().get("blocked_reason") == "ssrf_attempt"

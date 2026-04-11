from __future__ import annotations

from fastapi.testclient import TestClient

import api_main
import mega_service as ms
import security

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_terminal_requires_auth_in_strict_mode(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")
    with TestClient(api_main.app) as client:
        res = client.post("/api/terminal", json={"command": "mega-version"})
    assert res.status_code == 401


def test_terminal_allows_auth_in_strict_mode(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")

    async def fake_run(_args):
        return {"ok": True, "exit_code": 0, "stdout": "ok", "output": "ok"}

    monkeypatch.setattr(api_main.ms, "run_megacmd_command", fake_run)
    with TestClient(api_main.app) as client:
        res = client.post(
            "/api/terminal",
            json={"command": "mega-version"},
            headers={"x-api-key": "secret-admin", **SAFE_HEADERS},
        )
    assert res.status_code == 200
    assert res.json().get("ok") is True


def test_logs_are_redacted():
    with TestClient(api_main.app) as client:
        ms.log_buffer.append("mega-login user@example.com secret")
        res = client.get("/api/logs")
    assert res.status_code == 200
    body = res.json()
    assert any("***" in line for line in body)


def test_download_rejects_non_mega_urls():
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://example.com/file.zip"}, headers=SAFE_HEADERS)
    assert res.status_code == 400


def test_csrf_blocks_missing_origin_for_unsafe_routes():
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"})
    assert res.status_code == 403
    assert "csrf boundary violation" in res.json()["detail"].lower()


def test_csrf_blocks_untrusted_origin():
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"}, headers={"origin": "https://evil.example"})
    assert res.status_code == 403


def test_rate_limit_hits_429_on_terminal(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")

    async def fake_run(_args):
        return {"ok": True, "exit_code": 0, "stdout": "ok", "output": "ok"}

    monkeypatch.setattr(api_main.ms, "run_megacmd_command", fake_run)
    security._rate_state.clear()

    with TestClient(api_main.app) as client:
        for _ in range(15):
            ok = client.post("/api/terminal", json={"command": "mega-version"}, headers={"x-api-key": "secret-admin", **SAFE_HEADERS})
            assert ok.status_code == 200
        limited = client.post("/api/terminal", json={"command": "mega-version"}, headers={"x-api-key": "secret-admin", **SAFE_HEADERS})
    assert limited.status_code == 429


def test_rate_limit_resets_after_window(monkeypatch):
    base = {"t": 1_000_000.0}

    def fake_now():
        return base["t"]

    monkeypatch.setattr(security.time, "time", fake_now)
    security._rate_state.clear()

    with TestClient(api_main.app) as client:
        for _ in range(10):
            r = client.post("/api/login", json={"email": "x@example.com", "password": "bad"}, headers=SAFE_HEADERS)
            assert r.status_code in (200, 400)
        limited = client.post("/api/login", json={"email": "x@example.com", "password": "bad"}, headers=SAFE_HEADERS)
        assert limited.status_code == 429
        base["t"] += 61.0
        reset = client.post("/api/login", json={"email": "x@example.com", "password": "bad"}, headers=SAFE_HEADERS)
        assert reset.status_code != 429


def test_cookie_session_mode_requires_origin_plus_token(monkeypatch):
    monkeypatch.setenv("API_AUTH_TRANSPORT", "cookie_session")
    monkeypatch.setenv("CSRF_ENFORCEMENT_MODE", "origin_only")
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"}, headers=SAFE_HEADERS)
    assert res.status_code == 503
    assert "cookie_session requires origin_plus_token" in res.json()["detail"]


def test_cookie_session_mode_rejects_missing_csrf_token(monkeypatch):
    monkeypatch.setenv("API_AUTH_TRANSPORT", "cookie_session")
    monkeypatch.setenv("CSRF_ENFORCEMENT_MODE", "origin_plus_token")
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"}, headers=SAFE_HEADERS)
    assert res.status_code == 403
    assert "missing csrf token" in res.json()["detail"].lower()


def test_cookie_session_mode_accepts_valid_csrf_token(monkeypatch):
    monkeypatch.setenv("API_AUTH_TRANSPORT", "cookie_session")
    monkeypatch.setenv("CSRF_ENFORCEMENT_MODE", "origin_plus_token")
    with TestClient(api_main.app) as client:
        res = client.post(
            "/api/download",
            json={"url": "https://mega.nz/file/abc"},
            headers={**SAFE_HEADERS, "x-csrf-token": "ok-token"},
        )
    assert res.status_code == 200


def test_header_key_mode_preserves_existing_origin_only_behavior(monkeypatch):
    monkeypatch.setenv("API_AUTH_TRANSPORT", "header_key")
    monkeypatch.setenv("CSRF_ENFORCEMENT_MODE", "origin_only")
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"}, headers=SAFE_HEADERS)
    assert res.status_code == 200


def test_diag_commands_export_keeps_redacted_command_args(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")
    api_main.ms._command_events.clear()
    api_main.ms._command_events.append(
        {
            "ok": False,
            "command": "mega-login *** ***",
            "output": "failed",
            "exit_code": 1,
            "timestamp": 0,
        }
    )
    with TestClient(api_main.app) as client:
        res = client.get("/api/diag/commands", headers={"x-api-key": "secret-admin"})
    assert res.status_code == 200
    body = res.json()
    assert body["events"][0]["command"] == "mega-login *** ***"
    assert "user@example.com" not in body["events"][0]["command"]
    assert "secret" not in body["events"][0]["command"]

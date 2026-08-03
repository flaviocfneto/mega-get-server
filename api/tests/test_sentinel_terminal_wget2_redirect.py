from __future__ import annotations

from typing import Any

import mega_service as ms
import pytest
import security
from api_main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    security._rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")


def test_terminal_wget2_no_redirect_appended(monkeypatch):
    captured_args: list[str] = []

    async def fake_run(args: list[str], **kwargs: Any) -> dict[str, Any]:
        captured_args.extend(args)
        return {"ok": True, "exit_code": 0, "stdout": "ok", "output": "ok"}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_run)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /data/out"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    # Verify that --max-redirect=0 was automatically appended to command arguments
    assert "--max-redirect=0" in captured_args


def test_terminal_wget2_non_zero_redirect_blocked_equals():
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /data/out --max-redirect=5"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["blocked_reason"] == "ssrf_attempt"
    assert "Blocked: --max-redirect must be 0" in data["output"]


def test_terminal_wget2_non_zero_redirect_blocked_space():
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /data/out --max-redirect 10"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["blocked_reason"] == "ssrf_attempt"
    assert "Blocked: --max-redirect must be 0" in data["output"]


def test_terminal_wget2_zero_redirect_allowed_equals(monkeypatch):
    captured_args: list[str] = []

    async def fake_run(args: list[str], **kwargs: Any) -> dict[str, Any]:
        captured_args.extend(args)
        return {"ok": True, "exit_code": 0, "stdout": "ok", "output": "ok"}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_run)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /data/out --max-redirect=0"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "--max-redirect=0" in captured_args
    # It shouldn't append it again if already present
    assert captured_args.count("--max-redirect=0") == 1


def test_terminal_wget2_zero_redirect_allowed_space(monkeypatch):
    captured_args: list[str] = []

    async def fake_run(args: list[str], **kwargs: Any) -> dict[str, Any]:
        captured_args.extend(args)
        return {"ok": True, "exit_code": 0, "stdout": "ok", "output": "ok"}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_run)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /data/out --max-redirect 0"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "--max-redirect" in captured_args
    assert "0" in captured_args

from __future__ import annotations

import api_main
import mega_service as ms
import security
from fastapi.testclient import TestClient

client = TestClient(api_main.app)


def test_terminal_allows_wget2(monkeypatch):
    security._rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    async def fake_run(args, **kwargs):
        return {"ok": True, "exit_code": 0, "stdout": "ok", "output": "ok"}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_run)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /data/out"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_terminal_blocks_wget2_outside_data(monkeypatch):
    security._rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 http://example.com/file -O /etc/passwd"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["blocked_reason"] == "path_traversal_attempt"

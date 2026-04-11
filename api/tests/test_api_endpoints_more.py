from __future__ import annotations

from fastapi.testclient import TestClient

import api_main

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_logout_success_and_error(monkeypatch):
    async def fake_logout_cmd(_args):
        return {"ok": True, "output": "bye"}

    async def logged_out():
        return {"is_logged_in": False}

    async def still_logged_in():
        return {"is_logged_in": True}

    monkeypatch.setattr(api_main.ms, "run_megacmd_command", fake_logout_cmd)
    monkeypatch.setattr(api_main.ms, "get_account_info", logged_out)
    with TestClient(api_main.app) as client:
        ok = client.post("/api/logout", headers=SAFE_HEADERS)
    assert ok.status_code == 200
    assert ok.json()["status"] == "success"

    monkeypatch.setattr(api_main.ms, "get_account_info", still_logged_in)
    with TestClient(api_main.app) as client:
        bad = client.post("/api/logout", headers=SAFE_HEADERS)
    assert bad.status_code == 200
    assert bad.json()["status"] == "error"


def test_terminal_requires_command_and_blocks_not_allowlisted():
    with TestClient(api_main.app) as client:
        missing = client.post("/api/terminal", json={"command": "   "}, headers=SAFE_HEADERS)
        blocked = client.post("/api/terminal", json={"command": "rm -rf /"}, headers=SAFE_HEADERS)

    assert missing.status_code == 400
    assert blocked.status_code == 200
    assert blocked.json()["ok"] is False
    assert blocked.json()["blocked_reason"] == "not_in_allowlist"


def test_terminal_allowlisted_command_executes(monkeypatch):
    async def fake_run(args):
        assert args[0] == "mega-version"
        return {"ok": True, "exit_code": 0, "stdout": "v1.0"}

    monkeypatch.setattr(api_main.ms, "run_megacmd_command", fake_run)
    with TestClient(api_main.app) as client:
        res = client.post("/api/terminal", json={"command": "mega-version"}, headers=SAFE_HEADERS)
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "v1.0" in res.json()["output"]


def test_download_requires_url():
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "  "}, headers=SAFE_HEADERS)
    assert res.status_code == 400


def test_download_success_schedules_job(monkeypatch):
    called = {"history": None, "task": False}

    def fake_hist(url):
        called["history"] = url

    async def fake_run(url, labels, pr):
        called["ran"] = url
        return True, None

    def fake_create_task(coro):
        called["task"] = True
        coro.close()
        return None

    monkeypatch.setattr(api_main.ms, "add_url_to_history", fake_hist)
    monkeypatch.setattr(api_main.ms, "run_mega_get_with_user_meta", fake_run)
    monkeypatch.setattr(api_main.asyncio, "create_task", fake_create_task)

    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"}, headers=SAFE_HEADERS)
    assert res.status_code == 200
    assert called["history"] == "https://mega.nz/file/abc"
    assert called["task"] is True


def test_transfer_endpoints_delegate_to_service(monkeypatch):
    calls = []

    async def fake_action(action, tag):
        calls.append((action, tag))

    async def fake_resume(tag, *, log_label):
        calls.append((log_label.lower(), tag))

    async def fake_cancel_all():
        calls.append(("cancel-all", "*"))

    monkeypatch.setattr(api_main.ms, "run_mega_transfers_action", fake_action)
    monkeypatch.setattr(api_main.ms, "run_mega_transfers_resume_for_tag", fake_resume)
    monkeypatch.setattr(api_main.ms, "run_mega_transfers_cancel_all", fake_cancel_all)

    with TestClient(api_main.app) as client:
        assert client.post("/api/transfers/1/pause", headers=SAFE_HEADERS).status_code == 200
        assert client.post("/api/transfers/1/resume", headers=SAFE_HEADERS).status_code == 200
        assert client.post("/api/transfers/1/retry", headers=SAFE_HEADERS).status_code == 200
        assert client.post("/api/transfers/1/cancel", headers=SAFE_HEADERS).status_code == 200
        assert client.post("/api/transfers/cancel-all", headers=SAFE_HEADERS).status_code == 200

    assert ("pause", "1") in calls
    assert ("resume", "1") in calls
    assert ("retry", "1") in calls
    assert ("cancel", "1") in calls
    assert ("cancel-all", "*") in calls


def test_history_and_logs_delete(monkeypatch):
    cleared = {"history": False, "logs": False}

    def fake_clear_history():
        cleared["history"] = True

    def fake_logs_clear():
        cleared["logs"] = True

    monkeypatch.setattr(api_main.ms, "clear_history", fake_clear_history)
    monkeypatch.setattr(api_main.ms.log_buffer, "clear", fake_logs_clear)
    monkeypatch.setattr(api_main.ms.log_buffer, "append", lambda _msg: None)

    with TestClient(api_main.app) as client:
        h = client.delete("/api/history", headers=SAFE_HEADERS)
        l = client.delete("/api/logs", headers=SAFE_HEADERS)
    assert h.status_code == 200
    assert l.status_code == 200
    assert cleared["history"] is True
    assert cleared["logs"] is True

from __future__ import annotations

import asyncio
import json
import os

import mega_service as ms


def test_load_dotenv_if_present_reads_and_ignores_comments(tmp_path, monkeypatch):
    (tmp_path / "api").mkdir(parents=True, exist_ok=True)
    env_path = tmp_path / ".env"
    env_path.write_text("# comment\nA=1\nB = two\nEMPTY=\n", encoding="utf-8")

    monkeypatch.setattr(ms, "__file__", str(tmp_path / "api" / "mega_service.py"))
    monkeypatch.delenv("A", raising=False)
    monkeypatch.delenv("B", raising=False)
    ms.load_dotenv_if_present()
    assert os.environ.get("A") == "1"
    assert os.environ.get("B") == "two"


def test_history_load_and_save_roundtrip(tmp_path, monkeypatch):
    history = tmp_path / "history.json"
    history.write_text(json.dumps(["u1", "u2", 5]), encoding="utf-8")
    ms.set_history_path(str(history))
    ms.load_history()
    assert ms.get_history()[:2] == ["u1", "u2"]

    ms.add_url_to_history("u3")
    loaded = json.loads(history.read_text(encoding="utf-8"))
    assert loaded[0] == "u3"


def test_mega_cmd_server_binary_darwin_megacmd_bundle(monkeypatch, tmp_path):
    fake_bin = tmp_path / "MEGAcmd"
    fake_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(ms, "MEGACMD_PATH", str(tmp_path))
    monkeypatch.setattr(ms.sys, "platform", "darwin")
    monkeypatch.setattr(ms.shutil, "which", lambda *args, **kwargs: None)
    monkeypatch.setattr(ms.os.path, "isfile", lambda p: p == str(fake_bin))
    monkeypatch.setattr(ms.os, "access", lambda p, _mode: p == str(fake_bin))
    assert ms.mega_cmd_server_binary() == str(fake_bin)


def test_wait_for_mega_server_ready_timeout_and_oserror(monkeypatch):
    class _Loop:
        def __init__(self):
            self.t = 0.0

        def time(self):
            self.t += 1.0
            return self.t

    async def fake_exec(*args, **kwargs):
        raise OSError("boom")

    _orig_sleep = ms.asyncio.sleep
    loop = _Loop()
    monkeypatch.setattr(ms.asyncio, "get_event_loop", lambda: loop)
    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(ms.asyncio, "sleep", lambda _s: _orig_sleep(0))
    assert asyncio.run(ms.wait_for_mega_server_ready(max_wait_sec=2.0)) is False


def test_ensure_server_start_failure_still_checks_ready(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "in_docker", lambda: False)
    monkeypatch.setattr(ms, "mega_cmd_server_binary", lambda: "mega-cmd-server")

    async def fake_exec(*args, **kwargs):
        raise RuntimeError("cannot start")

    async def fake_ready():
        return True

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(ms, "wait_for_mega_server_ready", fake_ready)
    monkeypatch.setattr(ms.asyncio, "sleep", lambda _s: asyncio.sleep(0))
    assert asyncio.run(ms.ensure_mega_cmd_server_running()) is True


def test_transfer_actions_non_simulated_error_and_success(monkeypatch):
    ms.log_buffer.clear()
    monkeypatch.setattr(ms, "SIMULATE", False)

    async def fail_exec(flag, target):
        return (1, "oops", "details")

    async def ok_exec(flag, target):
        return (0, "done", "")

    monkeypatch.setattr(ms, "_mega_transfers_exec", fail_exec)
    asyncio.run(ms.run_mega_transfers_action("pause", "7"))
    logs = "\n".join(ms.log_buffer.get_lines()).lower()
    assert "failed for transfer 7" in logs

    ms.log_buffer.clear()
    monkeypatch.setattr(ms, "_mega_transfers_exec", ok_exec)
    asyncio.run(ms.run_mega_transfers_action("pause", "7"))
    logs2 = "\n".join(ms.log_buffer.get_lines()).lower()
    assert "command sent for transfer 7" in logs2

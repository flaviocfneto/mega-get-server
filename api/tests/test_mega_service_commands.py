from __future__ import annotations

import asyncio
import json
from pathlib import Path

import mega_service as ms


class _FakeProc:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


def test_subprocess_env_prepends_megacmd_path(monkeypatch):
    monkeypatch.setattr(ms, "MEGACMD_PATH", "/opt/megacmd")
    env = ms.subprocess_env()
    assert env["PATH"].startswith("/opt/megacmd")


def test_mega_cmd_server_binary_uses_which(monkeypatch):
    monkeypatch.setattr(ms, "MEGACMD_PATH", "")
    monkeypatch.setattr(ms.shutil, "which", lambda name, path=None: "/usr/bin/mega-cmd-server" if name == "mega-cmd-server" else None)
    assert ms.mega_cmd_server_binary() == "mega-cmd-server"


def test_mega_transfers_exec_handles_none_returncode(monkeypatch):
    async def fake_exec(*args, **kwargs):
        return _FakeProc(b"ok", b"", None)

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    rc, out, err = asyncio.run(ms._mega_transfers_exec("-c", "1"))
    assert rc == -1
    assert out == "ok"
    assert err == ""


def test_run_megacmd_command_success(monkeypatch):
    async def fake_exec(*args, **kwargs):
        return _FakeProc(b"done\n", b"", 0)

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    ms.log_buffer.clear()
    event = asyncio.run(ms.run_megacmd_command(["mega-version"]))
    assert event["ok"] is True
    assert event["output"] == "done"


def test_run_megacmd_command_exception_path(monkeypatch):
    async def fake_exec(*args, **kwargs):
        raise OSError("not found")

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    ms.log_buffer.clear()
    event = asyncio.run(ms.run_megacmd_command(["mega-version"]))
    assert event["ok"] is False
    assert event["exit_code"] == -1
    assert any("Command failed" in line for line in ms.log_buffer.get_lines())


def test_command_probe_runs_three_commands(monkeypatch):
    called = []

    async def fake_run(args):
        called.append(args)
        return {"ok": True, "command": " ".join(args)}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_run)
    out = asyncio.run(ms.command_probe())
    assert len(out) == 3
    assert called[0] == ["mega-version"]
    assert called[1] == ["mega-whoami"]


def test_run_transfer_actions_simulate_mode(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", True)
    ms.log_buffer.clear()
    asyncio.run(ms.run_mega_transfers_action("pause", "11"))
    asyncio.run(ms.run_mega_transfers_resume_for_tag("11", log_label="Retry"))
    asyncio.run(ms.run_mega_transfers_cancel_all())
    logs = "\n".join(ms.log_buffer.get_lines())
    assert "simulated" in logs.lower()


def test_redact_sensitive_text_corpus():
    fixture_path = Path(__file__).parent / "fixtures" / "redaction_corpus_v1.json"
    corpus = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert corpus["version"] == "v1"
    for case in corpus["cases"]:
        redacted = ms.redact_sensitive_text(case["input"])
        assert redacted == case["expected"], f"unexpected redaction output for case={case['name']}"
        for secret in case.get("must_not_contain", []):
            assert secret not in redacted, f"secret leaked for case={case['name']}"

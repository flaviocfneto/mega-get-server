from __future__ import annotations

import asyncio

import mega_service as ms


class _FakeProc:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


def test_run_mega_get_simulate(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", True)
    ms.log_buffer.clear()
    ok, err = asyncio.run(ms.run_mega_get("https://mega.nz/file/sim"))
    assert ok is True and err is None
    assert any("simulated" in line.lower() for line in ms.log_buffer.get_lines())


def test_run_mega_get_success_path(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/tmp")
    _orig_sleep = ms.asyncio.sleep
    monkeypatch.setattr(ms.asyncio, "sleep", lambda _s: _orig_sleep(0))

    calls = []

    async def fake_exec(*args, **kwargs):
        calls.append(args)
        if args[0] == "mega-get":
            return _FakeProc(b"accepted", b"", 0)
        return _FakeProc(b"", b"", 0)

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    ms.log_buffer.clear()
    ok, err = asyncio.run(ms.run_mega_get("https://mega.nz/file/ok"))
    assert ok is True and err is None
    logs = "\n".join(ms.log_buffer.get_lines())
    assert "accepted" in logs.lower() or "download command accepted" in logs.lower()
    assert any(c[0] == "mega-transfers" for c in calls)


def test_run_mega_get_retries_on_segfault(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/tmp")
    _orig_sleep = ms.asyncio.sleep
    monkeypatch.setattr(ms.asyncio, "sleep", lambda _s: _orig_sleep(0))

    responses = [
        _FakeProc(b"", b"segmentation fault", 1),
        _FakeProc(b"ok", b"", 0),
        _FakeProc(b"", b"", 0),
    ]

    async def fake_exec(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    ms.log_buffer.clear()
    ok, err = asyncio.run(ms.run_mega_get("https://mega.nz/file/retry"))
    assert ok is True
    logs = "\n".join(ms.log_buffer.get_lines()).lower()
    assert "retrying without explicit destination" in logs


def test_run_mega_get_already_exists_message(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/tmp")

    async def fake_exec(*args, **kwargs):
        return _FakeProc(b"", b"File already exists", 1)

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    ms.log_buffer.clear()
    ok, err = asyncio.run(ms.run_mega_get("https://mega.nz/file/existing"))
    assert ok is True
    assert any("already exists" in line.lower() for line in ms.log_buffer.get_lines())

from __future__ import annotations

import os
import stat
from pathlib import Path

import mega_service
from services.json_store import write_json_atomic


def test_json_store_writes_with_strict_permissions(tmp_path: Path) -> None:
    test_file = tmp_path / "test_store.json"
    data = {"key": "value"}
    write_json_atomic(test_file, data)

    assert test_file.exists()
    # Check that file permissions are 0o600 on UNIX-like platforms
    if os.name == "posix":
        mode = test_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_save_history_writes_with_strict_permissions(tmp_path: Path, monkeypatch) -> None:
    history_file = tmp_path / "test_history.json"
    monkeypatch.setattr(mega_service, "_url_history", ["https://mega.nz/file/1", "https://mega.nz/file/2"])
    monkeypatch.setattr(mega_service, "_history_file_path", str(history_file))

    mega_service.save_history()

    assert history_file.exists()
    if os.name == "posix":
        mode = history_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_daily_analytics_writes_with_strict_permissions(tmp_path: Path, monkeypatch) -> None:
    import api_main

    analytics_file = tmp_path / "test_analytics.json"
    monkeypatch.setattr(api_main, "DAILY_ANALYTICS_PATH", analytics_file)
    monkeypatch.setattr(api_main, "_daily_loaded", True)
    monkeypatch.setattr(api_main, "_daily_buckets", {"2026-08-03": {"bytes": 100, "count": 1}})

    api_main._persist_daily_buckets()

    assert analytics_file.exists()
    if os.name == "posix":
        mode = analytics_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_http_download_writes_with_strict_permissions(tmp_path: Path, monkeypatch) -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    import http_downloads as hd

    monkeypatch.setattr(mega_service, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(mega_service, "SIMULATE", False)
    monkeypatch.setattr(hd, "_resolved_http_download_executable", lambda: "/bin/true")
    monkeypatch.setattr(hd, "_resolve_and_validate_url", AsyncMock(return_value=("https://example.com/z.bin", 1024)))

    async def fake_exec(*args, **kwargs):
        # Find output path from args
        argv = list(args)
        o_idx = argv.index("-O")
        out_path = argv[o_idx + 1]

        # Verify that the file was ALREADY pre-created with 0o600 before wget2 is even executed (TOCTOU protection!)
        if os.name == "posix":
            assert os.path.isfile(out_path)
            mode = os.stat(out_path).st_mode
            assert stat.S_IMODE(mode) == 0o600

        # Simulate writing the downloaded bytes
        with open(out_path, "wb") as f:
            f.write(b"downloaded contents")

        proc = MagicMock()
        proc.pid = 4242
        proc.returncode = 0

        class _Stderr:
            async def readline(self):
                return b""

        proc.stderr = _Stderr()
        proc.wait = AsyncMock(return_value=0)
        proc.terminate = MagicMock()
        proc.kill = MagicMock()
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/z.bin", labels=[], priority="NORMAL")

    async def main():
        await hd._run_job_inner(job, None)

    asyncio.run(main())

    assert job.state == "COMPLETED"
    assert os.path.isfile(job.output_file)
    if os.name == "posix":
        mode = os.stat(job.output_file).st_mode
        assert stat.S_IMODE(mode) == 0o600

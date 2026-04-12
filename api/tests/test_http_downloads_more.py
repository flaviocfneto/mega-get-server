"""Additional http_downloads coverage: registry, lifecycle helpers, and mocked subprocess paths."""
from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

import http_downloads as hd
import mega_service as ms
import transfer_metadata as tm


@pytest.fixture(autouse=True)
def clear_http_registry():
    hd._registry.clear()
    yield
    hd._registry.clear()


@pytest.fixture
def meta_path(tmp_path, monkeypatch):
    p = tmp_path / "transfer_metadata.json"
    monkeypatch.setattr(tm, "META_PATH", p)
    return p


def test_http_downloads_enabled_default():
    assert hd.http_downloads_enabled() is True


def test_http_downloads_disabled(monkeypatch):
    monkeypatch.setenv("HTTP_DOWNLOADS_ENABLED", "0")
    assert hd.http_downloads_enabled() is False


def test_validate_http_empty():
    with pytest.raises(ValueError, match="URL"):
        hd.validate_http_download_url("")


def test_validate_http_wrong_scheme():
    with pytest.raises(ValueError, match="http"):
        hd.validate_http_download_url("ftp://example.com/x")


def test_normalize_download_url_empty():
    with pytest.raises(ValueError):
        hd.normalize_download_url("")


def test_normalize_download_url_bad_scheme():
    with pytest.raises(ValueError):
        hd.normalize_download_url("ftp://mega.nz/x")


def test_normalize_when_http_disabled(monkeypatch):
    monkeypatch.setenv("HTTP_DOWNLOADS_ENABLED", "0")
    with pytest.raises(ValueError):
        hd.normalize_download_url("https://example.com/x")


def test_parse_wget_stderr_no_percent():
    assert hd.parse_wget_stderr_progress("no match") == (None, None)


def test_fetch_content_length_head_none(monkeypatch):
    monkeypatch.setattr(hd, "urlopen", MagicMock(side_effect=OSError("nope")))
    assert hd.fetch_content_length_head("https://example.com/x") is None


def test_safe_output_basename_empty_path():
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    name = hd._safe_output_basename("https://example.com/", tag)
    assert "download" in name
    assert tag.replace("h-", "")[:8] in name


def test_job_to_api_row_progress_from_bytes(meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/f.bin", labels=["x"], priority="HIGH")
    job.output_file = "/data/f.bin"
    job.size_bytes = 100
    job.downloaded_bytes = 50
    job.progress_pct = 0.0
    row = hd.job_to_api_row(job)
    assert row["progress_pct"] == 50.0
    assert row["driver"] == "http"
    assert row["filename"] == "f.bin"


def test_job_to_api_row_with_metadata(meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    tm.update(tag, {"url": "https://other/x", "priority": "LOW", "speed_limit_kbps": 400, "tags": ["m"]})
    job = hd.HttpJob(tag=tag, url="https://example.com/a", labels=[], priority="NORMAL")
    row = hd.job_to_api_row(job)
    assert row["url"] == "https://other/x"
    assert row["priority"] == "LOW"
    assert row["speed_limit_kbps"] == 400
    assert row["tags"] == ["m"]


def test_list_and_get_transfer_row(meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://x/y", labels=[], priority="NORMAL")
    hd._registry[tag] = job
    rows = hd.list_api_rows()
    assert len(rows) == 1
    assert hd.get_transfer_row(tag) is not None
    assert hd.get_transfer_row("h-00000000-0000-4000-8000-000000000001") is None


def test_http_pause_not_found():
    async def main():
        return await hd.http_pause("h-550e8400-e29b-41d4-a716-446655440000")

    ok, err = asyncio.run(main())
    assert ok is False
    assert err == "Transfer not found"


def test_http_resume_not_found():
    async def main():
        return await hd.http_resume("h-550e8400-e29b-41d4-a716-446655440000")

    ok, err = asyncio.run(main())
    assert ok is False


def test_http_cancel_not_found():
    async def main():
        return await hd.http_cancel("h-550e8400-e29b-41d4-a716-446655440000")

    ok, err = asyncio.run(main())
    assert ok is False
    assert err == "Transfer not found"


def test_http_retry_not_found(meta_path):
    async def main():
        return await hd.http_retry("h-550e8400-e29b-41d4-a716-446655440000")

    ok, err = asyncio.run(main())
    assert ok is False
    assert err == "Transfer not found"


def test_http_retry_invalid_url(meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/ok", labels=[], priority="NORMAL")
    hd._registry[tag] = job
    tm.update(tag, {"url": "http://127.0.0.1/nope"})

    async def main():
        return await hd.http_retry(tag)

    ok, err = asyncio.run(main())
    assert ok is False
    assert err


def test_cancel_all_http_empty():
    asyncio.run(hd.cancel_all_http_downloads())


def test_resolved_http_download_executable_absent(monkeypatch):
    monkeypatch.delenv("WGET_HTTP_BIN", raising=False)
    monkeypatch.setattr(hd.shutil, "which", lambda *a, **k: None)
    assert hd._resolved_http_download_executable() is None


def test_resolved_http_download_executable_abs_path(tmp_path, monkeypatch):
    exe = tmp_path / "wget2"
    exe.write_text("#!/bin/sh\necho\n")
    os.chmod(exe, 0o755)
    monkeypatch.setenv("WGET_HTTP_BIN", str(exe))
    assert hd._resolved_http_download_executable() == str(exe)


def test_run_job_inner_missing_client(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(hd, "_resolved_http_download_executable", lambda: None)
    async def immediate_to_thread(fn, /, *a, **kw):
        return fn(*a, **kw)

    monkeypatch.setattr(hd.asyncio, "to_thread", immediate_to_thread)

    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/file.bin", labels=[], priority="NORMAL")

    async def main():
        await hd._run_job_inner(job, None)

    asyncio.run(main())
    assert job.state == "FAILED"
    le = (job.last_error or "").lower()
    assert "not found" in le or "wget2" in le


def test_run_job_inner_wget2_success(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(hd, "_resolved_http_download_executable", lambda: "/bin/true")

    async def immediate_to_thread(fn, /, *a, **kw):
        return fn(*a, **kw)

    monkeypatch.setattr(hd.asyncio, "to_thread", immediate_to_thread)

    out_file_holder: list[str] = []

    async def fake_exec(*args, **kwargs):
        argv = list(args)
        o_idx = argv.index("-O")
        out_path = argv[o_idx + 1]
        out_file_holder.append(out_path)
        with open(out_path, "wb") as f:
            f.write(b"done")
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

    monkeypatch.setattr(hd.asyncio, "create_subprocess_exec", fake_exec)

    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/z.bin", labels=[], priority="NORMAL")

    async def main():
        await hd._run_job_inner(job, None)

    asyncio.run(main())
    assert job.state == "COMPLETED"
    assert out_file_holder and os.path.isfile(out_file_holder[0])


def test_run_job_inner_wget2_nonzero_exit(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(hd, "_resolved_http_download_executable", lambda: "/bin/false")

    async def immediate_to_thread(fn, /, *a, **kw):
        return fn(*a, **kw)

    monkeypatch.setattr(hd.asyncio, "to_thread", immediate_to_thread)

    async def fake_exec(*args, **kwargs):
        argv = list(args)
        o_idx = argv.index("-O")
        out_path = argv[o_idx + 1]
        if os.path.isfile(out_path):
            os.remove(out_path)
        proc = MagicMock()
        proc.pid = 4243
        proc.returncode = 7

        class _Stderr:
            async def readline(self):
                return b""

        proc.stderr = _Stderr()
        proc.wait = AsyncMock(return_value=0)
        proc.terminate = MagicMock()
        proc.kill = MagicMock()
        return proc

    monkeypatch.setattr(hd.asyncio, "create_subprocess_exec", fake_exec)

    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/bad.bin", labels=[], priority="NORMAL")

    async def main():
        await hd._run_job_inner(job, None)

    asyncio.run(main())
    assert job.state == "FAILED"
    assert "wget2 exited" in (job.last_error or "")


def test_http_cancel_terminates_running(tmp_path, monkeypatch, meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/x", labels=[], priority="NORMAL")
    proc = MagicMock()
    proc.returncode = None
    proc.terminate = MagicMock()
    proc.kill = MagicMock()
    proc.wait = AsyncMock(return_value=0)
    job.proc = proc
    hd._registry[tag] = job

    ok, err = asyncio.run(hd.http_cancel(tag))
    assert ok is True
    proc.terminate.assert_called_once()


def test_task_runner_sets_failed_on_exception(meta_path, monkeypatch):
    async def boom(_j, _p):
        raise RuntimeError("boom")

    monkeypatch.setattr(hd, "_run_job_inner", boom)
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/x", labels=[], priority="NORMAL")
    asyncio.run(hd._http_download_task_runner(tag, None, job))
    assert hd._registry.get(tag) is not None
    assert hd._registry[tag].state == "FAILED"


def test_stderr_consumer_reads_line():
    async def run():
        job = hd.HttpJob(
            tag="h-550e8400-e29b-41d4-a716-446655440000",
            url="https://x",
            labels=[],
            priority="NORMAL",
        )
        job.size_bytes = 100

        class P:
            stderr = asyncio.StreamReader()

        async def feed():
            P.stderr.feed_data(b" 10% done\n")
            P.stderr.feed_eof()

        job.proc = P()
        hd._registry[job.tag] = job
        t = asyncio.create_task(hd._stderr_consumer(job))
        await feed()
        await asyncio.wait_for(t, timeout=2.0)
        assert job.progress_pct == 10.0

    asyncio.run(run())


def test_is_http_driver_tag_edge_cases():
    assert hd.is_http_driver_tag("") is False
    assert hd.is_http_driver_tag("h-short") is False
    assert hd.is_http_driver_tag("h-550e8400-e29b-41d4-a716-44665544000g") is False
    assert hd.is_http_driver_tag("h-550e8400-e29b-41d4-a716-446655440000") is True


def test_validate_http_rejects_mega_host():
    with pytest.raises(ValueError, match="MEGA"):
        hd.validate_http_download_url("https://mega.nz/file/abc")


def test_validate_http_rejects_localhost():
    with pytest.raises(ValueError, match="not allowed"):
        hd.validate_http_download_url("http://localhost/x")


def test_parse_wget_stderr_clamps_percent():
    assert hd.parse_wget_stderr_progress(" 101% ")[0] == 100.0
    assert hd.parse_wget_stderr_progress(" 0% ")[0] == 0.0


def test_fetch_content_length_head_success(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        headers = {"Content-Length": "2048"}

    monkeypatch.setattr(hd, "urlopen", MagicMock(return_value=_Resp()))
    assert hd.fetch_content_length_head("https://example.com/x") == 2048


def test_safe_unlink_skips_path_outside_download_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    outside = "/nope/outside.txt"
    hd.safe_unlink_job_paths([outside])
    assert any("skipped path outside" in line for line in ms.log_buffer.get_lines())


def test_safe_unlink_logs_nonENOENT_oserror(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    target = tmp_path / "x.bin"
    target.write_text("z", encoding="utf-8")

    def boom(_p):
        e = OSError("perm")
        e.errno = 13
        raise e

    monkeypatch.setattr(hd.os, "remove", boom)
    hd.safe_unlink_job_paths([str(target)])
    assert any("could not remove" in line for line in ms.log_buffer.get_lines())


def test_http_download_argv_inserts_rate_limit():
    argv = hd._http_download_argv("/bin/wget2", "https://x", "/out", 800)
    assert any(a.startswith("--limit-rate=") for a in argv)


def test_job_to_api_row_keeps_tags_when_meta_tags_not_list(meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    tm.update(tag, {"tags": "nope"})
    job = hd.HttpJob(tag=tag, url="https://example.com/a", labels=["keep"], priority="NORMAL")
    row = hd.job_to_api_row(job)
    assert row["tags"] == ["keep"]


def test_run_job_inner_cancelled_at_entry_sets_pending_failed(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    recorded: list[tuple] = []

    async def capture(pid, **kwargs):
        recorded.append((pid, dict(kwargs)))
        return True

    import pending_queue as pq_mod

    monkeypatch.setattr(pq_mod, "set_item_status", capture)
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/z", labels=[], priority="NORMAL")
    job.cancelled = True
    asyncio.run(hd._run_job_inner(job, "queue-item-1"))
    assert job.state == "FAILED"
    assert recorded and recorded[0][0] == "queue-item-1"


def test_run_job_inner_simulate_path(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(ms, "SIMULATE", True)
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/z", labels=[], priority="WEIRD")

    async def main():
        await hd._run_job_inner(job, None)

    asyncio.run(main())
    assert job.state == "COMPLETED"
    assert job.priority == "NORMAL"


def test_run_job_inner_priority_normalized_before_run(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(ms, "SIMULATE", True)
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/z", labels=[], priority="nope")
    asyncio.run(hd._run_job_inner(job, None))
    assert job.priority == "NORMAL"


def test_file_poller_updates_partial_file(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    out = tmp_path / "partial.bin"
    out.write_bytes(b"abcd")
    job = hd.HttpJob(tag=tag, url="https://example.com/p.bin", labels=[], priority="NORMAL")
    job.output_file = str(out)
    job.size_bytes = 100
    hd._registry[tag] = job
    steps = {"n": 0}

    async def sleep_patch(_t):
        steps["n"] += 1
        if steps["n"] >= 2:
            async with hd._registry_lock:
                hd._registry.pop(tag, None)

    monkeypatch.setattr(hd.asyncio, "sleep", sleep_patch)

    async def main():
        await hd._file_poller(job)

    asyncio.run(main())
    assert job.downloaded_bytes == 4


def test_http_pause_resume_when_signals_supported(monkeypatch):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://x", labels=[], priority="NORMAL")
    proc = MagicMock()
    proc.returncode = None
    proc.pid = 424242
    job.proc = proc
    job.state = "ACTIVE"
    hd._registry[tag] = job
    monkeypatch.setattr(hd, "_sig_pause", lambda _pid: True)
    monkeypatch.setattr(hd, "_sig_resume", lambda _pid: True)
    assert asyncio.run(hd.http_pause(tag))[0] is True
    assert job.state == "PAUSED"
    assert asyncio.run(hd.http_resume(tag))[0] is True
    assert job.state == "ACTIVE"


def test_http_cancel_kills_on_wait_timeout(tmp_path, monkeypatch, meta_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://x", labels=[], priority="NORMAL")
    proc = MagicMock()
    proc.returncode = None
    proc.kill = MagicMock()

    async def proc_wait():
        return 0

    proc.wait = proc_wait
    job.proc = proc
    hd._registry[tag] = job

    async def boom_wait_for(_coro, timeout=8.0):
        raise asyncio.TimeoutError

    monkeypatch.setattr(hd.asyncio, "wait_for", boom_wait_for)
    ok, err = asyncio.run(hd.http_cancel(tag))
    assert ok is True
    proc.kill.assert_called_once()


def test_run_job_inner_completed_getsize_fails(tmp_path, monkeypatch, meta_path):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(hd, "_resolved_http_download_executable", lambda: "/bin/true")

    async def immediate_to_thread(fn, /, *a, **kw):
        return fn(*a, **kw)

    monkeypatch.setattr(hd.asyncio, "to_thread", immediate_to_thread)

    async def fake_exec(*args, **kwargs):
        argv = list(args)
        o_idx = argv.index("-O")
        out_path = argv[o_idx + 1]
        with open(out_path, "wb") as f:
            f.write(b"done")
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

    monkeypatch.setattr(hd.asyncio, "create_subprocess_exec", fake_exec)

    def boom_getsize(_p):
        raise OSError("stat")

    monkeypatch.setattr(hd.os.path, "getsize", boom_getsize)

    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/z.bin", labels=[], priority="NORMAL")
    asyncio.run(hd._run_job_inner(job, None))
    assert job.state == "FAILED"


def test_http_retry_reschedules_job(meta_path, monkeypatch):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/old", labels=["a"], priority="HIGH")
    job.state = "FAILED"
    hd._registry[tag] = job
    tm.update(tag, {"url": "https://example.com/new", "tags": ["b"], "priority": "LOW"})

    created = []

    def capture_task(coro):
        created.append(coro)
        coro.close()
        return MagicMock()

    monkeypatch.setattr(hd.asyncio, "create_task", capture_task)
    ok, err = asyncio.run(hd.http_retry(tag))
    assert ok is True
    assert err is None
    assert created
    assert job.state == "QUEUED"


def test_stderr_consumer_stops_when_tag_removed_from_registry():
    async def run():
        job = hd.HttpJob(
            tag="h-550e8400-e29b-41d4-a716-446655440000",
            url="https://x",
            labels=[],
            priority="NORMAL",
        )

        class P:
            stderr = asyncio.StreamReader()

        async def feed():
            P.stderr.feed_data(b" 20% x\n")
            async with hd._registry_lock:
                hd._registry.pop(job.tag, None)
            P.stderr.feed_eof()

        job.proc = P()
        hd._registry[job.tag] = job
        t = asyncio.create_task(hd._stderr_consumer(job))
        await feed()
        await asyncio.wait_for(t, timeout=2.0)

    asyncio.run(run())


def test_prune_removes_registry_entry(monkeypatch):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://x", labels=[], priority="NORMAL")
    hd._registry[tag] = job

    real_sleep = asyncio.sleep

    async def sleep_noop(_delay):
        await real_sleep(0)

    monkeypatch.setattr(hd.asyncio, "sleep", sleep_noop)

    async def main():
        hd._schedule_prune(tag, 0.0)
        await real_sleep(0.01)

    asyncio.run(main())
    assert tag not in hd._registry

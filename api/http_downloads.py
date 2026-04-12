"""
Generic HTTP(S) downloads via GNU Wget2: validation, job registry, progress, lifecycle, artifact cleanup.
Uses --force-progress and --progress=bar:force so the bar is emitted on piped stderr (wget 1.x --show-progress is not used).
Production target: Linux/Docker (signal pause/resume).
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import re
import shutil
import signal
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import mega_service as ms
import pending_queue as pq
import transfer_metadata as tm

MEGA_HOSTS = frozenset({"mega.nz", "www.mega.nz", "mega.co.nz", "www.mega.co.nz"})

_PROGRESS_PCT_RE = re.compile(r"(\d{1,3})\s*%")
_COMPLETED_PRUNE_SEC = 120.0
_FAILED_PRUNE_SEC = 90.0

JobState = Literal["QUEUED", "ACTIVE", "PAUSED", "COMPLETED", "FAILED"]


def http_downloads_enabled() -> bool:
    raw = os.environ.get("HTTP_DOWNLOADS_ENABLED", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def is_http_driver_tag(tag: str) -> bool:
    if not tag or not tag.startswith("h-"):
        return False
    rest = tag[2:]
    if len(rest) != 36:
        return False
    try:
        uuid.UUID(rest)
    except ValueError:
        return False
    return True


def validate_http_download_url(url: str) -> str:
    """Return stripped URL or raise ValueError. Not for MEGA hosts (those use the mega path)."""
    u = (url or "").strip()
    if not u:
        raise ValueError("URL is required")
    parsed = urlparse(u)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("Only http/https URLs are allowed")
    if host in MEGA_HOSTS:
        raise ValueError("This host must use the MEGA download flow")
    if _host_is_blocked(host):
        raise ValueError("URL host is not allowed for generic downloads")
    if not http_downloads_enabled():
        raise ValueError("Generic HTTP downloads are disabled on this server")
    return u


def _host_is_blocked(hostname: str) -> bool:
    h = (hostname or "").lower().rstrip(".")
    if not h:
        return True
    if h == "localhost" or h.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(h)
        return bool(ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        pass
    return False


def normalize_download_url(url: str) -> tuple[Literal["mega", "http"], str]:
    """Classify URL for routing. Raises ValueError."""
    u = (url or "").strip()
    if not u:
        raise ValueError("URL is required")
    parsed = urlparse(u)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("Only http/https URLs are allowed")
    if host in MEGA_HOSTS:
        return ("mega", ms.validate_mega_download_url(u))
    if not http_downloads_enabled():
        raise ValueError("Generic HTTP downloads are disabled on this server")
    return ("http", validate_http_download_url(u))


def parse_wget_stderr_progress(line: str) -> tuple[float | None, int | None]:
    """Extract (progress_pct 0-100, _) from a wget/wget2-style progress line; best-effort."""
    line = line.strip()
    if not line or "%" not in line:
        return None, None
    m = _PROGRESS_PCT_RE.search(line)
    if not m:
        return None, None
    try:
        pct = float(m.group(1))
        return min(100.0, max(0.0, pct)), None
    except ValueError:
        return None, None


def fetch_content_length_head(url: str, timeout: float = 12.0) -> int | None:
    """Best-effort Content-Length via HEAD."""
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "FileTugger-HTTP-download/1.0"})
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — URL validated by caller
            cl = resp.headers.get("Content-Length")
            if cl and str(cl).isdigit():
                return int(cl)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        pass
    return None


def _download_dir_realpath() -> str:
    return os.path.realpath(os.path.abspath(ms.DOWNLOAD_DIR))


def _is_under_download_dir(path: str) -> bool:
    try:
        base = _download_dir_realpath()
        p = os.path.realpath(path)
        return p == base or p.startswith(base + os.sep)
    except OSError:
        return False


def safe_unlink_job_paths(paths: list[str], *, log_label: str = "cleanup") -> None:
    for raw in paths:
        if not raw:
            continue
        try:
            if not _is_under_download_dir(raw):
                ms.log_buffer.append(f"HTTP download {log_label}: skipped path outside download dir")
                continue
            if os.path.isfile(raw):
                os.remove(raw)
        except OSError as e:
            if getattr(e, "errno", None) != 2:
                ms.log_buffer.append(f"HTTP download {log_label}: could not remove {raw}: {e}")


def _safe_output_basename(url: str, tag: str) -> str:
    parsed = urlparse(url)
    base = os.path.basename(parsed.path) or "download"
    base = re.sub(r"[^\w.\-]", "_", base)[:180]
    if not base or base in (".", ".."):
        base = "download"
    stem, ext = os.path.splitext(base)
    short = tag.replace("h-", "")[:8]
    return f"{stem}_{short}{ext}"


@dataclass
class HttpJob:
    tag: str
    url: str
    labels: list[str]
    priority: str
    state: JobState = "QUEUED"
    output_paths: list[str] = field(default_factory=list)
    output_file: str = ""
    size_bytes: int = 0
    downloaded_bytes: int = 0
    progress_pct: float = 0.0
    last_error: str | None = None
    proc: asyncio.subprocess.Process | None = None
    paused: bool = False
    cancelled: bool = False
    stderr_task: asyncio.Task[None] | None = None
    poll_task: asyncio.Task[None] | None = None
    done_event: asyncio.Event = field(default_factory=asyncio.Event)


_registry: dict[str, HttpJob] = {}
_registry_lock = asyncio.Lock()


def _http_wget_bin_name() -> str:
    b = (os.environ.get("WGET_HTTP_BIN") or "wget2").strip()
    return b or "wget2"


def _resolved_http_download_executable() -> str | None:
    """Resolve the Wget2 binary using the same PATH as subprocess_env, or an absolute WGET_HTTP_BIN path."""
    env = ms.subprocess_env()
    path = env.get("PATH", "")
    name = _http_wget_bin_name()
    if os.path.isabs(name):
        return name if os.path.isfile(name) and os.access(name, os.X_OK) else None
    return shutil.which(name, path=path)


def _http_download_argv(exe: str, url: str, out_path: str, speed_limit_kbps: int) -> list[str]:
    args: list[str] = [
        exe,
        "-q",
        "--force-progress",
        "--progress=bar:force",
        "--http2",
        "--compression=gzip,deflate,br",
        "--timeout=60",
        "--tries=3",
        "--max-redirect=10",
        "--trust-server-names",
        "--content-disposition",
        "-O",
        out_path,
        url,
    ]
    if speed_limit_kbps > 0:
        kb_s = max(1, int(speed_limit_kbps / 8))
        args.insert(2, f"--limit-rate={kb_s}k")
    return args


async def _stderr_consumer(job: HttpJob) -> None:
    if not job.proc or not job.proc.stderr:
        return
    try:
        while True:
            line_b = await job.proc.stderr.readline()
            if not line_b:
                break
            line = line_b.decode(errors="replace")
            pct, _ = parse_wget_stderr_progress(line)
            async with _registry_lock:
                if job.tag not in _registry:
                    break
                if pct is not None:
                    job.progress_pct = pct
                    if job.size_bytes > 0:
                        job.downloaded_bytes = min(job.size_bytes, int(job.size_bytes * pct / 100.0))
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


async def _file_poller(job: HttpJob) -> None:
    try:
        while True:
            await asyncio.sleep(0.75)
            async with _registry_lock:
                if job.tag not in _registry or job.cancelled:
                    break
                out = job.output_file
            if not out or not os.path.isfile(out):
                continue
            try:
                sz = os.path.getsize(out)
                async with _registry_lock:
                    if job.tag not in _registry:
                        break
                    job.downloaded_bytes = sz
                    if job.size_bytes > 0:
                        job.progress_pct = min(100.0, round(100.0 * sz / job.size_bytes, 2))
            except OSError:
                pass
    except asyncio.CancelledError:
        pass


def _schedule_prune(tag: str, delay: float) -> None:
    async def _later() -> None:
        await asyncio.sleep(delay)
        async with _registry_lock:
            _registry.pop(tag, None)

    asyncio.create_task(_later())


def job_to_api_row(job: HttpJob) -> dict[str, Any]:
    st = ms.normalize_transfer_state(job.state)
    size_b = int(job.size_bytes or 0)
    dl = int(job.downloaded_bytes or 0)
    pct = float(job.progress_pct or 0)
    if size_b > 0 and dl > 0 and pct == 0:
        pct = min(100.0, round(100.0 * dl / size_b, 2))
    fn = os.path.basename(job.output_file) if job.output_file else "download"
    row: dict[str, Any] = {
        "tag": job.tag,
        "url": job.url,
        "progress_pct": pct,
        "downloaded_bytes": dl,
        "speed_bps": 0,
        "state": st,
        "path": job.output_file or "",
        "filename": fn,
        "size_bytes": size_b,
        "retry_count": 0,
        "speed_limit_kbps": 0,
        "tags": list(job.labels),
        "priority": str(job.priority or "NORMAL").upper(),
        "driver": "http",
    }
    meta = tm.get(job.tag)
    if meta:
        if meta.get("url"):
            row["url"] = str(meta.get("url"))
        row["priority"] = str(meta.get("priority") or row["priority"]).upper()
        row["speed_limit_kbps"] = int(meta.get("speed_limit_kbps") or row["speed_limit_kbps"])
        tags = meta.get("tags", row["tags"])
        row["tags"] = tags if isinstance(tags, list) else row["tags"]
    return row


def list_api_rows() -> list[dict[str, Any]]:
    return [job_to_api_row(j) for j in _registry.values()]


def get_transfer_row(tag: str) -> dict[str, Any] | None:
    job = _registry.get(tag)
    if job:
        return job_to_api_row(job)
    return None


async def _run_job_inner(job: HttpJob, pending_id: str | None) -> None:
    async with _registry_lock:
        if job.cancelled:
            job.state = "FAILED"
            job.last_error = "Canceled"
            job.done_event.set()
            if pending_id:
                await pq.set_item_status(pending_id, status="FAILED", last_error="Canceled")
            _schedule_prune(job.tag, _FAILED_PRUNE_SEC)
            return

    pr = (job.priority or "NORMAL").strip().upper()
    if pr not in {"LOW", "NORMAL", "HIGH"}:
        pr = "NORMAL"
    job.priority = pr
    tm.update(job.tag, {"url": job.url, "tags": list(job.labels), "priority": pr})
    meta = tm.get(job.tag)
    speed_kbps = int(meta.get("speed_limit_kbps") or 0)

    download_dir_abs = _download_dir_realpath()
    os.makedirs(download_dir_abs, exist_ok=True)
    out_name = _safe_output_basename(job.url, job.tag)
    out_path = os.path.join(download_dir_abs, out_name)
    job.output_file = out_path
    job.output_paths = [out_path]

    async with _registry_lock:
        if job.cancelled:
            job.state = "FAILED"
            job.last_error = "Canceled"
            safe_unlink_job_paths(job.output_paths)
            job.done_event.set()
            if pending_id:
                await pq.set_item_status(pending_id, status="FAILED", last_error="Canceled")
            _schedule_prune(job.tag, _FAILED_PRUNE_SEC)
            return

    if ms.SIMULATE:
        ms.log_buffer.append(f"HTTP download (simulated): {job.url[:80]}")
        job.state = "ACTIVE"
        job.progress_pct = 50.0
        await asyncio.sleep(0.3)
        job.progress_pct = 100.0
        job.state = "COMPLETED"
        job.size_bytes = 1024
        job.downloaded_bytes = 1024
        job.done_event.set()
        if pending_id:
            await pq.remove_item(pending_id)
        _schedule_prune(job.tag, _COMPLETED_PRUNE_SEC)
        return

    cl = await asyncio.to_thread(fetch_content_length_head, job.url)
    if cl is not None and cl > 0:
        job.size_bytes = cl

    async with _registry_lock:
        if job.cancelled:
            job.state = "FAILED"
            job.last_error = "Canceled"
            safe_unlink_job_paths(job.output_paths)
            job.done_event.set()
            if pending_id:
                await pq.set_item_status(pending_id, status="FAILED", last_error="Canceled")
            _schedule_prune(job.tag, _FAILED_PRUNE_SEC)
            return

    exe = _resolved_http_download_executable()
    if not exe:
        job.state = "FAILED"
        job.last_error = (
            f"HTTP download client not found ({_http_wget_bin_name()}). "
            "Install GNU Wget2 (e.g. apt install wget2) or set WGET_HTTP_BIN to its path."
        )
        safe_unlink_job_paths(job.output_paths)
        job.done_event.set()
        if pending_id:
            await pq.set_item_status(pending_id, status="FAILED", last_error=(job.last_error or "")[:512])
        _schedule_prune(job.tag, _FAILED_PRUNE_SEC)
        ms.log_buffer.append(job.last_error or "HTTP download client missing")
        return

    job.state = "ACTIVE"
    ms.log_buffer.append(f"HTTP download started: {ms.redact_sensitive_text(job.url)[:120]}")

    argv = _http_download_argv(exe, job.url, out_path, speed_kbps)
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
        env=ms.subprocess_env(),
    )
    job.proc = proc
    job.stderr_task = asyncio.create_task(_stderr_consumer(job))
    job.poll_task = asyncio.create_task(_file_poller(job))

    try:
        await proc.wait()
    finally:
        for t in (job.stderr_task, job.poll_task):
            if t:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
        job.stderr_task = None
        job.poll_task = None
        job.proc = None

    async with _registry_lock:
        if job.cancelled:
            job.state = "FAILED"
            job.last_error = "Canceled"
            safe_unlink_job_paths(job.output_paths)
            job.done_event.set()
            if pending_id:
                await pq.set_item_status(pending_id, status="FAILED", last_error="Canceled")
            _schedule_prune(job.tag, _FAILED_PRUNE_SEC)
            return

    rc = proc.returncode if proc.returncode is not None else -1
    if rc == 0 and os.path.isfile(out_path):
        try:
            fs = os.path.getsize(out_path)
            job.downloaded_bytes = fs
            if job.size_bytes <= 0:
                job.size_bytes = fs
            job.progress_pct = 100.0
            job.state = "COMPLETED"
            ms.log_buffer.append(f"HTTP download completed: {os.path.basename(out_path)}")
            if pending_id:
                await pq.remove_item(pending_id)
            _schedule_prune(job.tag, _COMPLETED_PRUNE_SEC)
        except OSError as e:
            job.state = "FAILED"
            job.last_error = str(e)
            safe_unlink_job_paths(job.output_paths)
            if pending_id:
                await pq.set_item_status(pending_id, status="FAILED", last_error=str(e)[:512])
            _schedule_prune(job.tag, _FAILED_PRUNE_SEC)
    else:
        job.state = "FAILED"
        job.last_error = f"wget2 exited {rc}"
        safe_unlink_job_paths(job.output_paths)
        ms.log_buffer.append(f"HTTP download failed (exit {rc})")
        if pending_id:
            await pq.set_item_status(pending_id, status="FAILED", last_error=(job.last_error or "")[:512])
        _schedule_prune(job.tag, _FAILED_PRUNE_SEC)

    job.done_event.set()


async def _http_download_task_runner(tag: str, pending_id: str | None, job: HttpJob) -> None:
    async with _registry_lock:
        _registry[tag] = job
    try:
        await _run_job_inner(job, pending_id)
    except Exception as e:
        async with _registry_lock:
            j = _registry.get(tag)
            if j:
                j.state = "FAILED"
                j.last_error = str(e)
                safe_unlink_job_paths(j.output_paths)
                j.done_event.set()
        if pending_id:
            await pq.set_item_status(pending_id, status="FAILED", last_error=str(e)[:512])
        ms.log_buffer.append(f"HTTP download error: {ms.redact_sensitive_text(str(e))[:200]}")
        _schedule_prune(tag, _FAILED_PRUNE_SEC)


def schedule_http_download(
    url: str,
    labels: list[str],
    priority: str,
    *,
    pending_id: str | None = None,
) -> str:
    """Register an HTTP download and run it in the background; returns tag h-{uuid}."""
    tag = f"h-{uuid.uuid4()}"
    job = HttpJob(tag=tag, url=url, labels=list(labels), priority=priority)
    asyncio.create_task(_http_download_task_runner(tag, pending_id, job))
    return tag


def _sig_pause(pid: int) -> bool:
    if not hasattr(signal, "SIGSTOP"):
        return False
    try:
        os.kill(pid, signal.SIGSTOP)
        return True
    except OSError:
        return False


def _sig_resume(pid: int) -> bool:
    if not hasattr(signal, "SIGCONT"):
        return False
    try:
        os.kill(pid, signal.SIGCONT)
        return True
    except OSError:
        return False


async def http_pause(tag: str) -> tuple[bool, str | None]:
    async with _registry_lock:
        job = _registry.get(tag)
        if not job:
            return False, "Transfer not found"
        if job.state != "ACTIVE" or not job.proc or job.proc.returncode is not None:
            return False, "Not active"
        pid = job.proc.pid
    if pid and _sig_pause(pid):
        async with _registry_lock:
            j = _registry.get(tag)
            if j:
                j.paused = True
                j.state = "PAUSED"
        return True, None
    return False, "Pause not supported on this platform"


async def http_resume(tag: str) -> tuple[bool, str | None]:
    async with _registry_lock:
        job = _registry.get(tag)
        if not job:
            return False, "Transfer not found"
        if job.state != "PAUSED":
            return False, "Not paused"
        pid = job.proc.pid if job.proc and job.proc.returncode is None else None
    if pid and _sig_resume(pid):
        async with _registry_lock:
            j = _registry.get(tag)
            if j:
                j.paused = False
                j.state = "ACTIVE"
        return True, None
    return False, "Resume not supported on this platform"


async def http_cancel(tag: str) -> tuple[bool, str | None]:
    proc: asyncio.subprocess.Process | None = None
    async with _registry_lock:
        job = _registry.get(tag)
        if not job:
            return False, "Transfer not found"
        job.cancelled = True
        proc = job.proc
    if proc and proc.returncode is None:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=8.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
    return True, None


async def http_retry(tag: str) -> tuple[bool, str | None]:
    """Re-run Wget2 for the same tag using metadata URL/tags/priority."""
    meta = tm.get(tag)
    async with _registry_lock:
        job = _registry.get(tag)
        if not job:
            return False, "Transfer not found"
        url = str(meta.get("url") or job.url)
        labels = meta.get("tags") if isinstance(meta.get("tags"), list) else job.labels
        pr = str(meta.get("priority") or job.priority)
        out_paths = list(job.output_paths)
    try:
        url = validate_http_download_url(url)
    except ValueError as e:
        return False, str(e)
    safe_unlink_job_paths(out_paths)
    async with _registry_lock:
        j = _registry.get(tag)
        if not j:
            return False, "Transfer not found"
        j.url = url
        j.labels = [str(x) for x in labels]
        j.priority = pr
        j.cancelled = False
        j.last_error = None
        j.progress_pct = 0.0
        j.downloaded_bytes = 0
        j.size_bytes = 0
        j.state = "QUEUED"
        j.output_paths = []
        j.output_file = ""
        j.proc = None
        job_ref = j
    asyncio.create_task(_http_download_task_runner(tag, None, job_ref))
    return True, None


async def cancel_all_http_downloads() -> None:
    tags = list(_registry.keys())
    for t in tags:
        if is_http_driver_tag(t):
            j = _registry.get(t)
            if j and j.state in ("ACTIVE", "PAUSED", "QUEUED"):
                await http_cancel(t)

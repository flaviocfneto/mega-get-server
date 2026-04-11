"""
Shared MEGAcmd integration for Flet UI and FastAPI: env, subprocess helpers,
transfer list parsing, download/actions, URL history, and in-memory logs.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pending_correlation
import transfer_metadata as tm

# #region agent log
DEBUG_LOG_PATH = os.environ.get(
    "MEGA_DEBUG_LOG_PATH",
    str(Path(__file__).resolve().parent / ".mega-debug.log"),
)


def _debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "") -> None:
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        Path(DEBUG_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


# #endregion


def load_dotenv_if_present() -> None:
    """Load .env from project root when keys are not already set."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_root, ".env")
        if not os.path.isfile(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if key and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass


def in_docker() -> bool:
    return os.path.exists("/.dockerenv") or bool(os.environ.get("container"))


def default_download_dir() -> str:
    if in_docker():
        return "/data/"
    if sys.platform == "win32":
        return os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    return os.path.expanduser("~/Downloads")


def app_root_dir() -> str:
    """Directory containing the deployed app (e.g. /app in Docker, or repo root parent of `api/` locally)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_history_path() -> str:
    return os.path.join(app_root_dir(), ".mega-get-history.json")


load_dotenv_if_present()

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR") or default_download_dir()
TRANSFER_LIST_LIMIT = os.environ.get("TRANSFER_LIST_LIMIT", "50")
PATH_DISPLAY_SIZE = os.environ.get("PATH_DISPLAY_SIZE", "80")
INPUT_TIMEOUT = float(os.environ.get("INPUT_TIMEOUT", "0.0166"))
SIMULATE = os.environ.get("MEGA_SIMULATE", "").strip().lower() in ("1", "true", "yes")
UI_TEST_MODE = os.environ.get("UI_TEST_MODE", "").strip().lower() in ("1", "true", "yes")

MEGACMD_PATH = os.environ.get("MEGACMD_PATH", "").strip()
if not MEGACMD_PATH and sys.platform == "darwin":
    _macos_path = "/Applications/MEGAcmd.app/Contents/MacOS"
    if os.path.isdir(_macos_path):
        MEGACMD_PATH = _macos_path

POLL_INTERVAL = max(INPUT_TIMEOUT, 0.5)
URL_HISTORY_MAX = 50
LOG_MAX_LINES = 500
CMD_HISTORY_MAX = 100

_log_notify: Callable[[], None] | None = None


def set_log_notify(fn: Callable[[], None] | None) -> None:
    global _log_notify
    _log_notify = fn


class LogBuffer:
    def __init__(self, max_lines: int = LOG_MAX_LINES) -> None:
        self._max = max_lines
        self._lines: list[str] = []
        self._lock = threading.Lock()

    def append(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)
            if len(self._lines) > self._max:
                self._lines = self._lines[-self._max :]
        if _log_notify:
            try:
                _log_notify()
            except Exception:
                pass

    def get_lines(self) -> list[str]:
        with self._lock:
            return list(self._lines)

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()


log_buffer = LogBuffer()
_command_events: list[dict[str, Any]] = []

# Serialize queue-driven (and UI) mega-get correlation windows so tag snapshots stay unambiguous.
queue_dispatch_semaphore = asyncio.Semaphore(1)


def validate_mega_download_url(url: str) -> str:
    """Return stripped URL or raise ValueError with the same messages as legacy /api/download checks."""
    u = (url or "").strip()
    if not u:
        raise ValueError("URL is required")
    parsed = urlparse(u)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("Only http/https URLs are allowed")
    if host not in {"mega.nz", "www.mega.nz", "mega.co.nz", "www.mega.co.nz"}:
        raise ValueError("Only MEGA URLs are allowed")
    return u


def _record_command_event(event: dict[str, Any]) -> None:
    _command_events.append(event)
    if len(_command_events) > CMD_HISTORY_MAX:
        del _command_events[:-CMD_HISTORY_MAX]


def get_command_events() -> list[dict[str, Any]]:
    return list(_command_events)


def redact_sensitive_text(text: str) -> str:
    masked = text
    masked = re.sub(r"(?i)(password|token|apikey|api_key)\s*[:=]\s*\S+", r"\1=***", masked)
    masked = re.sub(r"(?i)(mega-login\s+)\S+(\s+)\S+", r"\1***\2***", masked)
    masked = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9\-\._~\+/=]+", r"\1***", masked)
    # OpenAI-style and similar opaque prefixes (avoid relying on env var names).
    masked = re.sub(r"(?i)\bsk-[a-z0-9_-]{12,}\b", "***", masked)
    masked = re.sub(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "***", masked)
    masked = re.sub(r"(?is)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", "***", masked)
    masked = re.sub(r"(?i)([?&](?:token|apikey|api_key|key|secret)=)[^&\s]+", r"\1***", masked)
    return masked


def redact_command_args(args: list[str]) -> list[str]:
    if not args:
        return args
    cmd = args[0]
    if cmd == "mega-login":
        # redact password and email from diagnostics/event history
        redacted = [cmd]
        if len(args) > 1:
            redacted.append("***")
        if len(args) > 2:
            redacted.append("***")
        if len(args) > 3:
            redacted.extend(args[3:])
        return redacted
    return args


# URL history (newest first)
_url_history: list[str] = []
_history_file_path: str | None = None


def set_history_path(path: str | None) -> None:
    global _history_file_path
    _history_file_path = path


def get_history_path() -> str:
    return _history_file_path or default_history_path()


def load_history() -> None:
    global _url_history
    path = get_history_path()
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            _url_history = [u for u in data if isinstance(u, str)][:URL_HISTORY_MAX]
    except Exception:
        pass


def save_history() -> None:
    path = get_history_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_url_history[:URL_HISTORY_MAX], f, ensure_ascii=False)
    except Exception:
        pass


def get_history() -> list[str]:
    return list(_url_history)


def add_url_to_history(url: str) -> None:
    global _url_history
    if url in _url_history:
        _url_history.remove(url)
    _url_history.insert(0, url)
    if len(_url_history) > URL_HISTORY_MAX:
        _url_history.pop()
    save_history()


def clear_history() -> None:
    global _url_history
    _url_history.clear()
    save_history()


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    if MEGACMD_PATH:
        env["PATH"] = os.pathsep.join([MEGACMD_PATH, env.get("PATH", "")])
    return env


def mega_cmd_server_binary() -> str | None:
    env = subprocess_env()
    path_str = env.get("PATH", "")
    if not path_str:
        return None
    if shutil.which("mega-cmd-server", path=path_str):
        return "mega-cmd-server"
    if sys.platform == "darwin" and MEGACMD_PATH:
        mac_cmd = os.path.join(MEGACMD_PATH, "MEGAcmd")
        if os.path.isfile(mac_cmd) and os.access(mac_cmd, os.X_OK):
            return mac_cmd
    return None


async def wait_for_mega_server_ready(max_wait_sec: float = 15.0) -> bool:
    env = subprocess_env()
    deadline = asyncio.get_event_loop().time() + max_wait_sec
    while asyncio.get_event_loop().time() < deadline:
        try:
            proc = await asyncio.create_subprocess_exec(
                "mega-version",
                env=env,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=5.0)
            if proc.returncode == 0:
                return True
        except (asyncio.TimeoutError, OSError):
            pass
        await asyncio.sleep(1.0)
    return False


async def ensure_mega_cmd_server_running() -> bool:
    if in_docker() or SIMULATE:
        return True
    server_bin = mega_cmd_server_binary()
    env = subprocess_env()
    if server_bin == "mega-cmd-server":
        try:
            await asyncio.create_subprocess_exec(
                server_bin,
                env=env,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.sleep(2)
            _debug_log(
                "mega_service:ensure_mega_cmd_server",
                "started mega-cmd-server and waiting for ready",
                {"server_binary": server_bin, "waited_sec": 2},
                hypothesis_id="H4",
            )
        except Exception as e:
            _debug_log(
                "mega_service:ensure_mega_cmd_server",
                "server start failed",
                {"error": str(e), "server_binary": server_bin},
                hypothesis_id="H4",
            )
    ready = await wait_for_mega_server_ready()
    _debug_log("mega_service:ensure_mega_cmd_server", "server ready check", {"ready": ready}, hypothesis_id="H4")
    return ready


def _get_test_transfer_output() -> str:
    return """
⇓    1234  /Downloads/ubuntu-22.04.iso  45.2% of  3.54 GB ACTIVE
↑    5678  /Uploads/video.mp4  78.5% of  1.23 GB ACTIVE
⇓    9012  /Downloads/document.pdf  0.0% of  15.2 MB QUEUED
⇓    3456  /Downloads/large_archive.zip  12.8% of  8.91 GB RETRYING
"""


async def get_transfer_list() -> str:
    if SIMULATE:
        return (
            "\n"
            "TRANSFER  STATE     PROGRESS  PATH\n"
            "1         ACTIVE    12%       /data/sample_file.zip\n"
            "2         QUEUED    0%        /data/another_file.pdf\n"
        )
    if UI_TEST_MODE:
        return _get_test_transfer_output()

    _debug_log(
        "mega_service:get_transfer_list",
        "calling mega-transfers",
        {"limit": TRANSFER_LIST_LIMIT, "path_display_size": PATH_DISPLAY_SIZE},
        hypothesis_id="H5",
    )

    proc = await asyncio.create_subprocess_exec(
        "mega-transfers",
        f"--limit={TRANSFER_LIST_LIMIT}",
        f"--path-display-size={PATH_DISPLAY_SIZE}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=subprocess_env(),
    )
    stdout, stderr = await proc.communicate()
    out_s = (stdout or b"").decode(errors="replace")
    err_s = (stderr or b"").decode(errors="replace")
    # Some builds write the table to stderr or only populate stderr; merge for parsing.
    if not out_s.strip():
        out = err_s
    else:
        out = out_s
        if err_s.strip():
            out = out_s.rstrip() + "\n" + err_s

    _debug_log(
        "mega_service:get_transfer_list",
        "mega-transfers output",
        {
            "returncode": proc.returncode,
            "stderr_present": bool(stderr and len(stderr) > 0),
            "stderr_preview": (stderr or b"").decode(errors="replace")[:300].strip() if stderr else "",
            "stdout_len": len(out),
            "stdout_full": out,
        },
        hypothesis_id="H5",
    )
    return out


# Unicode + ASCII arrows seen in different MEGAcmd / terminal renderings
_TRANSFER_ARROW_CLASS = r"[⇓↑↓v^]"


def summarize_transfer_parse(raw: str, parsed: list[dict[str, Any]]) -> dict[str, Any]:
    """Lightweight stats for API debug (e.g. MEGA_ANALYTICS_PARSE_DEBUG=1)."""
    lines = [ln.strip() for ln in (raw or "").splitlines() if ln.strip()]
    return {
        "parsed_count": len(parsed),
        "nonempty_line_count": len(lines),
        "raw_char_len": len(raw or ""),
        "raw_preview": (raw or "")[:1200],
    }


def parse_transfer_list(raw: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not raw or not raw.strip():
        return result

    _debug_log(
        "mega_service:parse_transfer_list",
        "parsing transfer output",
        {"raw_length": len(raw), "raw_preview": raw[:500]},
        hypothesis_id="H6",
    )

    lines = raw.strip().split("\n")
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Only skip a clear MEGAcmd table header, not random paths containing words like STATE.
        if re.search(r"^\s*TYPE\s+.*\bTAG\b.*\bSTATE\b", line, re.IGNORECASE):
            continue

        sim_match = re.match(r"^\s*(\d+)\s+(\w+)\s+(\d+)%\s+(.+)$", line)
        if sim_match:
            tag, state, pct, path = sim_match.groups()
            filename = path.split("/")[-1] if "/" in path else path
            result.append(
                {
                    "tag": tag,
                    "progress_pct": float(pct),
                    "state": str(state).upper(),
                    "path": path.strip(),
                    "filename": filename,
                    "size_display": "Unknown",
                }
            )
            continue

        real_match = re.search(
            rf"({_TRANSFER_ARROW_CLASS})\s+(\d+)\s+(.*?)\s+(\d+(?:\.\d+)?)\s*%\s+of\s+([\d.]+)\s*([KMGT]?B)\s+(\w+)\s*$",
            line,
        )

        if real_match:
            _direction, tag, path_part, pct, size_val, size_unit, state = real_match.groups()
            path_part = path_part.strip()
            filename = path_part.split("/")[-1].strip() if "/" in path_part else path_part
            if "..." in path_part and "/" in path_part:
                parts = path_part.split("...")
                if len(parts) > 1 and "/" in parts[-1]:
                    filename = parts[-1].split("/")[-1].strip()
            if len(filename) > 60:
                filename = filename[:57] + "..."
            result.append(
                {
                    "tag": tag,
                    "progress_pct": float(pct),
                    "state": state.upper(),
                    "path": path_part,
                    "filename": filename or "Unknown",
                    "size_display": f"{size_val} {size_unit}",
                }
            )
            _debug_log(
                "mega_service:parse_transfer_list",
                "parsed transfer",
                {
                    "line_num": line_num,
                    "tag": tag,
                    "filename": filename,
                    "progress": pct,
                    "state": state,
                    "size": f"{size_val} {size_unit}",
                },
                hypothesis_id="H6",
            )
            continue

        # Alternate MEGAcmd line: progress % without "of <size>" before state (or truncated path).
        relaxed_match = re.search(
            rf"({_TRANSFER_ARROW_CLASS})\s+(\d+)\s+(.*?)\s+(\d+(?:\.\d+)?)\s*%\s+(?:of\s+[\d.]+\s*[KMGT]?B\s+)?(\w+)\s*$",
            line,
        )
        if relaxed_match:
            _d, tag, path_part, pct, state = relaxed_match.groups()
            path_part = path_part.strip()
            filename = path_part.split("/")[-1].strip() if "/" in path_part else path_part
            if "..." in path_part and "/" in path_part:
                parts = path_part.split("...")
                if len(parts) > 1 and "/" in parts[-1]:
                    filename = parts[-1].split("/")[-1].strip()
            if len(filename) > 60:
                filename = filename[:57] + "..."
            result.append(
                {
                    "tag": tag,
                    "progress_pct": float(pct),
                    "state": str(state).upper(),
                    "path": path_part,
                    "filename": filename or "Unknown",
                    "size_display": "Unknown",
                }
            )
            continue

        # Table-style: optional DOWNLOAD/UPLOAD keyword, tag, state, percent, path (no arrow).
        dl_match = re.match(
            r"(?i)^\s*(?:download|upload)\s+(\d+)\s+(\w+)\s+(\d+(?:\.\d+)?)%\s+(.+)$",
            line,
        )
        if dl_match:
            tag, state, pct, path = dl_match.groups()
            path = path.strip()
            filename = path.split("/")[-1] if "/" in path else path
            result.append(
                {
                    "tag": tag,
                    "progress_pct": float(pct),
                    "state": str(state).upper(),
                    "path": path,
                    "filename": filename,
                    "size_display": "Unknown",
                }
            )
            continue

        if len(line) > 10:
            _debug_log("mega_service:parse_transfer_list", "unparsed line", {"line_num": line_num, "line": line[:200]}, hypothesis_id="H6")

    _debug_log(
        "mega_service:parse_transfer_list",
        "parsing complete",
        {"total_lines": len(lines), "parsed_transfers": len(result)},
        hypothesis_id="H6",
    )
    return result


_SIZE_UNIT_RE = re.compile(r"^\s*([\d.]+)\s*([KMGT]?)B\s*$", re.IGNORECASE)


def normalize_transfer_state(state: str) -> str:
    """Map MEGAcmd-style labels to API transfer states used by the UI and analytics."""
    u = str(state or "").upper().strip()
    if u in ("FINISHED", "DONE", "COMPLETE", "SUCCESS"):
        return "COMPLETED"
    if u in ("ERROR", "CANCELLED", "CANCELED"):
        return "FAILED"
    return u


def _infer_account_type_from_text(text: str) -> str:
    """Best-effort plan label from mega-whoami / mega-df output (MEGAcmd varies by locale/version)."""
    t = (text or "").lower()
    if re.search(r"\bbusiness\b", t):
        return "BUSINESS"
    if re.search(r"\bpro\b", t) or "mega pro" in t or "pro lite" in t:
        return "PRO"
    return "UNKNOWN"


def _parse_mega_df_bytes_and_bw(df_text: str) -> tuple[int, int, int, int, bool]:
    """
    Returns (storage_used, storage_total, bandwidth_used, bandwidth_limit, storage_confident).
    Bandwidth is only set when at least four byte counts appear (common mega-df layout).
    """
    low = df_text.lower()
    nums = [int(n) for n in re.findall(r"(\d+)\s*bytes", low)]

    # Default fallback: historic positional parsing.
    storage_confident = len(nums) >= 2
    su, st = (nums[0], nums[1]) if storage_confident else (0, 0)
    bu, bl = 0, 0
    if len(nums) >= 4:
        bu, bl = nums[2], nums[3]

    # Try label-driven extraction first; MEGAcmd formats vary by platform/version.
    line_vals: list[tuple[str, int]] = []
    for m in re.finditer(r"(?im)^\s*([a-z][a-z0-9 _/\-]{1,50})\s*:\s*(\d+)\s*bytes\b", low):
        label = m.group(1).strip()
        val = int(m.group(2))
        line_vals.append((label, val))

    storage_used_l = [v for k, v in line_vals if "storage" in k and "used" in k]
    storage_total_l = [v for k, v in line_vals if "storage" in k and ("total" in k or "max" in k or "available" in k)]
    bw_used_l = [
        v
        for k, v in line_vals
        if ("bandwidth" in k or "transfer" in k or "traffic" in k) and ("used" in k or "spent" in k)
    ]
    bw_total_l = [
        v
        for k, v in line_vals
        if ("bandwidth" in k or "transfer" in k or "traffic" in k or "quota" in k)
        and ("total" in k or "max" in k or "available" in k or "quota" in k)
    ]

    if storage_used_l and storage_total_l:
        su, st = storage_used_l[0], storage_total_l[0]
        storage_confident = True

    if bw_used_l and bw_total_l:
        bu, bl = bw_used_l[0], bw_total_l[0]

    # If labeled bandwidth was not found, parse line forms like:
    # "Transfer quota: 123 bytes of 456 bytes"
    if bl == 0:
        m = re.search(
            r"(?im)^\s*(?:transfer|bandwidth|traffic)[^:\n]*:\s*(\d+)\s*bytes\s*(?:/|of)\s*(\d+)\s*bytes\b",
            low,
        )
        if m:
            bu = int(m.group(1))
            bl = int(m.group(2))

    return su, st, bu, bl, storage_confident


def size_display_to_bytes(size_display: str) -> int:
    if not size_display or size_display.strip().lower() == "unknown":
        return 0
    m = _SIZE_UNIT_RE.match(size_display.strip())
    if not m:
        return 0
    val = float(m.group(1))
    prefix = (m.group(2) or "").upper()
    mult = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    factor = mult.get(prefix, 1)
    return max(0, int(val * factor))


def parsed_transfer_to_api_row(t: dict[str, Any]) -> dict[str, Any]:
    size_b = size_display_to_bytes(str(t.get("size_display", "Unknown")))
    pct = float(t.get("progress_pct", 0))
    downloaded = round(size_b * pct / 100.0) if size_b > 0 else 0
    row = {
        "tag": str(t["tag"]),
        "url": "",
        "progress_pct": pct,
        "downloaded_bytes": downloaded,
        "speed_bps": 0,
        "state": normalize_transfer_state(str(t.get("state", ""))),
        "path": t.get("path", ""),
        "filename": t.get("filename", ""),
        "size_bytes": size_b,
        "retry_count": 0,
        "speed_limit_kbps": 0,
        "tags": [],
        "priority": "NORMAL",
    }
    meta = tm.get(row["tag"])
    if meta:
        row["url"] = str(meta.get("url") or row["url"])
        row["priority"] = str(meta.get("priority") or row["priority"]).upper()
        row["speed_limit_kbps"] = int(meta.get("speed_limit_kbps") or row["speed_limit_kbps"])
        tags = meta.get("tags", row["tags"])
        row["tags"] = tags if isinstance(tags, list) else row["tags"]
    return row


async def run_mega_get(url: str) -> tuple[bool, str | None]:
    """
    Run mega-get for url. Returns (success, raw_error_detail_or_none).
    raw_error is suitable for operator logs; callers should redact before exposing to clients.
    """
    if SIMULATE:
        log_buffer.append("URL Accepted (simulated)")
        await asyncio.sleep(1)
        return True, None

    download_dir_abs = os.path.abspath(DOWNLOAD_DIR)
    _debug_log(
        "mega_service:run_mega_get:entry",
        "mega-get invoked",
        {"url_preview": url.strip()[:80], "download_dir": download_dir_abs, "cwd": os.getcwd()},
        hypothesis_id="H1 H4",
    )

    log_buffer.append(f"Starting download to {DOWNLOAD_DIR}...")

    async def _run_get(args: list[str]) -> tuple[int, bytes, bytes]:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=subprocess_env(),
        )
        stdout_b, stderr_b = await proc.communicate()
        rc = proc.returncode if proc.returncode is not None else -1
        return rc, stdout_b or b"", stderr_b or b""

    base_args = ["mega-get", "--ignore-quota-warn", url.strip(), download_dir_abs]
    rc, stdout, stderr = await _run_get(base_args)
    err_msg_l = stderr.decode(errors="replace").lower()
    # Some macOS MEGAcmd installations intermittently segfault when destination is provided.
    # Retry once without destination to match the behavior users observe in terminal usage.
    if rc != 0 and ("segmentation fault" in err_msg_l or "signal 11" in err_msg_l or "mega-exec" in err_msg_l):
        log_buffer.append("MEGAcmd crashed on first attempt; retrying without explicit destination...")
        rc, stdout, stderr = await _run_get(["mega-get", "--ignore-quota-warn", url.strip()])

    _debug_log(
        "mega_service:run_mega_get:exit",
        "mega-get finished",
        {
            "returncode": rc,
            "stdout_preview": (stdout or b"").decode(errors="replace")[:400].strip(),
            "stderr_preview": (stderr or b"").decode(errors="replace")[:400].strip(),
        },
        hypothesis_id="H3",
    )

    if rc == 0:
        out_msg = (stdout or b"").decode(errors="replace").strip()
        err_msg = (stderr or b"").decode(errors="replace").strip()
        log_buffer.append("✓ Download command accepted by MEGAcmd")
        if out_msg:
            log_buffer.append(f"MEGAcmd: {out_msg[:800]}")
        if err_msg:
            log_buffer.append(f"MEGAcmd: {err_msg[:800]}")
        if not SIMULATE:
            await asyncio.sleep(2)
            try:
                rproc = await asyncio.create_subprocess_exec(
                    "mega-transfers",
                    "-r",
                    "-a",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    env=subprocess_env(),
                )
                r_stdout, _r_stderr = await rproc.communicate()
                r_text = (r_stdout or b"").decode(errors="replace").strip()
                if not r_text:
                    log_buffer.append(
                        "No active transfer detected after submit. The file may have completed instantly, "
                        "already exists at destination, or MEGAcmd queued nothing."
                    )
            except Exception:
                pass
    else:
        err_msg = stderr.decode(errors="replace").strip() if stderr else ""
        err_l = err_msg.lower()
        if "already exists" in err_l:
            log_buffer.append("✓ File already exists at destination (MEGAcmd skipped download).")
            return True, None
        log_buffer.append("✗ Error: Unable to start MEGA download")
        if stderr:
            if err_msg:
                log_buffer.append(f"Details: {err_msg}")
                if "segmentation fault" in err_l or "signal 11" in err_l or "mega-exec" in err_l:
                    log_buffer.append("MEGAcmd crashed while handling this URL (segmentation fault).")
                    log_buffer.append(
                        "Try restarting MEGAcmd daemon (`mega-quit` then `mega-login ...`) or reinstall MEGAcmd."
                    )
                    log_buffer.append(
                        "If it persists, run `mega-get <url> <dir>` directly in terminal to verify native MEGAcmd stability."
                    )
        return False, err_msg or "mega-get failed"

    return True, None


async def _snapshot_transfer_tags() -> set[str]:
    raw = await get_transfer_list()
    parsed = parse_transfer_list(raw)
    return {str(t.get("tag")) for t in parsed if t.get("tag")}


async def _apply_metadata_after_mega_get(
    url: str,
    labels: list[str],
    priority: str,
    tags_before: set[str],
) -> bool:
    """Return True if transfer_metadata was attached to exactly one new tag."""
    pr = (priority or "NORMAL").strip().upper()
    if pr not in {"LOW", "NORMAL", "HIGH"}:
        pr = "NORMAL"
    for _ in range(5):
        await asyncio.sleep(0.25)
        raw = await get_transfer_list()
        parsed = parse_transfer_list(raw)
        tags_after = {str(t.get("tag")) for t in parsed if t.get("tag")}
        new_tags = tags_after - tags_before
        if len(new_tags) == 1:
            tag = next(iter(new_tags))
            tm.update(tag, {"url": url, "tags": list(labels), "priority": pr})
            return True
    return False


async def run_mega_get_with_user_meta(
    url: str,
    labels: list[str],
    priority: str,
    pending_id: str | None = None,
) -> tuple[bool, str | None]:
    """
    Run mega-get under a global semaphore, then best-effort attach transfer_metadata when
    exactly one new MEGAcmd tag appears after the call.
    If correlation stays ambiguous and pending_id is set, persist for later merge on transfers poll.
    """
    async with queue_dispatch_semaphore:
        tags_before = await _snapshot_transfer_tags()
        ok, err = await run_mega_get(url)
        if ok:
            attached = await _apply_metadata_after_mega_get(url, labels, priority, tags_before)
            if not attached and pending_id:
                await pending_correlation.record_after_ambiguous_mega_get(
                    pending_id,
                    url,
                    list(labels),
                    priority or "NORMAL",
                    tags_before,
                )
        return ok, err


async def _mega_transfers_exec(flag: str, target: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "mega-transfers",
        flag,
        target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=subprocess_env(),
    )
    stdout, stderr = await proc.communicate()
    out = (stdout or b"").decode(errors="replace").strip()
    err = (stderr or b"").decode(errors="replace").strip()
    rc = proc.returncode
    if rc is None:
        rc = -1
    return rc, out, err


async def run_megacmd_command(args: list[str]) -> dict[str, Any]:
    """
    Execute a MEGAcmd CLI command with the configured subprocess environment.
    Returns {ok, command, exit_code, stdout, stderr, output, timestamp}.
    """
    started = int(time.time() * 1000)
    safe_args = redact_command_args(args)
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=subprocess_env(),
        )
        stdout_b, stderr_b = await proc.communicate()
        code = proc.returncode if proc.returncode is not None else -1
        stdout = (stdout_b or b"").decode(errors="replace").strip()
        stderr = (stderr_b or b"").decode(errors="replace").strip()
        output = stdout if stdout else stderr
        event = {
            "ok": code == 0,
            "command": " ".join(safe_args),
            "exit_code": code,
            "stdout": stdout[:2000],
            "stderr": stderr[:2000],
            "output": output[:2000],
            "timestamp": started,
        }
    except Exception as e:
        event = {
            "ok": False,
            "command": " ".join(safe_args),
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "output": str(e),
            "timestamp": started,
        }
    _record_command_event(event)
    if not event["ok"]:
        log_buffer.append(f"Command failed ({event['exit_code']}): {event['command']}")
        if event["output"]:
            log_buffer.append(f"Details: {event['output']}")
    return event


async def command_probe() -> list[dict[str, Any]]:
    """
    Run lightweight runtime probes mirroring known-good manual checks.
    """
    probes = [
        ["mega-version"],
        ["mega-whoami"],
        ["mega-transfers", "--limit=10", "--path-display-size=80"],
    ]
    results: list[dict[str, Any]] = []
    for cmd in probes:
        results.append(await run_megacmd_command(cmd))
    return results


async def get_account_info() -> dict[str, Any]:
    if SIMULATE:
        return {
            "email": "simulated@local",
            "is_logged_in": True,
            "account_type": "FREE",
            "storage_used_bytes": 1_000_000,
            "storage_total_bytes": 20_000_000_000,
            "bandwidth_limit_bytes": 0,
            "bandwidth_used_bytes": 0,
            "details_partial": True,
        }

    who = await run_megacmd_command(["mega-whoami"])
    out_txt = (who.get("stdout") or "").strip()
    err_txt = (who.get("stderr") or "").strip()
    combined_who = out_txt or err_txt or (who.get("output") or "").strip()
    logged_in = bool(who.get("ok")) and bool(combined_who)
    email = None
    if logged_in:
        first = combined_who.splitlines()[0].strip()
        if ":" in first:
            email = first.split(":", 1)[1].strip()
        else:
            email = first or None
    details_partial = True
    storage_used = 0
    storage_total = 0
    bandwidth_used = 0
    bandwidth_limit = 0
    account_type = "UNKNOWN"
    if logged_in:
        account_type = _infer_account_type_from_text(combined_who)
        df = await run_megacmd_command(["mega-df"])
        df_out = (df.get("stdout") or "").strip()
        df_err = (df.get("stderr") or "").strip()
        df_txt = df_out or df_err or (df.get("output") or "")
        if df.get("ok") and df_txt.strip():
            su, st, bu, bl, storage_ok = _parse_mega_df_bytes_and_bw(df_txt)
            storage_used, storage_total = su, st
            bandwidth_used, bandwidth_limit = bu, bl
            d_infer = _infer_account_type_from_text(df_txt)
            if d_infer != "UNKNOWN":
                account_type = d_infer
            if storage_ok:
                details_partial = False
    return {
        "email": email,
        "is_logged_in": logged_in,
        "account_type": account_type,
        "storage_used_bytes": storage_used,
        "storage_total_bytes": storage_total,
        "bandwidth_limit_bytes": bandwidth_limit,
        "bandwidth_used_bytes": bandwidth_used,
        "details_partial": details_partial,
    }


async def run_mega_transfers_action(action: str, tag: str) -> None:
    """pause | resume | cancel — per-tag MEGAcmd."""
    if action == "resume":
        await run_mega_transfers_resume_for_tag(tag, log_label="Resume")
        return

    if SIMULATE:
        log_buffer.append(f"{action.title()} transfer {tag} (simulated)")
        return

    flag = {"cancel": "-c", "pause": "-p"}.get(action, "-c")
    code, out, err = await _mega_transfers_exec(flag, tag.strip() if tag else "-a")

    if out:
        log_buffer.append(out)
    if code != 0:
        log_buffer.append(f"{action.title()} failed for transfer {tag} (exit {code})")
        if err:
            log_buffer.append(f"Details: {err[:800]}")
    else:
        log_buffer.append(f"{action.title()} command sent for transfer {tag}")


async def run_mega_transfers_resume_for_tag(tag: str, *, log_label: str) -> None:
    """MEGAcmd -r <tag>. log_label is 'Resume' or 'Retry' for log distinction."""
    if SIMULATE:
        log_buffer.append(f"{log_label} (resume) simulated for transfer {tag}")
        return

    code, out, err = await _mega_transfers_exec("-r", tag.strip())
    if out:
        log_buffer.append(out)
    if code != 0:
        log_buffer.append(f"{log_label} (mega-transfers -r) failed for transfer {tag} (exit {code})")
        if err:
            log_buffer.append(f"Details: {err[:800]}")
    else:
        log_buffer.append(f"{log_label} (resume) sent for transfer {tag} — mega-transfers -r {tag}")


async def run_mega_transfers_cancel_all() -> None:
    """mega-transfers -c -a"""
    if SIMULATE:
        log_buffer.append("Cancel-all (simulated): mega-transfers -c -a")
        return

    code, out, err = await _mega_transfers_exec("-c", "-a")
    if out:
        log_buffer.append(out)
    log_buffer.append(f"Cancel-all: mega-transfers -c -a completed (exit {code})")
    if code != 0 and err:
        log_buffer.append(f"Details: {err[:800]}")


def is_web_server_mode() -> bool:
    if os.environ.get("FLET_FORCE_WEB_SERVER", "").strip().lower() in ("1", "true", "yes"):
        return True
    if in_docker():
        return True
    if sys.platform == "linux" and not os.environ.get("DISPLAY"):
        return True
    return False

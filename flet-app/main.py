"""
MEGA Get - Flet prototype.
Web UI for mega-get-server: add MEGA URLs, view transfers, cancel/pause/resume.
Runs as desktop (native window), web (browser/server), or in Docker; adapts view, port, and DOWNLOAD_DIR.

Environment Variables:
- DOWNLOAD_DIR: Where to save downloads (default: ~/Downloads or /data/ in Docker)
- TRANSFER_LIST_LIMIT: Max transfers to show (default: 50)
- PATH_DISPLAY_SIZE: Path truncation size (default: 80)
- INPUT_TIMEOUT: Polling interval in seconds (default: 0.0166)
- MEGA_SIMULATE: Set to "1" to run without MEGA CMD (fake transfers for testing)
- UI_TEST_MODE: Set to "1" to show realistic sample transfers for UI development
- MEGACMD_PATH: Path to MEGAcmd binaries (default: /Applications/MEGAcmd.app/Contents/MacOS on macOS)

Debugging:
- All debug logs are written to: /Users/flavioneto/Documents/MEGA-Downloader/mega-get-server/.cursor/debug.log
- Check this file to see raw mega-transfers output and parsing results
- Use UI_TEST_MODE=1 to visualize the UI with sample data without running MEGAcmd
"""
import asyncio
import json
import os
import re
import shutil
import sys
import time

import flet as ft

# #region agent log
DEBUG_LOG_PATH = "/Users/flavioneto/Documents/MEGA-Downloader/mega-get-server/.cursor/debug.log"

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
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


def _load_dotenv_if_present() -> None:
    """Load .env from project root so desktop (and other) runs get DOWNLOAD_DIR etc. without shell env."""
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


def _in_docker() -> bool:
    """True if running inside a Docker container."""
    return os.path.exists("/.dockerenv") or bool(os.environ.get("container"))


def _default_download_dir() -> str:
    """Platform-aware default for DOWNLOAD_DIR. Use /data/ in Docker, else user Downloads."""
    if _in_docker():
        return "/data/"
    if sys.platform == "win32":
        return os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    return os.path.expanduser("~/Downloads")


# Load .env from project root first so desktop app gets DOWNLOAD_DIR etc.
_load_dotenv_if_present()

# Env vars (match existing mega-get-server); DOWNLOAD_DIR is platform-aware when unset
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR") or _default_download_dir()
TRANSFER_LIST_LIMIT = os.environ.get("TRANSFER_LIST_LIMIT", "50")
PATH_DISPLAY_SIZE = os.environ.get("PATH_DISPLAY_SIZE", "80")
INPUT_TIMEOUT = float(os.environ.get("INPUT_TIMEOUT", "0.0166"))
SIMULATE = os.environ.get("MEGA_SIMULATE", "").strip().lower() in ("1", "true", "yes")

# MEGAcmd location: MEGACMD_PATH env, or on macOS default to Applications install
# https://github.com/meganz/MEGAcmd
MEGACMD_PATH = os.environ.get("MEGACMD_PATH", "").strip()
if not MEGACMD_PATH and sys.platform == "darwin":
    _macos_path = "/Applications/MEGAcmd.app/Contents/MacOS"
    if os.path.isdir(_macos_path):
        MEGACMD_PATH = _macos_path

POLL_INTERVAL = max(INPUT_TIMEOUT, 0.5)


def _subprocess_env() -> dict[str, str]:
    """Env for subprocess so mega-* commands are found (e.g. local MEGAcmd on macOS)."""
    env = os.environ.copy()
    if MEGACMD_PATH:
        env["PATH"] = os.pathsep.join([MEGACMD_PATH, env.get("PATH", "")])
    return env


def _mega_cmd_server_binary() -> str | None:
    """
    Path to the MEGAcmd server executable, or None if not found.
    Linux: mega-cmd-server. macOS: no standalone server; MEGAcmd.app runs server when opened — use MEGAcmd binary.
    """
    env = _subprocess_env()
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


async def _wait_for_mega_server_ready(max_wait_sec: float = 15.0) -> bool:
    """Run mega-version until it succeeds (server ready) or timeout. Returns True if ready."""
    env = _subprocess_env()
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


async def _ensure_mega_cmd_server_running() -> bool:
    """
    On desktop (non-Docker), start the MEGAcmd server (Linux only) and wait until it is ready.
    Mirrors entrypoint.sh: start server, delay, then use mega-get/mega-transfers.
    macOS: bundle has no mega-cmd-server; do not start MEGAcmd app (would show GUI). Only wait for ready.
    Returns True if server is ready.
    """
    if _in_docker() or SIMULATE:
        return True
    server_bin = _mega_cmd_server_binary()
    env = _subprocess_env()
    # Start server only when it is the headless binary (mega-cmd-server on Linux), not the macOS app
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
            # #region agent log
            _debug_log(
                "main.py:ensure_mega_cmd_server",
                "started mega-cmd-server and waiting for ready",
                {"server_binary": server_bin, "waited_sec": 2},
                hypothesis_id="H4",
            )
            # #endregion
        except Exception as e:
            # #region agent log
            _debug_log("main.py:ensure_mega_cmd_server", "server start failed", {"error": str(e), "server_binary": server_bin}, hypothesis_id="H4")
            # #endregion
            pass
    ready = await _wait_for_mega_server_ready()
    # #region agent log
    _debug_log("main.py:ensure_mega_cmd_server", "server ready check", {"ready": ready}, hypothesis_id="H4")
    # #endregion
    return ready


def log_append(page: ft.Page, log: ft.TextField, line: str) -> None:
    """Append a message line to the log and refresh UI."""
    global _message_lines
    _message_lines.append(line)
    if _refresh_ui_callback:
        _refresh_ui_callback()


async def run_mega_get(url: str, page: ft.Page, log: ft.TextField) -> None:
    """Run mega-get for URL (or simulate)."""
    if SIMULATE:
        log_append(page, log, "URL Accepted (simulated)")
        await asyncio.sleep(1)
        return
    # #region agent log
    download_dir_abs = os.path.abspath(DOWNLOAD_DIR)
    _debug_log(
        "main.py:run_mega_get:entry",
        "mega-get invoked",
        {"url_preview": url.strip()[:80], "download_dir": download_dir_abs, "cwd": os.getcwd()},
        hypothesis_id="H1 H4",
    )
    # #endregion
    
    log_append(page, log, f"Starting download to {DOWNLOAD_DIR}...")
    
    proc = await asyncio.create_subprocess_exec(
        "mega-get",
        "-q",
        "--ignore-quota-warn",
        url.strip(),
        download_dir_abs,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_subprocess_env(),
    )
    stdout, stderr = await proc.communicate()
    # #region agent log
    _debug_log(
        "main.py:run_mega_get:exit",
        "mega-get finished",
        {
            "returncode": proc.returncode,
            "stdout_len": len(stdout or b""),
            "stdout_preview": (stdout or b"").decode(errors="replace")[:400].strip(),
            "stderr_len": len(stderr or b""),
            "stderr_preview": (stderr or b"").decode(errors="replace")[:400].strip(),
        },
        hypothesis_id="H3",
    )
    # #endregion
    if proc.returncode == 0:
        log_append(page, log, "✓ Download started successfully")
        # Give server a moment to start the transfer, then try resume once (can help with RETRYING)
        if not SIMULATE:
            await asyncio.sleep(2)
            try:
                rproc = await asyncio.create_subprocess_exec(
                    "mega-transfers", "-r", "-a",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    env=_subprocess_env(),
                )
                await rproc.communicate()
            except Exception:
                pass
    else:
        log_append(page, log, f"✗ Error: Unable to parse MEGA URL")
        if stderr:
            err_msg = stderr.decode(errors="replace").strip()
            if err_msg:
                log_append(page, log, f"Details: {err_msg}")


async def run_mega_transfers_action(action: str, tag: str, page: ft.Page, log: ft.TextField) -> None:
    """Run mega-transfers -c/-p/-r with tag (or simulate)."""
    if SIMULATE:
        log_append(page, log, f"{action.title()} transfer {tag}")
        return
    flag = {"cancel": "-c", "pause": "-p", "resume": "-r"}.get(action, "-c")
    proc = await asyncio.create_subprocess_exec(
        "mega-transfers",
        flag,
        tag.strip() if tag else "-a",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_subprocess_env(),
    )
    stdout, stderr = await proc.communicate()
    out = (stdout or b"").decode(errors="replace").strip()
    err = (stderr or b"").decode(errors="replace").strip()
    if out:
        log_append(page, log, out)
    if err and proc.returncode != 0:
        log_append(page, log, err)
    else:
        log_append(page, log, f"{action.title()} command sent for transfer {tag}")


async def get_transfer_list() -> str:
    """Return current transfer list output (or simulated/test)."""
    if SIMULATE:
        return (
            "\n"
            "TRANSFER  STATE     PROGRESS  PATH\n"
            "1         ACTIVE    12%       /data/sample_file.zip\n"
            "2         QUEUED    0%        /data/another_file.pdf\n"
        )
    
    if UI_TEST_MODE:
        return _get_test_transfer_output()
    
    # #region agent log
    _debug_log(
        "main.py:get_transfer_list",
        "calling mega-transfers",
        {
            "limit": TRANSFER_LIST_LIMIT,
            "path_display_size": PATH_DISPLAY_SIZE,
        },
        hypothesis_id="H5",
    )
    # #endregion
    
    proc = await asyncio.create_subprocess_exec(
        "mega-transfers",
        f"--limit={TRANSFER_LIST_LIMIT}",
        f"--path-display-size={PATH_DISPLAY_SIZE}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_subprocess_env(),
    )
    stdout, stderr = await proc.communicate()
    out = (stdout or b"").decode(errors="replace")
    if stderr and proc.returncode != 0:
        out += (stderr or b"").decode(errors="replace")
    
    # #region agent log - Always log the output for debugging
    _debug_log(
        "main.py:get_transfer_list",
        "mega-transfers output",
        {
            "returncode": proc.returncode,
            "stderr_present": bool(stderr and len(stderr) > 0),
            "stderr_preview": (stderr or b"").decode(errors="replace")[:300].strip() if stderr else "",
            "stdout_len": len(out),
            "stdout_full": out,  # Log the full output for debugging
        },
        hypothesis_id="H5",
    )
    # #endregion
    return out


def _parse_transfer_list(raw: str) -> list[dict]:
    """
    Parse mega-transfers text output into a list of transfer dicts.
    Each dict has: tag (str), progress_pct (0-100), state (str), path (str), filename (str), size_display (str).
    Handles real output (TYPE TAG SOURCEPATH DESTINYPATH PROGRESS STATE) and SIMULATE format.
    """
    result: list[dict] = []
    if not raw or not raw.strip():
        return result
    
    # Debug: log raw output
    _debug_log(
        "main.py:_parse_transfer_list",
        "parsing transfer output",
        {"raw_length": len(raw), "raw_preview": raw[:500]},
        hypothesis_id="H6",
    )
    
    lines = raw.strip().split("\n")
    for line_num, line in enumerate(lines):
        original_line = line
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if any(header in line for header in ["TYPE", "TAG", "STATE", "TRANSFER", "PROGRESS", "PATH"]):
            if all(h in line for h in ["TYPE", "TAG", "STATE"]):
                continue
        
        # SIMULATE format: "1         ACTIVE    12%       /data/sample_file.zip"
        sim_match = re.match(r"^\s*(\d+)\s+(\w+)\s+(\d+)%\s+(.+)$", line)
        if sim_match:
            tag, state, pct, path = sim_match.groups()
            filename = path.split("/")[-1] if "/" in path else path
            result.append({
                "tag": tag,
                "progress_pct": float(pct),
                "state": state,
                "path": path.strip(),
                "filename": filename,
                "size_display": "Unknown",
            })
            continue
        
        # Real format variations:
        # "⇓    76  /path/to/file.mkv  5.42% of  455.34 MB ACTIVE"
        # "↑    123 /path/file.zip     12.5% of  1.23 GB QUEUED"
        
        # Try to match: direction TAG path PERCENTAGE% of SIZE UNIT STATE
        real_match = re.search(
            r"([⇓↑])\s+(\d+)\s+(.*?)\s+(\d+(?:\.\d+)?)\s*%\s+of\s+([\d.]+)\s*([KMGT]?B)\s+(\w+)\s*$",
            line
        )
        
        if real_match:
            direction, tag, path_part, pct, size_val, size_unit, state = real_match.groups()
            path_part = path_part.strip()
            
            # Extract filename from path
            filename = path_part.split("/")[-1].strip() if "/" in path_part else path_part
            
            # Handle truncated paths with "..."
            if "..." in path_part and "/" in path_part:
                # Try to get the last part after ...
                parts = path_part.split("...")
                if len(parts) > 1 and "/" in parts[-1]:
                    filename = parts[-1].split("/")[-1].strip()
            
            # Truncate very long filenames
            if len(filename) > 60:
                filename = filename[:57] + "..."
            
            result.append({
                "tag": tag,
                "progress_pct": float(pct),
                "state": state,
                "path": path_part,
                "filename": filename or "Unknown",
                "size_display": f"{size_val} {size_unit}",
            })
            
            _debug_log(
                "main.py:_parse_transfer_list",
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
        
        # If we get here, the line didn't match any pattern
        if len(line) > 10:  # Only log substantial lines we couldn't parse
            _debug_log(
                "main.py:_parse_transfer_list",
                "unparsed line",
                {"line_num": line_num, "line": line[:200]},
                hypothesis_id="H6",
            )
    
    _debug_log(
        "main.py:_parse_transfer_list",
        "parsing complete",
        {"total_lines": len(lines), "parsed_transfers": len(result)},
        hypothesis_id="H6",
    )
    
    return result


# Shared state: message lines (user/command output) and latest transfer list
_message_lines: list[str] = []
_transfer_list: str = ""
_retrying_hint_shown: bool = False
_url_history: list[str] = []
_url_history_max = 50
_history_file_path: str | None = None
_refresh_ui_callback: callable | None = None

# UI Test mode: set to True to show sample transfers for testing
UI_TEST_MODE = os.environ.get("UI_TEST_MODE", "").strip().lower() in ("1", "true", "yes")

def _get_test_transfer_output() -> str:
    """Generate realistic test transfer output for UI development."""
    return """
⇓    1234  /Downloads/ubuntu-22.04.iso  45.2% of  3.54 GB ACTIVE
↑    5678  /Uploads/video.mp4  78.5% of  1.23 GB ACTIVE
⇓    9012  /Downloads/document.pdf  0.0% of  15.2 MB QUEUED
⇓    3456  /Downloads/large_archive.zip  12.8% of  8.91 GB RETRYING
"""


def _load_history() -> None:
    """Load URL history from JSON file if _history_file_path is set."""
    global _url_history
    if not _history_file_path or not os.path.isfile(_history_file_path):
        return
    try:
        with open(_history_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            _url_history = [u for u in data if isinstance(u, str)][:_url_history_max]
    except Exception:
        pass


def _save_history() -> None:
    """Save URL history to JSON file if _history_file_path is set."""
    if not _history_file_path:
        return
    try:
        with open(_history_file_path, "w", encoding="utf-8") as f:
            json.dump(_url_history[:_url_history_max], f, ensure_ascii=False)
    except Exception:
        pass


def _build_transfer_cards(
    page: ft.Page,
    log: ft.TextField,
    transfers: list[dict],
) -> list[ft.Control]:
    """Build a list of Card controls for the transfer list."""
    cards: list[ft.Control] = []
    for t in transfers:
        tag = str(t["tag"])
        pct = t["progress_pct"] / 100.0
        state = t["state"]
        filename = t.get("filename", t.get("path", ""))
        size_display = t.get("size_display", "Unknown")
        
        # Color code the state
        state_color = {
            "ACTIVE": ft.Colors.GREEN_400,
            "PAUSED": ft.Colors.ORANGE_400,
            "QUEUED": ft.Colors.BLUE_400,
            "RETRYING": ft.Colors.YELLOW_400,
            "COMPLETED": ft.Colors.GREEN_600,
            "FAILED": ft.Colors.RED_400,
        }.get(state, ft.Colors.GREY_400)
        
        # Progress bar color based on state
        progress_color = state_color if state == "ACTIVE" else ft.Colors.GREY_500

        def make_action(action: str, ttag: str):
            async def handler(e: ft.ControlEvent) -> None:
                page.run_task(run_mega_transfers_action, action, ttag, page, log)
            return handler

        cancel_btn = ft.IconButton(
            icon=ft.Icons.CANCEL,
            tooltip="Cancel",
            on_click=make_action("cancel", tag),
            icon_color=ft.Colors.RED_400,
            icon_size=20,
        )
        pause_btn = ft.IconButton(
            icon=ft.Icons.PAUSE,
            tooltip="Pause",
            on_click=make_action("pause", tag),
            icon_color=ft.Colors.ORANGE_400,
            icon_size=20,
        )
        resume_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            tooltip="Resume",
            on_click=make_action("resume", tag),
            icon_color=ft.Colors.GREEN_400,
            icon_size=20,
        )
        
        # Build progress text
        progress_text = f"{int(pct * 100)}%"
        if size_display != "Unknown":
            progress_text = f"{int(pct * 100)}% of {size_display}"
        
        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        # Header row: filename and state badge
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.CLOUD_DOWNLOAD if state in ["ACTIVE", "QUEUED", "PAUSED"] else ft.Icons.CHECK_CIRCLE,
                                    size=20,
                                    color=state_color,
                                ),
                                ft.Text(
                                    filename,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    expand=True,
                                    size=14,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        state,
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        color=state_color,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.1, state_color),
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=4,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            spacing=8,
                        ),
                        # Progress bar row
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            progress_text,
                                            size=12,
                                            color=ft.Colors.GREY_400,
                                        ),
                                    ],
                                ),
                                ft.ProgressBar(
                                    value=pct,
                                    bar_height=10,
                                    color=progress_color,
                                    bgcolor=ft.Colors.with_opacity(0.2, state_color),
                                    border_radius=5,
                                ),
                            ],
                            spacing=4,
                        ),
                        # Action buttons row
                        ft.Row(
                            [
                                ft.Text(f"Tag: {tag}", size=10, color=ft.Colors.GREY_500),
                                ft.Container(expand=True),
                                resume_btn,
                                pause_btn,
                                cancel_btn,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=8,
                ),
                padding=14,
            ),
            elevation=2,
        )
        cards.append(card)
    return cards


def _refresh_ui(
    page: ft.Page,
    transfers_container: ft.Column,
    log_text: ft.TextField,
) -> None:
    """Rebuild transfer cards and log text from current state."""
    parsed = _parse_transfer_list(_transfer_list)
    transfers_container.controls = _build_transfer_cards(page, log_text, parsed)
    
    # Show helpful message when no transfers
    if not parsed:
        # Check if we have raw output but failed to parse
        if _transfer_list and len(_transfer_list.strip()) > 0:
            # We got output but couldn't parse it
            transfers_container.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.WARNING, size=48, color=ft.Colors.ORANGE_400),
                            ft.Text(
                                "Unable to parse transfer data",
                                size=16,
                                color=ft.Colors.ORANGE_400,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Check the log below for raw output",
                                size=12,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    _transfer_list[:500] + ("..." if len(_transfer_list) > 500 else ""),
                                    size=10,
                                    color=ft.Colors.GREY_600,
                                    selectable=True,
                                ),
                                bgcolor="#1a1a1a",
                                padding=10,
                                border_radius=5,
                                border=ft.Border.all(1, "#333333"),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    padding=40,
                    alignment=ft.alignment.Alignment(0, 0),
                )
            ]
        else:
            # No output at all - no active transfers
            transfers_container.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, size=48, color=ft.Colors.GREY_600),
                            ft.Text(
                                "No active transfers",
                                size=16,
                                color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Add a MEGA URL above to start downloading",
                                size=12,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.alignment.Alignment(0, 0),
                )
            ]
    
    log_text.value = "\n".join(_message_lines) if _message_lines else "Ready to download..."
    page.update()


async def poll_transfers(page: ft.Page, refresh_callback: callable | None = None) -> None:
    """Background task: periodically refresh transfer list and UI."""
    global _transfer_list, _retrying_hint_shown
    poll_count = 0
    while True:
        try:
            out = await get_transfer_list()
            _transfer_list = out
            # One-time hint when transfer is RETRYING at 0% (known MEGAcmd behavior)
            if not _retrying_hint_shown and "RETRYING" in out:
                _retrying_hint_shown = True
                _message_lines.append(
                    "⚠ If transfers stay at 0% (RETRYING), try Resume, or Cancel and re-add the URL."
                )
            # #region agent log
            poll_count += 1
            if poll_count <= 5 or poll_count % 10 == 0:
                _debug_log(
                    "main.py:poll_transfers",
                    "poll cycle complete",
                    {"poll_count": poll_count, "transfers_found": len(_parse_transfer_list(out))},
                    hypothesis_id="H5",
                )
            # #endregion
            if refresh_callback:
                refresh_callback()
            elif _refresh_ui_callback:
                _refresh_ui_callback()
        except Exception as e:
            _message_lines.append(f"Poll error: {e}")
            if _refresh_ui_callback:
                _refresh_ui_callback()
        await asyncio.sleep(POLL_INTERVAL)


async def main(page: ft.Page) -> None:
    global _refresh_ui_callback, _url_history, _history_file_path
    
    page.title = "MEGA Get"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    # App bar with gradient background
    page.appbar = ft.AppBar(
        title=ft.Row(
            [
                ft.Icon(ft.Icons.CLOUD_DOWNLOAD, color=ft.Colors.BLUE_400),
                ft.Text("MEGA Get", size=20, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        ),
        center_title=False,
        bgcolor="#2a2a2a",
    )
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _history_file_path = os.path.join(project_root, ".mega-get-history.json")
    _load_history()
    
    # Desktop: start mega-cmd-server (Linux) and wait until server is ready
    if not SIMULATE and not UI_TEST_MODE:
        _message_lines.append("⏳ Initializing MEGAcmd...")
    
    if UI_TEST_MODE:
        _message_lines.append("🧪 UI TEST MODE - Showing sample transfers for development")
        _message_lines.append("ℹ Set UI_TEST_MODE=0 or remove env var to use real MEGAcmd")
    
    server_ready = await _ensure_mega_cmd_server_running()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    if not server_ready and not _in_docker() and sys.platform == "darwin" and not UI_TEST_MODE:
        _message_lines.append("⚠ MEGAcmd server not detected. Open MEGAcmd from Applications, then restart this app.")
    elif server_ready and not UI_TEST_MODE:
        _message_lines.append(f"✓ MEGAcmd ready. Downloads will be saved to: {DOWNLOAD_DIR}")
    
    if SIMULATE:
        _message_lines.append("ℹ Simulation mode (MEGA_SIMULATE=1) - no MEGA CMD required.")
    
    # #region agent log
    download_dir_abs = os.path.abspath(DOWNLOAD_DIR)
    subprocess_env = _subprocess_env()
    path_for_resolve = subprocess_env.get("PATH", "")
    mega_get_resolved = shutil.which("mega-get", path=path_for_resolve) if path_for_resolve else None
    run_mode = "web" if _is_web_server_mode() else "desktop"
    _debug_log(
        "main.py:main:startup",
        "DOWNLOAD_DIR, permissions, and local MEGAcmd (desktop)",
        {
            "run_mode": run_mode,
            "DOWNLOAD_DIR": DOWNLOAD_DIR,
            "download_dir_abs": download_dir_abs,
            "exists": os.path.isdir(DOWNLOAD_DIR),
            "writable": os.access(DOWNLOAD_DIR, os.W_OK),
            "cwd": os.getcwd(),
            "MEGACMD_PATH": MEGACMD_PATH or "(none)",
            "mega_get_binary": mega_get_resolved or "(not found in PATH)",
            "PATH_prefix": (path_for_resolve or "")[:200],
            "server_ready": server_ready,
        },
        hypothesis_id="H1 H2 H4",
    )
    # #endregion

    url_field = ft.TextField(
        label="MEGA URL",
        hint_text="https://mega.nz/#!xxxxxxxx!xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        border_radius=8,
        filled=True,
        prefix_icon=ft.Icons.LINK,
        expand=True,
    )
    
    get_btn = ft.Button(
        "Download",
        icon=ft.Icons.CLOUD_DOWNLOAD,
        on_click=None,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        ),
    )

    log_text = ft.TextField(
        multiline=True,
        read_only=True,
        min_lines=6,
        max_lines=10,
        value="Ready to download...",
        border_radius=8,
        filled=True,
    )
    
    transfers_container = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=12,
    )
    
    history_list_column = ft.Column(
        spacing=4,
        scroll=ft.ScrollMode.AUTO,
    )

    def do_refresh_ui() -> None:
        _refresh_ui(page, transfers_container, log_text)
        _refresh_history_ui(history_list_column, url_field)

    _refresh_ui_callback = do_refresh_ui  # noqa: PLW0603

    async def on_get(_: ft.ControlEvent) -> None:
        url = url_field.value
        if not (url and url.strip()):
            log_append(page, log_text, "⚠ Please enter a MEGA URL")
            return
        url = url.strip()
        
        # Add to history
        if url in _url_history:
            _url_history.remove(url)
        _url_history.insert(0, url)
        if len(_url_history) > _url_history_max:
            _url_history.pop()
        _save_history()
        
        # Clear URL field
        url_field.value = ""
        page.update()
        
        # Start download
        page.run_task(run_mega_get, url, page, log_text)
        do_refresh_ui()

    get_btn.on_click = on_get

    def clear_history_local(_e: ft.ControlEvent) -> None:
        global _url_history
        _url_history.clear()
        _save_history()
        _refresh_history_ui(history_list_column, url_field)
        page.update()

    def _refresh_history_ui(history_col: ft.Column, url_f: ft.TextField) -> None:
        history_col.controls.clear()
        for u in _url_history[:30]:
            def make_click(link: str):
                def handler(e: ft.ControlEvent) -> None:
                    url_f.value = link
                    page.update()
                return handler
            tile = ft.ListTile(
                leading=ft.Icon(ft.Icons.HISTORY, size=16),
                title=ft.Text(
                    u[:60] + "..." if len(u) > 60 else u,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    size=11,
                ),
                on_click=make_click(u),
                dense=True,
            )
            history_col.controls.append(tile)
        if _url_history:
            history_col.controls.append(
                ft.Container(
                    content=ft.TextButton(
                        "Clear history",
                        icon=ft.Icons.DELETE_SWEEP,
                        on_click=clear_history_local,
                    ),
                    padding=ft.Padding.only(top=8),
                )
            )
        page.update()

    # Add URL section
    add_url_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Add Download", size=18, weight=ft.FontWeight.W_500),
                ft.Row(
                    [url_field, get_btn],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=12,
        ),
        padding=16,
        border_radius=8,
        bgcolor="#2a2a2a",
    )
    
    # Transfers section
    transfers_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Active Transfers", size=18, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=transfers_container,
                    expand=True,
                    border=ft.Border.all(1, "#444444"),
                    border_radius=8,
                    padding=12,
                    bgcolor="#1e1e1e",
                ),
            ],
            expand=True,
            spacing=12,
        ),
        expand=True,
        padding=16,
    )
    
    # History section
    history_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Recent URLs", size=18, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=history_list_column,
                    height=300,
                    border=ft.Border.all(1, "#444444"),
                    border_radius=8,
                    padding=8,
                    bgcolor="#1e1e1e",
                ),
            ],
            spacing=12,
        ),
        padding=16,
    )
    
    # Main content area with responsive row
    main_content = ft.Row(
        [
            ft.Container(content=transfers_section, expand=2),
            ft.Container(content=history_section, expand=1),
        ],
        spacing=0,
        expand=True,
    )
    
    # Log section as expansion panel
    log_expansion = ft.ExpansionPanel(
        header=ft.ListTile(
            leading=ft.Icon(ft.Icons.TERMINAL),
            title=ft.Text("Log", weight=ft.FontWeight.W_500),
        ),
        content=ft.Container(content=log_text, padding=16),
        can_tap_header=True,
    )
    
    log_panel_list = ft.ExpansionPanelList(
        controls=[log_expansion],
        elevation=0,
    )
    
    # Add all sections to page
    page.add(
        ft.Column(
            [
                add_url_section,
                main_content,
                log_panel_list,
            ],
            spacing=16,
            expand=True,
        )
    )
    
    do_refresh_ui()
    page.run_task(poll_transfers, page, do_refresh_ui)


def _is_web_server_mode() -> bool:
    """True if app should run as web server (Docker, headless, or FLET_FORCE_WEB_SERVER)."""
    if os.environ.get("FLET_FORCE_WEB_SERVER", "").strip().lower() in ("1", "true", "yes"):
        return True
    if _in_docker():
        return True
    if sys.platform == "linux" and not os.environ.get("DISPLAY"):
        return True
    return False


if __name__ == "__main__":
    if _is_web_server_mode():
        port = int(os.environ.get("FLET_SERVER_PORT", "8080"))
        ft.run(main, view=ft.AppView.FLET_APP_WEB, port=port)
    else:
        ft.run(main)
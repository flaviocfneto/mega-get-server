"""
MEGA Get - Flet prototype.
Web UI for mega-get-server: add MEGA URLs, view transfers, cancel/pause/resume.
Runs as desktop (native window), web (browser/server), or in Docker; adapts view, port, and DOWNLOAD_DIR.
Uses env vars: DOWNLOAD_DIR, TRANSFER_LIST_LIMIT, PATH_DISPLAY_SIZE, INPUT_TIMEOUT.
Set MEGA_SIMULATE=1 to run without MEGA CMD (fake transfer list and messages).
On macOS, uses local MEGAcmd from /Applications/MEGAcmd.app if MEGACMD_PATH is not set.
"""
import asyncio
import json
import os
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


async def _ensure_mega_cmd_server_running() -> None:
    """
    On desktop (non-Docker), start the MEGAcmd server (Linux only) and wait until it is ready.
    Mirrors entrypoint.sh: start server, delay, then use mega-get/mega-transfers.
    macOS: bundle has no mega-cmd-server; do not start MEGAcmd app (would show GUI). Only wait for ready.
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
    _refresh_log(page, log)


async def run_mega_get(url: str, page: ft.Page, log: ft.TextField) -> None:
    """Run mega-get for URL (or simulate)."""
    if SIMULATE:
        log_append(page, log, "URL Accepted (simulated)")
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
        log_append(page, log, "URL Accepted")
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
        log_append(page, log, f"Error parsing MEGA URL: '{url.strip()}'")
        if stderr:
            log_append(page, log, stderr.decode(errors="replace").strip())


async def run_mega_transfers_action(action: str, tag: str, page: ft.Page, log: ft.TextField) -> None:
    """Run mega-transfers -c/-p/-r with tag (or simulate)."""
    if SIMULATE:
        log_append(page, log, f"{action} (simulated): {tag or '(no tag)'}")
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


async def get_transfer_list() -> str:
    """Return current transfer list output (or simulated)."""
    if SIMULATE:
        return (
            "\n"
            "TRANSFER  STATE     PROGRESS  PATH\n"
            "1         ACTIVE    12%       /data/sample_file.zip\n"
            "2         QUEUED    0%        /data/another_file.pdf\n"
        )
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
    # #region agent log
    if proc.returncode != 0 or (stderr and len(stderr) > 0):
        _debug_log(
            "main.py:get_transfer_list",
            "mega-transfers error or stderr",
            {
                "returncode": proc.returncode,
                "stderr_preview": (stderr or b"").decode(errors="replace")[:300].strip(),
                "out_len": len(out),
                "out_preview": out[:300].strip(),
            },
            hypothesis_id="H5",
        )
    # #endregion
    return out


# Shared state: message lines (user/command output) and latest transfer list
_message_lines: list[str] = []
_transfer_list: str = ""
_retrying_hint_shown: bool = False


def _refresh_log(page: ft.Page, log: ft.TextField) -> None:
    """Rebuild log from messages + transfer list."""
    parts = ["\n".join(_message_lines)] if _message_lines else []
    if _transfer_list:
        parts.append(_transfer_list)
    log.value = "\n\n".join(parts) or "No data yet."
    page.update()


async def poll_transfers(page: ft.Page, log: ft.TextField) -> None:
    """Background task: periodically refresh transfer list in the log."""
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
                    "If transfers stay at 0% (RETRYING), try Resume, or Cancel and re-add the URL. "
                    "Export links work without login; persistent RETRYING can be a MEGAcmd/network limitation."
                )
            # #region agent log
            poll_count += 1
            if poll_count <= 3 or poll_count % 20 == 0:
                _debug_log(
                    "main.py:poll_transfers",
                    "transfer list sample",
                    {"poll_count": poll_count, "out_len": len(out), "out_preview": out[:350].strip()},
                    hypothesis_id="H5",
                )
            # #endregion
            _refresh_log(page, log)
        except Exception as e:
            _message_lines.append(f"Poll error: {e}")
            _refresh_log(page, log)
        await asyncio.sleep(POLL_INTERVAL)


async def main(page: ft.Page) -> None:
    page.title = "MEGA Get"
    page.theme_mode = ft.ThemeMode.DARK
    # Desktop: start mega-cmd-server (Linux) and wait until server is ready
    server_ready = await _ensure_mega_cmd_server_running()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    if not server_ready and not _in_docker() and sys.platform == "darwin":
        _message_lines.append("MEGAcmd server not detected. Open MEGAcmd from Applications once, then try Get.")
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
        },
        hypothesis_id="H1 H2 H4",
    )
    # #endregion

    url_field = ft.TextField(
        label="MEGA URL",
        hint_text="https://mega.nz/#!xxxxxxxx!xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        expand=True,
    )
    transfer_tag_field = ft.TextField(
        label="Transfer Tag",
        hint_text="or all with -a",
        width=120,
    )
    if SIMULATE:
        _message_lines.append("Simulation mode (MEGA_SIMULATE=1) - no MEGA CMD required.")

    log = ft.TextField(
        multiline=True,
        read_only=True,
        min_lines=15,
        expand=True,
        value="No data yet. Add a URL or wait for transfer list.",
    )

    async def on_get(_: ft.ControlEvent) -> None:
        url = url_field.value
        if not (url and url.strip()):
            log_append(page, log, "Enter a MEGA URL.")
            return
        page.run_task(run_mega_get, url.strip(), page, log)

    async def on_cancel(_: ft.ControlEvent) -> None:
        page.run_task(run_mega_transfers_action, "cancel", transfer_tag_field.value or "", page, log)

    async def on_pause(_: ft.ControlEvent) -> None:
        page.run_task(run_mega_transfers_action, "pause", transfer_tag_field.value or "", page, log)

    async def on_resume(_: ft.ControlEvent) -> None:
        page.run_task(run_mega_transfers_action, "resume", transfer_tag_field.value or "", page, log)

    page.add(
        ft.Row(
            [
                url_field,
                ft.ElevatedButton("Get", on_click=on_get),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        ft.Row(
            [
                transfer_tag_field,
                ft.ElevatedButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Pause", on_click=on_pause),
                ft.ElevatedButton("Resume", on_click=on_resume),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        log,
    )
    _refresh_log(page, log)

    page.run_task(poll_transfers, page, log)


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
        ft.app(target=main, view=ft.AppView.FLET_APP_WEB, port=port)
    else:
        ft.app(target=main, view=ft.AppView.FLET_APP)

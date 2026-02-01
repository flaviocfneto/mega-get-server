"""
MEGA Get - Flet prototype.
Web UI for mega-get-server: add MEGA URLs, view transfers, cancel/pause/resume.
Runs as desktop (native window), web (browser/server), or in Docker; adapts view, port, and DOWNLOAD_DIR.
Uses env vars: DOWNLOAD_DIR, TRANSFER_LIST_LIMIT, PATH_DISPLAY_SIZE, INPUT_TIMEOUT.
Set MEGA_SIMULATE=1 to run without MEGA CMD (fake transfer list and messages).
On macOS, uses local MEGAcmd from /Applications/MEGAcmd.app if MEGACMD_PATH is not set.
"""
import asyncio
import os
import sys

import flet as ft


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
    proc = await asyncio.create_subprocess_exec(
        "mega-get",
        "-q",
        "--ignore-quota-warn",
        url.strip(),
        DOWNLOAD_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_subprocess_env(),
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        log_append(page, log, "URL Accepted")
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
    return out


# Shared state: message lines (user/command output) and latest transfer list
_message_lines: list[str] = []
_transfer_list: str = ""


def _refresh_log(page: ft.Page, log: ft.TextField) -> None:
    """Rebuild log from messages + transfer list."""
    parts = ["\n".join(_message_lines)] if _message_lines else []
    if _transfer_list:
        parts.append(_transfer_list)
    log.value = "\n\n".join(parts) or "No data yet."
    page.update()


async def poll_transfers(page: ft.Page, log: ft.TextField) -> None:
    """Background task: periodically refresh transfer list in the log."""
    global _transfer_list
    while True:
        try:
            out = await get_transfer_list()
            _transfer_list = out
            _refresh_log(page, log)
        except Exception as e:
            _message_lines.append(f"Poll error: {e}")
            _refresh_log(page, log)
        await asyncio.sleep(POLL_INTERVAL)


async def main(page: ft.Page) -> None:
    page.title = "MEGA Get"
    page.theme_mode = ft.ThemeMode.DARK
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

"""
MEGA Get - Flet prototype.
Web UI for mega-get-server: add MEGA URLs, view transfers, cancel/pause/resume.
"""
import asyncio
import os
import shutil
import sys

import flet as ft

import mega_service as ms

_transfer_list: str = ""
_retrying_hint_shown: bool = False
_refresh_ui_callback: callable | None = None


def _refresh_ui(
    page: ft.Page,
    transfers_container: ft.Column,
    log_text: ft.TextField,
) -> None:
    parsed = ms.parse_transfer_list(_transfer_list)
    transfers_container.controls = _build_transfer_cards(page, log_text, parsed)

    if not parsed:
        if _transfer_list and len(_transfer_list.strip()) > 0:
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

    lines = ms.log_buffer.get_lines()
    log_text.value = "\n".join(lines) if lines else "Ready to download..."
    page.update()


def _build_transfer_cards(
    page: ft.Page,
    log: ft.TextField,
    transfers: list[dict],
) -> list[ft.Control]:
    cards: list[ft.Control] = []
    for t in transfers:
        tag = str(t["tag"])
        pct = t["progress_pct"] / 100.0
        state = t["state"]
        filename = t.get("filename", t.get("path", ""))
        size_display = t.get("size_display", "Unknown")

        state_color = {
            "ACTIVE": ft.Colors.GREEN_400,
            "PAUSED": ft.Colors.ORANGE_400,
            "QUEUED": ft.Colors.BLUE_400,
            "RETRYING": ft.Colors.YELLOW_400,
            "COMPLETED": ft.Colors.GREEN_600,
            "FAILED": ft.Colors.RED_400,
        }.get(state, ft.Colors.GREY_400)

        progress_color = state_color if state == "ACTIVE" else ft.Colors.GREY_500

        cancel_btn = ft.IconButton(
            icon=ft.Icons.CANCEL,
            tooltip="Cancel",
            on_click=lambda e, tg=tag: page.run_task(ms.run_mega_transfers_action, "cancel", tg),
            icon_color=ft.Colors.RED_400,
            icon_size=20,
        )
        pause_btn = ft.IconButton(
            icon=ft.Icons.PAUSE,
            tooltip="Pause",
            on_click=lambda e, tg=tag: page.run_task(ms.run_mega_transfers_action, "pause", tg),
            icon_color=ft.Colors.ORANGE_400,
            icon_size=20,
        )
        resume_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            tooltip="Resume",
            on_click=lambda e, tg=tag: page.run_task(ms.run_mega_transfers_action, "resume", tg),
            icon_color=ft.Colors.GREEN_400,
            icon_size=20,
        )

        progress_text = f"{int(pct * 100)}%"
        if size_display != "Unknown":
            progress_text = f"{int(pct * 100)}% of {size_display}"

        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
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


async def poll_transfers(page: ft.Page, refresh_callback: callable | None = None) -> None:
    global _transfer_list, _retrying_hint_shown
    poll_count = 0
    while True:
        try:
            out = await ms.get_transfer_list()
            _transfer_list = out
            if not _retrying_hint_shown and "RETRYING" in out:
                _retrying_hint_shown = True
                ms.log_buffer.append(
                    "⚠ If transfers stay at 0% (RETRYING), try Resume, or Cancel and re-add the URL."
                )
            poll_count += 1
            if poll_count <= 5 or poll_count % 10 == 0:
                ms._debug_log(
                    "main.py:poll_transfers",
                    "poll cycle complete",
                    {"poll_count": poll_count, "transfers_found": len(ms.parse_transfer_list(out))},
                    hypothesis_id="H5",
                )
            if refresh_callback:
                refresh_callback()
            elif _refresh_ui_callback:
                _refresh_ui_callback()
        except Exception as e:
            ms.log_buffer.append(f"Poll error: {e}")
            if _refresh_ui_callback:
                _refresh_ui_callback()
        await asyncio.sleep(ms.POLL_INTERVAL)


async def main(page: ft.Page) -> None:
    global _refresh_ui_callback

    page.title = "MEGA Get"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

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
    ms.set_history_path(os.path.join(project_root, ".mega-get-history.json"))
    ms.load_history()

    if not ms.SIMULATE and not ms.UI_TEST_MODE:
        ms.log_buffer.append("⏳ Initializing MEGAcmd...")

    if ms.UI_TEST_MODE:
        ms.log_buffer.append("🧪 UI TEST MODE - Showing sample transfers for development")
        ms.log_buffer.append("ℹ Set UI_TEST_MODE=0 or remove env var to use real MEGAcmd")

    server_ready = await ms.ensure_mega_cmd_server_running()
    os.makedirs(ms.DOWNLOAD_DIR, exist_ok=True)

    if not server_ready and not ms.in_docker() and sys.platform == "darwin" and not ms.UI_TEST_MODE:
        ms.log_buffer.append("⚠ MEGAcmd server not detected. Open MEGAcmd from Applications, then restart this app.")
    elif server_ready and not ms.UI_TEST_MODE:
        ms.log_buffer.append(f"✓ MEGAcmd ready. Downloads will be saved to: {ms.DOWNLOAD_DIR}")

    if ms.SIMULATE:
        ms.log_buffer.append("ℹ Simulation mode (MEGA_SIMULATE=1) - no MEGA CMD required.")

    download_dir_abs = os.path.abspath(ms.DOWNLOAD_DIR)
    subprocess_env = ms.subprocess_env()
    path_for_resolve = subprocess_env.get("PATH", "")
    mega_get_resolved = shutil.which("mega-get", path=path_for_resolve) if path_for_resolve else None
    run_mode = "web" if ms.is_web_server_mode() else "desktop"
    ms._debug_log(
        "main.py:main:startup",
        "DOWNLOAD_DIR, permissions, and local MEGAcmd (desktop)",
        {
            "run_mode": run_mode,
            "DOWNLOAD_DIR": ms.DOWNLOAD_DIR,
            "download_dir_abs": download_dir_abs,
            "exists": os.path.isdir(ms.DOWNLOAD_DIR),
            "writable": os.access(ms.DOWNLOAD_DIR, os.W_OK),
            "cwd": os.getcwd(),
            "MEGACMD_PATH": ms.MEGACMD_PATH or "(none)",
            "mega_get_binary": mega_get_resolved or "(not found in PATH)",
            "PATH_prefix": (path_for_resolve or "")[:200],
            "server_ready": server_ready,
        },
        hypothesis_id="H1 H2 H4",
    )

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

    global _refresh_ui_callback
    _refresh_ui_callback = do_refresh_ui
    ms.set_log_notify(do_refresh_ui)

    async def on_get(_: ft.ControlEvent) -> None:
        url = url_field.value
        if not (url and url.strip()):
            ms.log_buffer.append("⚠ Please enter a MEGA URL")
            do_refresh_ui()
            return
        url = url.strip()
        ms.add_url_to_history(url)
        url_field.value = ""
        page.update()
        await ms.run_mega_get(url)
        do_refresh_ui()

    get_btn.on_click = on_get

    def clear_history_local(_e: ft.ControlEvent) -> None:
        ms.clear_history()
        _refresh_history_ui(history_list_column, url_field)
        page.update()

    def _refresh_history_ui(history_col: ft.Column, url_f: ft.TextField) -> None:
        history_col.controls.clear()
        for u in ms.get_history()[:30]:
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
        if ms.get_history():
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

    main_content = ft.Row(
        [
            ft.Container(content=transfers_section, expand=2),
            ft.Container(content=history_section, expand=1),
        ],
        spacing=0,
        expand=True,
    )

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


if __name__ == "__main__":
    if ms.is_web_server_mode():
        port = int(os.environ.get("FLET_SERVER_PORT", "8080"))
        ft.run(main, view=ft.AppView.FLET_APP_WEB, port=port)
    else:
        ft.run(main)

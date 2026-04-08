"""Persisted UI-only settings (JSON). Does not change MEGAcmd download directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path(__file__).resolve().parent / "ui_settings.json"

DEFAULT_UI_KEYS: dict[str, Any] = {
    "history_limit": 50,
    "history_retention_days": 7,
    "max_retries": 3,
    "global_speed_limit_kbps": 0,
    "scheduled_start": "00:00",
    "scheduled_stop": "23:59",
    "is_scheduling_enabled": False,
    "sound_alerts_enabled": True,
    "is_privacy_mode": False,
    "is_compact_mode": False,
    "post_download_action": "",
    "webhook_url": "",
    "watch_folder_enabled": False,
    "watch_folder_path": "/downloads/watch",
}


def load_stored() -> dict[str, Any]:
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_stored(data: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_post_into_stored(body: dict[str, Any]) -> None:
    stored = load_stored()
    for key in DEFAULT_UI_KEYS:
        if key not in body:
            continue
        val = body[key]
        if val is None:
            continue
        default = DEFAULT_UI_KEYS[key]
        if isinstance(default, bool):
            stored[key] = bool(val)
        elif isinstance(default, int):
            try:
                stored[key] = int(val)
            except (TypeError, ValueError):
                pass
        else:
            stored[key] = str(val)
    save_stored(stored)

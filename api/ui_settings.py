"""Persisted UI-only settings (JSON). Does not change MEGAcmd download directory."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import http_downloads as hd
from services.json_store import read_json_dict, write_json_atomic

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

_cache: dict[str, Any] | None = None


def load_stored() -> dict[str, Any]:
    global _cache
    if _cache is not None:
        return copy.deepcopy(_cache)
    _cache = read_json_dict(SETTINGS_PATH)
    return copy.deepcopy(_cache)


def save_stored(data: dict[str, Any]) -> None:
    global _cache
    _cache = copy.deepcopy(data)
    write_json_atomic(SETTINGS_PATH, data)


def clear_cache() -> None:
    global _cache
    _cache = None


def merge_post_into_stored(body: dict[str, Any]) -> None:
    stored = load_stored()
    for key in DEFAULT_UI_KEYS:
        if key not in body:
            continue
        val = body[key]
        if val is None:
            continue

        if key == "webhook_url":
            url = str(val).strip()
            if len(url) > 1024:
                continue
            if url:
                parsed = urlparse(url)
                if parsed.scheme not in {"http", "https"}:
                    continue
                host = (parsed.hostname or "").lower()
                if not host or hd._host_is_blocked(host):
                    continue
            stored[key] = url
            continue

        if key == "watch_folder_path":
            path = str(val).strip()
            if len(path) > 1024 or ".." in path:
                # Basic path traversal protection for watch folder
                continue
            stored[key] = path
            continue

        if key == "post_download_action":
            action = str(val).strip()
            if len(action) > 1024:
                continue
            stored[key] = action
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

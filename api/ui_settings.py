"""Persisted UI-only settings (JSON). Does not change MEGAcmd download directory."""

from __future__ import annotations

import copy
import os
import re
import threading
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
_lock = threading.RLock()


def load_stored() -> dict[str, Any]:
    global _cache
    with _lock:
        if _cache is not None:
            return copy.deepcopy(_cache)
        if os.name == "posix" and SETTINGS_PATH.is_file():
            try:
                st = os.stat(SETTINGS_PATH)
                if (st.st_mode & 0o777) != 0o600:
                    os.chmod(SETTINGS_PATH, 0o600)
            except OSError:
                pass
        _cache = read_json_dict(SETTINGS_PATH)
        return copy.deepcopy(_cache)


def save_stored(data: dict[str, Any]) -> None:
    global _cache
    with _lock:
        _cache = copy.deepcopy(data)
        write_json_atomic(SETTINGS_PATH, data)


def clear_cache() -> None:
    global _cache
    with _lock:
        _cache = None


def merge_post_into_stored(body: dict[str, Any]) -> None:
    with _lock:
        stored = load_stored()
        for key in DEFAULT_UI_KEYS:
            if key not in body:
                continue
            val = body[key]
            if val is None:
                continue

            # Defense-in-depth: Reject any ASCII control characters (like newlines, tabs, null-bytes) in sensitive settings
            if key in {"webhook_url", "watch_folder_path", "post_download_action"}:
                if any(ord(c) < 32 or ord(c) == 127 for c in str(val)):
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
                # Validate that path is an absolute path and does not contain relative traversal components
                if len(path) > 1024 or not os.path.isabs(path):
                    continue
                norm_path = os.path.normpath(path)
                if ".." in norm_path.split(os.sep) or ".." in path:
                    continue
                stored[key] = norm_path
                continue

            if key == "post_download_action":
                action = str(val).strip().lower()
                allowed_actions = {"", "none", "notify", "extract", "delete", "move"}
                if action not in allowed_actions:
                    continue
                stored[key] = action
                continue

            if key in {"scheduled_start", "scheduled_stop"}:
                time_str = str(val).strip()
                if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", time_str):
                    continue
                stored[key] = time_str
                continue

            default = DEFAULT_UI_KEYS[key]
            if isinstance(default, bool):
                stored[key] = bool(val)
            elif isinstance(default, int):
                try:
                    v = int(val)
                    if key == "history_limit" and not (1 <= v <= 1000):
                        continue
                    if key == "history_retention_days" and not (1 <= v <= 365):
                        continue
                    if key == "max_retries" and not (0 <= v <= 100):
                        continue
                    if key == "global_speed_limit_kbps" and not (0 <= v <= 1000000):
                        continue
                    stored[key] = v
                except (TypeError, ValueError):
                    pass
            else:
                stored[key] = str(val)
        save_stored(stored)

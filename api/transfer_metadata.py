"""Persist transfer metadata keyed by transfer tag."""

from __future__ import annotations

import copy
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from services.json_store import read_json_dict, write_json_atomic

META_PATH = Path(__file__).resolve().parent / "transfer_metadata.json"

_cache: dict[str, dict[str, Any]] | None = None
_lock = threading.RLock()


def load_all() -> dict[str, dict[str, Any]]:
    global _cache
    with _lock:
        if _cache is not None:
            return copy.deepcopy(_cache)
        data = read_json_dict(META_PATH)
        out: dict[str, dict[str, Any]] = {}
        for tag, val in data.items():
            if isinstance(tag, str) and isinstance(val, dict):
                out[tag] = val
        _cache = out
        return copy.deepcopy(out)


def save_all(data: dict[str, dict[str, Any]]) -> None:
    global _cache
    with _lock:
        _cache = copy.deepcopy(data)
        write_json_atomic(META_PATH, data)


def clear_cache() -> None:
    global _cache
    with _lock:
        _cache = None


def get(tag: str) -> dict[str, Any]:
    return load_all().get(tag, {})


def update(tag: str, values: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        data = load_all()
        current = data.get(tag, {})
        current.update(values)
        data[tag] = current
        save_all(data)
        return current


def update_many(tags: list[str], updater: Callable[[str, dict[str, Any]], dict[str, Any] | None]) -> int:
    with _lock:
        data = load_all()
        affected = 0
        for tag in tags:
            current = data.get(tag, {})
            new_val = updater(tag, current)
            if new_val is None:
                continue
            data[tag] = new_val
            affected += 1
        save_all(data)
        return affected

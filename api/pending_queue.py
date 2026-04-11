"""Application-level pending download queue (JSON, single-process)."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.json_store import read_json_dict, write_json_atomic

QUEUE_PATH = Path(__file__).resolve().parent / "pending_queue.json"
_MAX_ITEMS_ENV = "PENDING_QUEUE_MAX_ITEMS"
_DEFAULT_MAX_ITEMS = 200
_JSON_MAX_BYTES = 2 * 1024 * 1024
_LAST_ERROR_MAX = 512
_MAX_TAGS = 50

_lock: Any = None  # asyncio.Lock, set lazily


def _get_lock():
    import asyncio

    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


def max_items() -> int:
    raw = os.environ.get(_MAX_ITEMS_ENV, "").strip()
    if raw:
        try:
            return max(1, min(10_000, int(raw)))
        except ValueError:
            pass
    return _DEFAULT_MAX_ITEMS


def _normalize_tags(raw: list[str] | None) -> list[str]:
    if not raw:
        return []
    if len(raw) > _MAX_TAGS:
        raise ValueError("Too many tags")
    out: list[str] = []
    for t in raw:
        s = str(t).strip()
        if s and s not in out:
            out.append(s)
    return out


def _normalize_priority(p: str | None) -> str:
    pr = (p or "NORMAL").strip().upper()
    if pr not in {"LOW", "NORMAL", "HIGH"}:
        raise ValueError("priority must be LOW, NORMAL or HIGH")
    return pr


def _load_items_unlocked() -> list[dict[str, Any]]:
    data = read_json_dict(QUEUE_PATH)
    items = data.get("items")
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]


def _check_json_size(items: list[dict[str, Any]]) -> None:
    try:
        blob = json.dumps({"items": items}, ensure_ascii=False)
    except (TypeError, ValueError):
        raise ValueError("Queue serialization failed") from None
    if len(blob.encode("utf-8")) > _JSON_MAX_BYTES:
        raise ValueError("Pending queue data too large")


def item_to_api_row(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(d.get("id", "")),
        "url": str(d.get("url", "")),
        "tags": list(d.get("tags", [])) if isinstance(d.get("tags"), list) else [],
        "priority": str(d.get("priority", "NORMAL")).upper(),
        "created_at": str(d.get("created_at", "")),
        "status": str(d.get("status", "PENDING")).upper(),
        "last_error": d.get("last_error"),
    }


async def list_items() -> list[dict[str, Any]]:
    async with _get_lock():
        items = _load_items_unlocked()
    return [item_to_api_row(x) for x in items]


async def add_item(*, url: str, tags: list[str] | None, priority: str | None) -> dict[str, Any]:
    tags_n = _normalize_tags(tags)
    pr = _normalize_priority(priority)
    async with _get_lock():
        items = _load_items_unlocked()
        cap = max_items()
        pending_count = sum(1 for x in items if str(x.get("status", "PENDING")).upper() == "PENDING")
        if pending_count >= cap:
            raise ValueError("Pending queue is full")
        item = {
            "id": str(uuid.uuid4()),
            "url": url,
            "tags": tags_n,
            "priority": pr,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "PENDING",
            "last_error": None,
        }
        items.append(item)
        _check_json_size(items)
        write_json_atomic(QUEUE_PATH, {"items": items})
    return item_to_api_row(item)


async def remove_item(item_id: str) -> bool:
    async with _get_lock():
        items = _load_items_unlocked()
        n0 = len(items)
        items = [x for x in items if str(x.get("id")) != item_id]
        if len(items) == n0:
            return False
        _check_json_size(items)
        write_json_atomic(QUEUE_PATH, {"items": items})
    return True


async def get_item(item_id: str) -> dict[str, Any] | None:
    async with _get_lock():
        for x in _load_items_unlocked():
            if str(x.get("id")) == item_id:
                return dict(x)
    return None


async def set_item_status(
    item_id: str,
    *,
    status: str,
    last_error: str | None = None,
) -> bool:
    async with _get_lock():
        items = _load_items_unlocked()
        found = False
        for x in items:
            if str(x.get("id")) == item_id:
                x["status"] = status
                if last_error is not None:
                    x["last_error"] = last_error[:_LAST_ERROR_MAX] if last_error else None
                else:
                    x["last_error"] = x.get("last_error")
                found = True
                break
        if not found:
            return False
        _check_json_size(items)
        write_json_atomic(QUEUE_PATH, {"items": items})
    return True


async def remove_item_if_exists(item_id: str) -> None:
    await remove_item(item_id)


async def mark_dispatching(item_id: str) -> tuple[dict[str, Any] | None, str]:
    """
    PENDING -> DISPATCHING for a specific id.
    Returns (row_or_none, code): code is ok | not_found | already_dispatching | not_pending.
    """
    async with _get_lock():
        items = _load_items_unlocked()
        for x in items:
            if str(x.get("id")) != item_id:
                continue
            st = str(x.get("status", "")).upper()
            if st == "PENDING":
                x["status"] = "DISPATCHING"
                row = dict(x)
                _check_json_size(items)
                write_json_atomic(QUEUE_PATH, {"items": items})
                return row, "ok"
            if st == "DISPATCHING":
                return dict(x), "already_dispatching"
            return None, "not_pending"
    return None, "not_found"


async def first_pending_id() -> str | None:
    async with _get_lock():
        for x in _load_items_unlocked():
            if str(x.get("status", "")).upper() == "PENDING":
                return str(x.get("id"))
    return None


async def list_pending_ids_in_order() -> list[str]:
    async with _get_lock():
        items = _load_items_unlocked()
    return [str(x.get("id")) for x in items if str(x.get("status", "")).upper() == "PENDING"]

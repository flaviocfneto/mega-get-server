"""Durable pending metadata correlation when MEGAcmd tag resolution is ambiguous (JSON, single-process)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import transfer_metadata as tm
from services.json_store import read_json_dict, write_json_atomic

log = logging.getLogger(__name__)

CORRELATION_PATH = Path(__file__).resolve().parent / "pending_correlation.json"
_MAX_ENTRIES_ENV = "PENDING_CORRELATION_MAX_ENTRIES"
_DEFAULT_MAX_ENTRIES = 200
_JSON_MAX_BYTES = 2 * 1024 * 1024
_TTL_DAYS = 7
_MAX_ATTEMPTS = 20
_MAX_PROCESS_PER_REQUEST = 50

_lock: Any = None


def _get_lock():
    import asyncio

    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


def max_entries() -> int:
    raw = os.environ.get(_MAX_ENTRIES_ENV, "").strip()
    if raw:
        try:
            return max(1, min(10_000, int(raw)))
        except ValueError:
            pass
    return _DEFAULT_MAX_ENTRIES


def _load_entries_unlocked() -> dict[str, dict[str, Any]]:
    data = read_json_dict(CORRELATION_PATH)
    raw = data.get("entries")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, dict):
            out[k] = v
    return out


def _check_json_size(entries: dict[str, dict[str, Any]]) -> None:
    try:
        blob = json.dumps({"entries": entries}, ensure_ascii=False)
    except (TypeError, ValueError):
        raise ValueError("Correlation serialization failed") from None
    if len(blob.encode("utf-8")) > _JSON_MAX_BYTES:
        raise ValueError("Pending correlation data too large")


def _parse_created_at(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _sweep_stale_unlocked(entries: dict[str, dict[str, Any]], *, now: datetime) -> None:
    cutoff = now - timedelta(days=_TTL_DAYS)
    stale_ids: list[str] = []
    for eid, row in entries.items():
        created = _parse_created_at(str(row.get("created_at", "")))
        if created is None:
            stale_ids.append(eid)
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created < cutoff:
            stale_ids.append(eid)
    for eid in stale_ids:
        del entries[eid]
        log.info("pending_correlation: dropped stale entry id=%s", eid)


async def record_after_ambiguous_mega_get(
    pending_id: str,
    url: str,
    labels: list[str],
    priority: str,
    tags_before: set[str],
) -> None:
    """Persist a row when mega-get succeeded but exactly one new tag could not be resolved yet."""
    pr = (priority or "NORMAL").strip().upper()
    if pr not in {"LOW", "NORMAL", "HIGH"}:
        pr = "NORMAL"
    tags_sorted = sorted(tags_before)
    now = datetime.now(timezone.utc)
    async with _get_lock():
        entries = _load_entries_unlocked()
        _sweep_stale_unlocked(entries, now=now)
        cap = max_entries()
        if len(entries) >= cap and pending_id not in entries:
            log.warning(
                "pending_correlation: at capacity (%s), dropping record for pending_id=%s",
                cap,
                pending_id,
            )
            return
        entries[pending_id] = {
            "url": url,
            "tags": list(labels),
            "priority": pr,
            "tags_before": tags_sorted,
            "created_at": now.isoformat(),
            "attempts": 0,
        }
        _check_json_size(entries)
        write_json_atomic(CORRELATION_PATH, {"entries": entries})
    log.info("pending_correlation: recorded pending_id=%s (ambiguous tag)", pending_id)


async def try_attach_from_current_tags(
    current_tags: set[str],
    *,
    max_to_process: int = _MAX_PROCESS_PER_REQUEST,
) -> int:
    """
    For each pending entry, if exactly one new tag appeared vs tags_before, tm.update and remove entry.
    Returns number of successful attachments.
    """
    now = datetime.now(timezone.utc)
    attached = 0
    async with _get_lock():
        entries = _load_entries_unlocked()
        n_before_sweep = len(entries)
        _sweep_stale_unlocked(entries, now=now)
        dirty = n_before_sweep != len(entries)
        if not entries:
            if dirty:
                write_json_atomic(CORRELATION_PATH, {"entries": {}})
            return 0

        examined = 0
        to_delete: list[str] = []
        updates: list[tuple[str, str, str, list[str], str]] = []  # eid, tag, url, labels, pr

        for eid, row in list(entries.items()):
            if examined >= max_to_process:
                break
            examined += 1
            tags_before_raw = row.get("tags_before")
            if not isinstance(tags_before_raw, list):
                to_delete.append(eid)
                continue
            tags_before_set = {str(x) for x in tags_before_raw}
            new_tags = current_tags - tags_before_set
            if len(new_tags) == 1:
                tag = next(iter(new_tags))
                url = str(row.get("url", ""))
                labels = row.get("tags") if isinstance(row.get("tags"), list) else []
                pr = str(row.get("priority", "NORMAL")).upper()
                if pr not in {"LOW", "NORMAL", "HIGH"}:
                    pr = "NORMAL"
                updates.append((eid, tag, url, [str(x) for x in labels], pr))
            else:
                attempts = int(row.get("attempts", 0) or 0) + 1
                row["attempts"] = attempts
                dirty = True
                if attempts > _MAX_ATTEMPTS:
                    to_delete.append(eid)
                    log.info(
                        "pending_correlation: max attempts for pending_id=%s, dropping",
                        eid,
                    )

        for eid in to_delete:
            entries.pop(eid, None)
        if to_delete:
            dirty = True

        for eid, tag, url, labels, pr in updates:
            tm.update(tag, {"url": url, "tags": labels, "priority": pr})
            entries.pop(eid, None)
            attached += 1
            log.info(
                "pending_correlation: attached metadata pending_id=%s tag=%s",
                eid,
                tag,
            )
        if updates:
            dirty = True

        if dirty:
            _check_json_size(entries)
            write_json_atomic(CORRELATION_PATH, {"entries": entries})
    return attached

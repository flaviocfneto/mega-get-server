"""Unit tests for pending_queue helpers and edge cases."""
from __future__ import annotations

import asyncio
import json

import pytest

import pending_queue as pq


@pytest.fixture
def qpath(tmp_path, monkeypatch):
    p = tmp_path / "pending_queue.json"
    p.write_text('{"items": []}', encoding="utf-8")
    monkeypatch.setattr(pq, "QUEUE_PATH", p)
    return p


def test_max_items_from_env(monkeypatch):
    monkeypatch.setenv("PENDING_QUEUE_MAX_ITEMS", "42")
    assert pq.max_items() == 42


def test_max_items_env_invalid_falls_back(monkeypatch):
    monkeypatch.setenv("PENDING_QUEUE_MAX_ITEMS", "not-int")
    assert pq.max_items() == pq._DEFAULT_MAX_ITEMS


def test_max_items_env_clamped(monkeypatch):
    monkeypatch.setenv("PENDING_QUEUE_MAX_ITEMS", "999999")
    assert pq.max_items() == 10_000


def test_normalize_tags_too_many():
    with pytest.raises(ValueError, match="Too many tags"):
        pq._normalize_tags([f"t{i}" for i in range(51)])


def test_normalize_tags_dedupes_and_strips():
    assert pq._normalize_tags([" a ", "a", "b"]) == ["a", "b"]


def test_normalize_priority_invalid():
    with pytest.raises(ValueError, match="priority"):
        pq._normalize_priority("nope")


def test_load_items_malformed_file(qpath):
    qpath.write_text("not json", encoding="utf-8")
    assert pq._load_items_unlocked() == []


def test_load_items_missing_items_key(qpath):
    qpath.write_text("{}", encoding="utf-8")
    assert pq._load_items_unlocked() == []


def test_item_to_api_row_minimal():
    row = pq.item_to_api_row({"id": "x", "url": "u"})
    assert row["id"] == "x"
    assert row["tags"] == []


def test_add_item_then_set_status_and_remove(qpath):
    async def main():
        item = await pq.add_item(url="https://example.com/z", tags=["t"], priority="HIGH")
        iid = item["id"]
        ok = await pq.set_item_status(iid, status="FAILED", last_error="x" * 600)
        assert ok is True
        data = json.loads(qpath.read_text(encoding="utf-8"))
        assert data["items"][0]["status"] == "FAILED"
        assert len(data["items"][0]["last_error"]) <= pq._LAST_ERROR_MAX
        assert await pq.set_item_status("00000000-0000-4000-8000-000000000099", status="PENDING") is False
        assert await pq.remove_item(iid) is True
        assert await pq.remove_item(iid) is False

    asyncio.run(main())


def test_mark_dispatching_paths(qpath):
    async def main():
        a = await pq.add_item(url="https://a.com", tags=None, priority="NORMAL")
        b = await pq.add_item(url="https://b.com", tags=None, priority="NORMAL")
        aid, bid = a["id"], b["id"]
        row, code = await pq.mark_dispatching(aid)
        assert code == "ok"
        assert row["status"] == "DISPATCHING"
        row2, code2 = await pq.mark_dispatching(aid)
        assert code2 == "already_dispatching"
        await pq.set_item_status(bid, status="FAILED", last_error="e")
        row3, code3 = await pq.mark_dispatching(bid)
        assert code3 == "not_pending"
        row4, code4 = await pq.mark_dispatching("00000000-0000-4000-8000-000000000099")
        assert code4 == "not_found"

    asyncio.run(main())


def test_first_pending_and_list_pending_ids(qpath):
    async def main():
        assert await pq.first_pending_id() is None
        assert await pq.list_pending_ids_in_order() == []
        await pq.add_item(url="https://x.com", tags=None, priority="LOW")
        fid = await pq.first_pending_id()
        assert fid
        ids = await pq.list_pending_ids_in_order()
        assert ids == [fid]

    asyncio.run(main())


def test_get_item(qpath):
    async def main():
        it = await pq.add_item(url="https://y.com", tags=None, priority="NORMAL")
        got = await pq.get_item(it["id"])
        assert got and got["url"] == "https://y.com"
        assert await pq.get_item("00000000-0000-4000-8000-000000000099") is None

    asyncio.run(main())


def test_queue_full_raises(qpath, monkeypatch):
    monkeypatch.setenv("PENDING_QUEUE_MAX_ITEMS", "1")

    async def main():
        await pq.add_item(url="https://one.com", tags=None, priority="NORMAL")
        with pytest.raises(ValueError, match="full"):
            await pq.add_item(url="https://two.com", tags=None, priority="NORMAL")

    asyncio.run(main())


def test_remove_item_if_exists(qpath):
    async def main():
        await pq.remove_item_if_exists("00000000-0000-4000-8000-000000000099")

    asyncio.run(main())

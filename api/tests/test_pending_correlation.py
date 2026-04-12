from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

import pending_correlation as pcorr
import transfer_metadata as tm


@pytest.fixture
def isolated_correlation(tmp_path, monkeypatch):
    monkeypatch.setattr(pcorr, "CORRELATION_PATH", tmp_path / "pending_correlation.json")
    monkeypatch.setattr(tm, "META_PATH", tmp_path / "transfer_metadata.json")
    yield


def test_try_attach_single_new_tag_updates_metadata(isolated_correlation):
    async def main():
        await pcorr.record_after_ambiguous_mega_get(
            "pid-1",
            "https://mega.nz/file/abc",
            ["L1"],
            "HIGH",
            {"before-a"},
        )
        n = await pcorr.try_attach_from_current_tags({"before-a", "tag99"})
        assert n == 1
        meta = tm.get("tag99")
        assert meta.get("url") == "https://mega.nz/file/abc"
        assert meta.get("tags") == ["L1"]
        assert meta.get("priority") == "HIGH"

    asyncio.run(main())


def test_try_attach_empty_store(isolated_correlation):
    async def main():
        assert await pcorr.try_attach_from_current_tags({"x"}) == 0

    asyncio.run(main())


def test_ttl_drops_stale_on_attach(isolated_correlation):
    async def main():
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        pcorr.CORRELATION_PATH.write_text(
            json.dumps(
                {
                    "entries": {
                        "stale": {
                            "url": "https://mega.nz/file/z",
                            "tags": [],
                            "priority": "NORMAL",
                            "tags_before": [],
                            "created_at": old,
                            "attempts": 0,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        assert await pcorr.try_attach_from_current_tags({"t1"}) == 0
        data = json.loads(pcorr.CORRELATION_PATH.read_text(encoding="utf-8"))
        assert data.get("entries") == {}

    asyncio.run(main())


def test_max_attempts_drops_entry(isolated_correlation, monkeypatch):
    monkeypatch.setattr(pcorr, "_MAX_ATTEMPTS", 2)

    async def main():
        await pcorr.record_after_ambiguous_mega_get(
            "pid-x",
            "https://mega.nz/file/x",
            [],
            "NORMAL",
            {"a"},
        )
        for _ in range(3):
            await pcorr.try_attach_from_current_tags({"a"})
        data = json.loads(pcorr.CORRELATION_PATH.read_text(encoding="utf-8"))
        assert "pid-x" not in data.get("entries", {})

    asyncio.run(main())


def test_malformed_correlation_file_treated_as_empty(isolated_correlation):
    pcorr.CORRELATION_PATH.write_text("not-json{{{", encoding="utf-8")

    async def main():
        assert await pcorr.try_attach_from_current_tags({"a"}) == 0

    asyncio.run(main())


def test_max_entries_invalid_env_uses_default(monkeypatch):
    monkeypatch.setenv("PENDING_CORRELATION_MAX_ENTRIES", "not-int")
    assert pcorr.max_entries() == pcorr._DEFAULT_MAX_ENTRIES


def test_record_skips_when_at_capacity(isolated_correlation, monkeypatch):
    monkeypatch.setenv("PENDING_CORRELATION_MAX_ENTRIES", "1")

    async def main():
        await pcorr.record_after_ambiguous_mega_get("p1", "https://mega.nz/a", [], "NORMAL", {"a"})
        await pcorr.record_after_ambiguous_mega_get("p2", "https://mega.nz/b", [], "NORMAL", {"b"})

    asyncio.run(main())
    data = json.loads(pcorr.CORRELATION_PATH.read_text(encoding="utf-8"))
    assert len(data.get("entries", {})) == 1


def test_invalid_tags_before_row_removed(isolated_correlation):
    pcorr.CORRELATION_PATH.write_text(
        json.dumps(
            {
                "entries": {
                    "bad": {
                        "url": "https://mega.nz/file/q",
                        "tags": [],
                        "priority": "NORMAL",
                        "tags_before": "not-a-list",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "attempts": 0,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    async def main():
        await pcorr.try_attach_from_current_tags({"a", "b"})
        data = json.loads(pcorr.CORRELATION_PATH.read_text(encoding="utf-8"))
        assert "bad" not in data.get("entries", {})

    asyncio.run(main())

"""Coverage for api_main._transfer_by_tag HTTP vs MEGA paths."""

from __future__ import annotations

import asyncio

import api_main as am
import http_downloads as hd
import mega_service as ms


def test_transfer_by_tag_prefers_http_registry():
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    job = hd.HttpJob(tag=tag, url="https://example.com/a.bin", labels=["x"], priority="HIGH")
    hd._registry[tag] = job
    try:
        row = asyncio.run(am._transfer_by_tag(tag))
        assert row["driver"] == "http"
        assert row["tag"] == tag
    finally:
        hd._registry.pop(tag, None)


def test_transfer_by_tag_from_mega_transfer_list(monkeypatch):
    async def fake_tl():
        return (
            "\n"
            "TRANSFER  STATE     PROGRESS  PATH\n"
            "9         ACTIVE    12%       /data/sample_file.zip\n"
        )

    monkeypatch.setattr(ms, "get_transfer_list", fake_tl)
    row = asyncio.run(am._transfer_by_tag("9"))
    assert row["tag"] == "9"
    assert row.get("driver") == "megacmd"


def test_transfer_by_tag_metadata_fallback_when_not_in_list(monkeypatch):
    async def fake_tl():
        return ""

    monkeypatch.setattr(ms, "get_transfer_list", fake_tl)
    row = asyncio.run(am._transfer_by_tag("missing-tag-xyz"))
    assert row["tag"] == "missing-tag-xyz"
    assert row.get("driver") == "megacmd"

from __future__ import annotations

import asyncio

import pending_queue as pq
import pytest


def test_set_item_status_validates_type_control_chars_and_whitelist(tmp_path, monkeypatch):
    monkeypatch.setattr(pq, "QUEUE_PATH", tmp_path / "pending_queue.json")
    pq.clear_cache()

    async def main():
        item = await pq.add_item(url="http://example.com/test", tags=["test"], priority="NORMAL")
        item_id = item["id"]

        # Valid status updates
        for valid_status in ["COMPLETED", "FAILED", "PAUSED", "ACTIVE", "QUEUED", "RETRYING", "DISPATCHING", "PENDING"]:
            ok = await pq.set_item_status(item_id, status=valid_status)
            assert ok is True

        # Non-string status should raise ValueError
        with pytest.raises(ValueError, match="status must be a string"):
            await pq.set_item_status(item_id, status=12345)  # type: ignore

        # Control character in status should raise ValueError
        with pytest.raises(ValueError, match="Status contains invalid control characters"):
            await pq.set_item_status(item_id, status="ACTIVE\n")

        # Unwhitelisted status should raise ValueError
        with pytest.raises(ValueError, match="Invalid queue item status"):
            await pq.set_item_status(item_id, status="MALICIOUS_STATUS")

    asyncio.run(main())

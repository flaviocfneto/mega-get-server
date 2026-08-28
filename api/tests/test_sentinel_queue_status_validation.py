import pytest
import pending_queue as pq


@pytest.mark.asyncio
async def test_set_item_status_validation():
    item = await pq.add_item(url="https://mega.nz/file/test#key", tags=["test"], priority="NORMAL")
    item_id = item["id"]

    # Test valid status updates
    for valid_status in ["DISPATCHING", "ACTIVE", "QUEUED", "RETRYING", "PAUSED", "COMPLETED", "FAILED"]:
        assert await pq.set_item_status(item_id, status=valid_status) is True
        fetched = await pq.get_item(item_id)
        assert fetched["status"] == valid_status

    # Test invalid status strings raise ValueError
    with pytest.raises(ValueError, match="Invalid queue item status"):
        await pq.set_item_status(item_id, status="INVALID_STATUS")

    # Test status containing ASCII control characters raises ValueError
    with pytest.raises(ValueError, match="Invalid queue item status"):
        await pq.set_item_status(item_id, status="FAILED\nINJECTION")

    # Cleanup
    await pq.remove_item(item_id)

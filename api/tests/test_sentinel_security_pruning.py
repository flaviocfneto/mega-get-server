from __future__ import annotations

import time
from collections import deque

import pytest
import security


@pytest.mark.anyio
async def test_rate_limit_cleans_expired_entries(monkeypatch) -> None:
    # Reset security rate state and cleanup time
    security._rate_state.clear()
    security._rate_windows.clear()
    monkeypatch.setattr(security, "_last_cleanup_time", 0.0)

    now = time.time()

    # Define two dummy endpoints with different window configurations
    @security.rate_limit("short_window_route", limit=10, window_seconds=60)
    async def short_endpoint(request) -> str:
        return "ok"

    # Set up some existing records:
    # 1. Active entry on short_window_route: 127.0.0.1 (recent timestamp)
    security._rate_state["short_window_route:127.0.0.1"] = deque([now])
    security._rate_windows["short_window_route:127.0.0.1"] = 60

    # 2. Long-window endpoint entry on long_window_route: 10.0.0.1 (timestamp from 150 seconds ago).
    # Since its window is 300 seconds, it is STILL active and must NOT be pruned when short_endpoint is called.
    security._rate_state["long_window_route:10.0.0.1"] = deque([now - 150.0])
    security._rate_windows["long_window_route:10.0.0.1"] = 300

    # 3. Truly expired entry on short_window_route: 10.0.0.2 (timestamp from 150 seconds ago).
    # Since its window is 60 seconds, it IS expired and should be pruned.
    security._rate_state["short_window_route:10.0.0.2"] = deque([now - 150.0])
    security._rate_windows["short_window_route:10.0.0.2"] = 60

    # 4. Empty entry on short_window_route: 192.168.1.1 (should be pruned)
    security._rate_state["short_window_route:192.168.1.1"] = deque()
    security._rate_windows["short_window_route:192.168.1.1"] = 60

    # Create a mock request for short_endpoint
    class MockClient:
        def __init__(self) -> None:
            self.host = "127.0.0.1"

    class MockRequest:
        def __init__(self) -> None:
            self.client = MockClient()

    req = MockRequest()

    # Force last cleanup time to be 400 seconds ago so that the periodic cleanup runs
    security._last_cleanup_time = now - 400.0

    # Call the decorated short_endpoint function
    result = await short_endpoint(request=req)
    assert result == "ok"

    # The cleanup should have run during this call!
    # Let's verify the keys:
    # 1. "short_window_route:127.0.0.1" (recent) should still exist
    assert "short_window_route:127.0.0.1" in security._rate_state

    # 2. "long_window_route:10.0.0.1" (from 150 seconds ago, with a 300-second window)
    # MUST still exist! (This prevents the cross-endpoint rate-limit bypass bug!)
    assert "long_window_route:10.0.0.1" in security._rate_state

    # 3. "short_window_route:10.0.0.2" (from 150 seconds ago, with a 60-second window) is expired and should be pruned!
    assert "short_window_route:10.0.0.2" not in security._rate_state

    # 4. "short_window_route:192.168.1.1" (empty deque) should be pruned!
    assert "short_window_route:192.168.1.1" not in security._rate_state

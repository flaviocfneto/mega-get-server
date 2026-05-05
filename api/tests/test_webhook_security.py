from __future__ import annotations

import asyncio

import mega_service as ms
import ui_settings as us
from services.webhook_service import send_webhook_notification


class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_webhook_blocked_private_ip(monkeypatch):
    monkeypatch.setattr(us, "load_stored", lambda: {"webhook_url": "http://127.0.0.1/callback"})
    ms.log_buffer.clear()

    async def run():
        await send_webhook_notification({"test": "data"})

    asyncio.run(run())

    lines = ms.log_buffer.get_lines()
    assert any("Webhook notification blocked" in line for line in lines)


def test_webhook_success(monkeypatch):
    monkeypatch.setattr(us, "load_stored", lambda: {"webhook_url": "http://example.com/callback"})
    ms.log_buffer.clear()

    async def mock_post(*args, **kwargs):
        return MockResponse(200)

    import httpx

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async def run():
        await send_webhook_notification({"test": "data"})

    asyncio.run(run())

    lines = ms.log_buffer.get_lines()
    assert not any("Webhook notification blocked" in line for line in lines)
    assert not any("Webhook notification failed" in line for line in lines)

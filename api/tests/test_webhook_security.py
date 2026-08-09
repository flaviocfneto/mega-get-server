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


def test_webhook_dns_rebinding_blocked(monkeypatch):
    monkeypatch.setattr(us, "load_stored", lambda: {"webhook_url": "http://some-public-webhook-rebind.com/callback"})
    ms.log_buffer.clear()

    import socket

    call_count = 0

    def mock_getaddrinfo(host, port, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call (during _host_is_blocked): return a safe public IP
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 80))]
        else:
            # Subsequent calls (during Transport's resolve): return a blocked IP (DNS Rebinding!)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port or 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    async def run():
        await send_webhook_notification({"test": "data"})

    asyncio.run(run())

    lines = ms.log_buffer.get_lines()
    assert any("Webhook notification failed" in line for line in lines)
    assert any("DNS resolution resolved to a blocked IP" in line or "SSRF validation failed" in line for line in lines)


def test_webhook_dns_pinning_success(monkeypatch):
    monkeypatch.setattr(us, "load_stored", lambda: {"webhook_url": "https://example.com/callback"})
    ms.log_buffer.clear()

    import socket

    def mock_getaddrinfo(host, port, *args, **kwargs):
        # Return a safe public IP
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 443))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    # We mock AsyncHTTPTransport.handle_async_request to verify pinning and SNI
    import httpx

    captured_request = []

    async def mock_handle_async_request(self, request: httpx.Request) -> httpx.Response:
        captured_request.append(request)
        # Return a mock successful response
        return httpx.Response(200, json={"ok": True}, request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", mock_handle_async_request)

    async def run():
        await send_webhook_notification({"test": "data"})

    asyncio.run(run())

    lines = ms.log_buffer.get_lines()
    assert not any("failed" in line.lower() for line in lines)
    assert len(captured_request) == 1
    req = captured_request[0]
    # Check that the host was pinned to the resolved IP
    assert req.url.host == "93.184.216.34"
    # Check that SNI is set to original hostname
    assert req.extensions.get("sni_hostname") == "example.com"

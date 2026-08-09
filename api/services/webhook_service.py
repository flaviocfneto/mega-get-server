from __future__ import annotations

import asyncio
import ipaddress
import socket
from typing import Any

import httpx


class SafeAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    """
    Custom AsyncHTTPTransport that resolves hostnames exactly once, validates
    all resolved IP addresses against the SSRF host blocklist, and pins the request
    to the first safe IP to prevent DNS rebinding SSRF attacks.
    """

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        import http_downloads as hd

        host = request.url.host
        try:
            ipaddress.ip_address(host)
        except ValueError:
            try:
                # Resolve host exactly once
                port = request.url.port or (443 if request.url.scheme == "https" else 80)
                addr_info = await asyncio.to_thread(socket.getaddrinfo, host, port)
                if not addr_info:
                    raise httpx.ConnectError(f"DNS resolution failed for {host}")

                # Check all resolved IPs to prevent SSRF and DNS rebinding
                for item in addr_info:
                    ip_str = item[4][0]
                    if hd._host_is_blocked(ip_str):
                        raise httpx.ConnectError(f"DNS resolution resolved to a blocked IP: {ip_str}")

                # Pin the request target to the first resolved IP
                target_ip = addr_info[0][4][0]
                request.extensions["sni_hostname"] = host
                request.url = request.url.copy_with(host=target_ip)
            except Exception as e:
                raise httpx.ConnectError(f"DNS pinning/SSRF validation failed: {e}") from e
        return await super().handle_async_request(request)


async def send_webhook_notification(payload: dict[str, Any]) -> None:
    """
    Send a POST notification to the configured webhook_url if it's set and valid.
    Implements SSRF protection by re-validating the hostname before sending.
    """
    from urllib.parse import urlparse

    import http_downloads as hd
    import mega_service as ms
    import ui_settings as us

    settings = us.load_stored()
    webhook_url = settings.get("webhook_url", "").strip()
    if not webhook_url:
        return

    try:
        parsed = urlparse(webhook_url)
        host = (parsed.hostname or "").lower()
        if not host or hd._host_is_blocked(host):
            ms.log_buffer.append(f"⚠ Webhook notification blocked: untrusted host in {webhook_url}")
            return
    except Exception as e:
        ms.log_buffer.append(f"⚠ Webhook notification failed: invalid URL {webhook_url} ({e})")
        return

    try:
        transport = SafeAsyncHTTPTransport()
        async with httpx.AsyncClient(transport=transport, timeout=10.0) as client:
            # We don't follow redirects for webhooks to prevent SSRF bypasses via redirects
            # and because most webhooks should be direct.
            resp = await client.post(webhook_url, json=payload, follow_redirects=False)
            if resp.status_code >= 400:
                ms.log_buffer.append(f"⚠ Webhook notification returned status {resp.status_code}")
    except Exception as e:
        ms.log_buffer.append(f"⚠ Webhook notification failed: {e}")


async def notify_download_completed(tag: str, filename: str, size_bytes: int, driver: str) -> None:
    import time

    payload = {
        "event": "download_completed",
        "tag": tag,
        "filename": filename,
        "size_bytes": size_bytes,
        "driver": driver,
        "timestamp": int(time.time()),
    }
    await send_webhook_notification(payload)

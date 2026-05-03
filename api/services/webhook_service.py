from __future__ import annotations

import asyncio
import json
import os
import httpx
from typing import Any

async def send_webhook_notification(payload: dict[str, Any]) -> None:
    """
    Send a POST notification to the configured webhook_url if it's set and valid.
    Implements SSRF protection by re-validating the hostname before sending.
    """
    import ui_settings as us
    import mega_service as ms
    import http_downloads as hd
    from urllib.parse import urlparse

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
        async with httpx.AsyncClient(timeout=10.0) as client:
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
        "timestamp": int(time.time())
    }
    await send_webhook_notification(payload)

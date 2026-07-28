from __future__ import annotations

import os

import pending_queue as pq
import pytest
from api_main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Ensure strict mode for testing tag control character validations
    os.environ["API_AUTH_MODE"] = "strict"
    os.environ["API_WRITE_KEY"] = "test-write-key"
    os.environ["CSRF_ENFORCEMENT_MODE"] = "origin_only"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_pending_queue_rejects_control_characters():
    with pytest.raises(ValueError, match="Tags contain invalid control characters"):
        await pq.add_item(
            url="http://example.com/file.zip",
            tags=["my\ntag"],
            priority="NORMAL",
        )


def test_api_download_rejects_tags_with_control_characters(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # Newline character in tag
    payload_autostart_true = {
        "url": "http://example.com/file1.zip",
        "tags": ["normal-tag", "bad\ntag"],
        "autostart": True,
    }
    resp = client.post("/api/download", json=payload_autostart_true, headers=headers)
    assert resp.status_code == 400
    assert "Tags contain invalid control characters" in resp.json().get("detail", "")

    # Null character in tag, autostart False (queues the item)
    payload_autostart_false = {
        "url": "http://example.com/file2.zip",
        "tags": ["bad\x00tag"],
        "autostart": False,
    }
    resp = client.post("/api/download", json=payload_autostart_false, headers=headers)
    assert resp.status_code == 400
    assert "Tags contain invalid control characters" in resp.json().get("detail", "")


def test_api_queue_add_rejects_tags_with_control_characters(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    payload = {
        "url": "http://example.com/file.zip",
        "tags": ["some-tag", "another\ttag"],
    }
    resp = client.post("/api/queue", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Tags contain invalid control characters" in resp.json().get("detail", "")


def test_api_transfers_bulk_rejects_control_character_labels(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    payload = {
        "tags": ["123"],
        "action": "add_tag",
        "value": "label_with\rcr",
    }
    resp = client.post("/api/transfers/bulk", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Tags contain invalid control characters" in resp.json().get("detail", "")


def test_api_transfer_update_rejects_control_character_tags(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # Use a valid tag format (e.g. 123)
    payload = {
        "tags": ["valid-tag", "tag\x00with-null"],
    }
    resp = client.post("/api/transfers/123/update", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Tags contain invalid control characters" in resp.json().get("detail", "")

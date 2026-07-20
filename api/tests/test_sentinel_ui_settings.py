from __future__ import annotations

import os

import pytest
from api_main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Ensure strict mode for testing config endpoints
    os.environ["API_AUTH_MODE"] = "strict"
    os.environ["API_WRITE_KEY"] = "test-write-key"
    os.environ["CSRF_ENFORCEMENT_MODE"] = "origin_only"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"
    with TestClient(app) as c:
        yield c


def test_watch_folder_path_traversal_blocked(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    # First get current config
    resp = client.get("/api/config", headers=headers)
    assert resp.status_code == 200
    orig_path = resp.json().get("watch_folder_path")

    # Try traversal
    payload = {"watch_folder_path": "/data/../etc"}
    resp = client.post("/api/config", json=payload, headers=headers)
    assert resp.status_code == 200

    # Verify it was NOT applied
    resp = client.get("/api/config", headers=headers)
    assert resp.json().get("watch_folder_path") == orig_path


def test_watch_folder_path_valid_applied(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    payload = {"watch_folder_path": "/data/safe/path"}
    resp = client.post("/api/config", json=payload, headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/config", headers=headers)
    assert resp.json().get("watch_folder_path") == "/data/safe/path"


def test_settings_control_characters_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    # Get current config
    resp = client.get("/api/config", headers=headers)
    assert resp.status_code == 200
    orig_webhook = resp.json().get("webhook_url") or ""
    orig_watch = resp.json().get("watch_folder_path")
    orig_action = resp.json().get("post_download_action") or ""

    # Try payload containing control characters (e.g. newline, tab, null-byte)
    payload = {
        "webhook_url": "http://example.com/callback\n",
        "watch_folder_path": "/data/watch\x00path",
        "post_download_action": "echo\t'hello'",
    }
    resp = client.post("/api/config", json=payload, headers=headers)
    assert resp.status_code == 200

    # Verify they were NOT applied
    resp = client.get("/api/config", headers=headers)
    assert resp.json().get("webhook_url") == orig_webhook
    assert resp.json().get("watch_folder_path") == orig_watch
    assert resp.json().get("post_download_action") == orig_action

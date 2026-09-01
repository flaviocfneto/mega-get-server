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

    # Try various path traversal and relative path payloads
    traversal_payloads = [
        "/data/../etc",
        "/downloads/watch/../../etc/passwd",
        "relative/path/to/watch",
        "watch_folder",
        "../watch",
    ]
    for p in traversal_payloads:
        resp = client.post("/api/config", json={"watch_folder_path": p}, headers=headers)
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


def test_post_download_action_whitelist_enforced(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    resp = client.get("/api/config", headers=headers)
    assert resp.status_code == 200
    orig_action = resp.json().get("post_download_action") or ""

    # Arbitrary strings/commands should be rejected and ignored
    invalid_payloads = [
        "rm -rf /",
        "systemctl reboot",
        "echo pwned",
        "unsupported_action",
    ]
    for act in invalid_payloads:
        resp = client.post("/api/config", json={"post_download_action": act}, headers=headers)
        assert resp.status_code == 200
        resp = client.get("/api/config", headers=headers)
        assert resp.json().get("post_download_action") == orig_action

    # Valid whitelisted actions should be accepted
    for valid_act in ["none", "notify", "extract", "delete", "move", ""]:
        resp = client.post("/api/config", json={"post_download_action": valid_act}, headers=headers)
        assert resp.status_code == 200
        resp = client.get("/api/config", headers=headers)
        assert resp.json().get("post_download_action") == valid_act


def test_schedule_times_and_numeric_bounds_enforced(client):
    import ui_settings as us

    orig_stored = us.load_stored()
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    resp = client.get("/api/config", headers=headers)
    assert resp.status_code == 200
    orig_start = resp.json().get("scheduled_start")
    orig_limit = resp.json().get("history_limit")

    try:
        # Direct merge tests with invalid schedule strings and out-of-bounds ints
        us.merge_post_into_stored(
            {
                "scheduled_start": "25:00",
                "scheduled_stop": "invalid",
                "history_limit": -5,
                "history_retention_days": 1000,
                "max_retries": -1,
                "global_speed_limit_kbps": -500,
            }
        )
        stored = us.load_stored()
        assert stored.get("scheduled_start") == orig_start
        assert stored.get("history_limit") == orig_limit

        # Direct merge tests with valid inputs
        us.merge_post_into_stored(
            {
                "scheduled_start": "08:30",
                "scheduled_stop": "22:15",
                "history_limit": 100,
                "history_retention_days": 14,
                "max_retries": 5,
                "global_speed_limit_kbps": 5000,
            }
        )
        stored = us.load_stored()
        assert stored.get("scheduled_start") == "08:30"
        assert stored.get("scheduled_stop") == "22:15"
        assert stored.get("history_limit") == 100
        assert stored.get("history_retention_days") == 14
        assert stored.get("max_retries") == 5
        assert stored.get("global_speed_limit_kbps") == 5000
    finally:
        us.save_stored(orig_stored)

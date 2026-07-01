from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient
from api_main import app

@pytest.fixture
def client():
    os.environ["API_AUTH_MODE"] = "strict"
    os.environ["API_WRITE_KEY"] = "test-write-key"
    os.environ["CSRF_ENFORCEMENT_MODE"] = "origin_only"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"
    with TestClient(app) as c:
        yield c

def test_config_post_validation_pydantic(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # Test invalid history_limit (too high)
    resp = client.post("/api/config", json={"history_limit": 1001}, headers=headers)
    assert resp.status_code == 422

    # Test invalid max_retries (negative)
    resp = client.post("/api/config", json={"max_retries": -1}, headers=headers)
    assert resp.status_code == 422

    # Test invalid scheduled_start (bad format)
    resp = client.post("/api/config", json={"scheduled_start": "25:00"}, headers=headers)
    assert resp.status_code == 422

    # Test overly long strings
    long_str = "a" * 1025
    resp = client.post("/api/config", json={"webhook_url": long_str}, headers=headers)
    assert resp.status_code == 422

def test_config_post_valid_values(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    payload = {
        "history_limit": 100,
        "max_retries": 5,
        "scheduled_start": "02:30",
        "sound_alerts_enabled": False
    }
    resp = client.post("/api/config", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["history_limit"] == 100
    assert data["max_retries"] == 5
    assert data["scheduled_start"] == "02:30"
    assert data["sound_alerts_enabled"] is False

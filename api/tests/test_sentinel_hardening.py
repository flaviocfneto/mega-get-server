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


def test_transfer_update_oversized_tag_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    long_tag = "a" * 129
    payload = {"tags": [long_tag]}
    resp = client.post("/api/transfers/some-tag/update", json=payload, headers=headers)
    # Pydantic validation error
    assert resp.status_code == 422


def test_transfer_update_oversized_url_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    long_url = "https://example.com/" + "a" * 4100
    payload = {"url": long_url}
    resp = client.post("/api/transfers/some-tag/update", json=payload, headers=headers)
    assert resp.status_code == 422


def test_transfer_update_invalid_priority_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}
    payload = {"priority": "SUPER_HIGH"}
    resp = client.post("/api/transfers/some-tag/update", json=payload, headers=headers)
    # Logic in handler returns 400 for invalid priority strings that pass length check
    assert resp.status_code == 400


def test_transfer_limit_out_of_range_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # Negative
    resp = client.post("/api/transfers/some-tag/limit", json={"speed_limit_kbps": -1}, headers=headers)
    assert resp.status_code == 422

    # Too large
    resp = client.post("/api/transfers/some-tag/limit", json={"speed_limit_kbps": 2000000}, headers=headers)
    assert resp.status_code == 422


def test_bulk_add_tag_length_limit(client, monkeypatch):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # Mock tm.get and tm.update
    import transfer_metadata as tm

    monkeypatch.setattr(tm, "get", lambda tag: {"tags": []})
    updates = []
    monkeypatch.setattr(tm, "update", lambda tag, val: updates.append((tag, val)))

    long_tag = "b" * 200
    payload = {"tags": ["tag1"], "action": "add_tag", "value": long_tag}
    resp = client.post("/api/transfers/bulk", json=payload, headers=headers)
    assert resp.status_code == 200

    # Verify the tag was truncated to 128
    assert len(updates) == 1
    assert updates[0][1]["tags"][0] == "b" * 128

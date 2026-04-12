"""API routes for HTTP driver tags (h-*) and bulk HTTP branches."""
from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import api_main

SAFE_HEADERS = {"origin": "http://localhost:5173"}
HTTP_TAG = "h-550e8400-e29b-41d4-a716-446655440000"


def test_transfer_pause_http_tag_success(monkeypatch):
    monkeypatch.setattr(api_main.hd, "http_pause", AsyncMock(return_value=(True, None)))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/pause", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 200


def test_transfer_pause_http_tag_fails(monkeypatch):
    monkeypatch.setattr(api_main.hd, "http_pause", AsyncMock(return_value=(False, "Not active")))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/pause", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 400
    assert "not active" in r.json()["detail"].lower()


def test_transfer_resume_http_tag_success(monkeypatch):
    monkeypatch.setattr(api_main.hd, "http_resume", AsyncMock(return_value=(True, None)))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/resume", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 200


def test_transfer_resume_http_tag_fails(monkeypatch):
    monkeypatch.setattr(api_main.hd, "http_resume", AsyncMock(return_value=(False, "Not paused")))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/resume", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 400


def test_transfer_retry_http_tag_success(monkeypatch):
    monkeypatch.setattr(api_main.hd, "http_retry", AsyncMock(return_value=(True, None)))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/retry", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 200


def test_transfer_retry_http_tag_fails(monkeypatch):
    monkeypatch.setattr(api_main.hd, "http_retry", AsyncMock(return_value=(False, "bad url")))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/retry", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 400


def test_transfer_cancel_http_tag_fails(monkeypatch):
    monkeypatch.setattr(api_main.hd, "is_http_driver_tag", lambda t: t == HTTP_TAG)
    monkeypatch.setattr(api_main.hd, "http_cancel", AsyncMock(return_value=(False, "missing")))

    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{HTTP_TAG}/cancel", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 400


def test_bulk_http_pause_resume_cancel_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(api_main.tm, "META_PATH", tmp_path / "meta.json")
    monkeypatch.setattr(api_main.hd, "http_pause", AsyncMock(return_value=(True, None)))
    monkeypatch.setattr(api_main.hd, "http_resume", AsyncMock(return_value=(True, None)))
    monkeypatch.setattr(api_main.hd, "http_cancel", AsyncMock(return_value=(True, None)))

    with TestClient(api_main.app) as client:
        r1 = client.post(
            "/api/transfers/bulk",
            json={"tags": [HTTP_TAG], "action": "pause"},
            headers=SAFE_HEADERS,
        )
        r2 = client.post(
            "/api/transfers/bulk",
            json={"tags": [HTTP_TAG], "action": "resume"},
            headers=SAFE_HEADERS,
        )
        r3 = client.post(
            "/api/transfers/bulk",
            json={"tags": [HTTP_TAG], "action": "cancel"},
            headers=SAFE_HEADERS,
        )
        r4 = client.post(
            "/api/transfers/bulk",
            json={"tags": [HTTP_TAG], "action": "set_priority", "value": "LOW"},
            headers=SAFE_HEADERS,
        )
        r5 = client.post(
            "/api/transfers/bulk",
            json={"tags": [HTTP_TAG], "action": "add_tag", "value": "lbl"},
            headers=SAFE_HEADERS,
        )
        r6 = client.post(
            "/api/transfers/bulk",
            json={"tags": [HTTP_TAG], "action": "remove_tag", "value": "lbl"},
            headers=SAFE_HEADERS,
        )
    for r in (r1, r2, r3, r4, r5, r6):
        assert r.status_code == 200, r.text
    assert r4.json()["metadataAffected"] >= 1


def test_cancel_all_calls_http_and_mega(monkeypatch):
    monkeypatch.setattr(api_main.hd, "cancel_all_http_downloads", AsyncMock(return_value=None))
    monkeypatch.setattr(api_main.ms, "run_mega_transfers_cancel_all", AsyncMock(return_value=None))

    with TestClient(api_main.app) as client:
        r = client.post("/api/transfers/cancel-all", json={}, headers=SAFE_HEADERS)
    assert r.status_code == 200

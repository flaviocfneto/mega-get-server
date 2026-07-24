from __future__ import annotations

import os

import pytest
from api_main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Ensure strict mode for testing tag validation
    os.environ["API_AUTH_MODE"] = "strict"
    os.environ["API_WRITE_KEY"] = "test-write-key"
    os.environ["CSRF_ENFORCEMENT_MODE"] = "origin_only"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"
    with TestClient(app) as c:
        yield c


def test_valid_transfer_tags_allowed(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # 1. Valid numeric tag (MEGAcmd style)
    resp = client.post("/api/transfers/12345/pause", headers=headers)
    # Tag validation succeeds; since the transfer is not running in non-simulate, this returns 200 or 400 (not validation 400)
    assert resp.status_code != 400 or "Invalid transfer tag format" not in resp.json().get("detail", "")

    # 2. Valid HTTP tag (h-uuid style)
    resp = client.post("/api/transfers/h-da86358c-b03a-4469-8fc7-e23a4b92b67f/pause", headers=headers)
    # The HTTP tag is validated, but since the transfer is not found, it returns HTTP 400 with "Transfer not found"
    assert resp.status_code == 400
    assert resp.json().get("detail") == "Transfer not found"


def test_invalid_transfer_tags_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    # Invalid tags that do not contain path separators (which would trigger 404 due to path normalization)
    invalid_tags = [
        "-a",  # Command injection flag attempt
        "--help",  # Command injection flag attempt
        "123-abc",  # Invalid mix of characters
        "h-da86358c-b03a-4469-8fc7",  # HTTP tag too short
        "h-da86358c-b03a-4469-8fc7-e23a4b92b67f-extra",  # HTTP tag too long
        "h-da86358c-b03a-4469-8fc7-e23a4b92b67f;rm",  # Semicolon injection without slash
    ]

    for tag in invalid_tags:
        resp = client.post(f"/api/transfers/{tag}/pause", headers=headers)
        assert resp.status_code == 400
        assert "Invalid transfer tag format" in resp.json().get("detail", "")


def test_bulk_invalid_transfer_tags_rejected(client):
    headers = {"X-API-KEY": "test-write-key", "Origin": "http://localhost:5173"}

    invalid_tags = [
        "-a",
        "--help",
        "../../etc/passwd",  # Path traversal inside JSON array
        "123/456",  # Slash inside JSON array
        "123-abc",
        "h-da86358c-b03a-4469-8fc7-e23a4b92b67f;rm -rf /",  # Semicolon injection with slash inside JSON array
    ]

    for tag in invalid_tags:
        payload = {
            "tags": ["123", tag],
            "action": "pause"
        }
        resp = client.post("/api/transfers/bulk", json=payload, headers=headers)
        assert resp.status_code == 400
        assert "Invalid transfer tag format" in resp.json().get("detail", "")

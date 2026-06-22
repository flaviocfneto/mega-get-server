from __future__ import annotations

import os

import pytest
from api_main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    os.environ["API_AUTH_MODE"] = "strict"
    os.environ["API_ADMIN_KEY"] = "test-admin-key"
    os.environ["CSRF_ENFORCEMENT_MODE"] = "origin_only"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"
    with TestClient(app) as c:
        yield c


def test_terminal_restricted_characters(client):
    headers = {"X-API-KEY": "test-admin-key", "Origin": "http://localhost:5173"}

    # Test newline
    payload = {"command": "mega-version\nwhoami"}
    resp = client.post("/api/terminal", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is False
    assert data.get("blocked_reason") == "injection_attempt"

    # Test carriage return
    payload = {"command": "mega-version\rwhoami"}
    resp = client.post("/api/terminal", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is False
    assert data.get("blocked_reason") == "injection_attempt"

    # Test existing restricted char in allowed command
    # Using 'mega-version' and shlex.split will keep 'mega-version;' as one part
    # which will then be blocked because it's not in the allowlist OR because it contains ';'
    payload = {"command": "mega-version;"}
    resp = client.post("/api/terminal", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is False
    # If shlex.split includes it in the first part, it fails allowlist check first.
    # We want to check character hardening which happens after.
    # Let's use a command that IS allowed and has a parameter with restricted char.
    payload = {"command": 'mega-ls ";"'}
    resp = client.post("/api/terminal", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is False
    assert data.get("blocked_reason") == "injection_attempt"

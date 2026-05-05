from __future__ import annotations

import api_main
from fastapi.testclient import TestClient


def test_api_config_get_requires_auth_in_strict_mode(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_WRITE_KEY", "secret-write")
    with TestClient(api_main.app) as client:
        res = client.get("/api/config")
    assert res.status_code == 401


def test_api_config_get_allows_auth_in_strict_mode(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_WRITE_KEY", "secret-write")
    with TestClient(api_main.app) as client:
        res = client.get("/api/config", headers={"x-api-key": "secret-write"})
    assert res.status_code == 200

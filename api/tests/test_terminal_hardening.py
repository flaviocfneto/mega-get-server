from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from api_main import app
import mega_service as ms
import os

client = TestClient(app)

def test_terminal_mega_get_blocked_outside_download_dir(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    response = client.post(
        "/api/terminal",
        json={"command": "mega-get https://mega.nz/file/xyz /etc/passwd"},
        headers={"Origin": "http://testserver"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: local path must be within /data" in data["output"]
    assert data["blocked_reason"] == "path_traversal_attempt"

def test_terminal_mega_get_blocked_sibling_dir(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    response = client.post(
        "/api/terminal",
        json={"command": "mega-get https://mega.nz/file/xyz /data_private/passwords.txt"},
        headers={"Origin": "http://testserver"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Blocked: local path must be within /data" in data["output"]
    assert data["blocked_reason"] == "path_traversal_attempt"

def test_terminal_mega_get_allowed_inside_download_dir(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "mega-get https://mega.nz/file/xyz /data/test.bin"},
        headers={"Origin": "http://testserver"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("blocked_reason") != "path_traversal_attempt"

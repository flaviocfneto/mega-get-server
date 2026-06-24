from __future__ import annotations
import os
import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient
from security import _rate_state

client = TestClient(app)

def test_terminal_cwd_is_download_dir(monkeypatch, tmp_path):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")

    # Set up a temporary download directory
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(download_dir))

    # We'll use 'mega-version' as it's allowed and we can mock its execution to check cwd
    original_run = ms.run_megacmd_command
    captured_cwd = []

    async def mock_run(args, cwd=None):
        captured_cwd.append(cwd)
        return {"ok": True, "stdout": "mocked", "exit_code": 0}

    monkeypatch.setattr(ms, "run_megacmd_command", mock_run)

    response = client.post(
        "/api/terminal",
        json={"command": "mega-version"},
        headers={"Origin": "http://testserver"},
    )

    assert response.status_code == 200
    assert captured_cwd[0] == os.path.abspath(str(download_dir))

def test_terminal_filename_only_restricted(monkeypatch, tmp_path):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")

    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(download_dir))

    # Mock run_megacmd_command to avoid actually running wget2 which might be missing
    async def mock_run(args, cwd=None):
        return {"ok": True, "stdout": "mocked", "exit_code": 0}
    monkeypatch.setattr(ms, "run_megacmd_command", mock_run)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -O myfile.txt http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    # This should be ALLOWED because it's inside DOWNLOAD_DIR
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_terminal_filename_traversal_blocked(monkeypatch, tmp_path):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")

    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(download_dir))

    # This should be BLOCKED
    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -O ../outside.txt http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "Blocked: local path access outside" in response.json()["output"]

from __future__ import annotations

import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_terminal_mega_ls_bypass_repro(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # This should be blocked, but currently it bypasses because it starts with /Root
    response = client.post(
        "/api/terminal", json={"command": "mega-ls /Root/../etc"}, headers={"Origin": "http://testserver"}
    )

    assert response.status_code == 200
    data = response.json()

    # If it's NOT blocked, 'ok' might be True (or False if mega-ls actually fails, but it shouldn't be 'path_traversal_attempt')
    # We WANT it to be blocked.
    if data.get("blocked_reason") == "path_traversal_attempt":
        print("Vulnerability FIXED (unexpected for repro)")
    else:
        print(
            f"Vulnerability CONFIRMED: command was NOT blocked by path_traversal_attempt. Reason: {data.get('blocked_reason')}"
        )

    # In fixed version, we expect it to be blocked by traversal check
    assert data.get("blocked_reason") == "path_traversal_attempt"

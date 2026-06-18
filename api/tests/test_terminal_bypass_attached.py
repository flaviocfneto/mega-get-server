from __future__ import annotations

import api_main
import security
from fastapi.testclient import TestClient

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_terminal_path_traversal_via_attached_flag(monkeypatch):
    security._rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(api_main.app) as client:
        # Try to bypass via attached flag
        res = client.post(
            "/api/terminal",
            json={"command": "wget2 -O/etc/passwd https://google.com"},
            headers=SAFE_HEADERS,
        )
        # We WANT this to be False. If it's True, the vulnerability exists.
        assert res.json()["ok"] is False, (
            f"VULNERABILITY CONFIRMED: wget2 -O/etc/passwd bypassed path traversal check! Response: {res.json()}"
        )


def test_terminal_path_traversal_via_another_attached_flag(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    with TestClient(api_main.app) as client:
        res = client.post(
            "/api/terminal",
            json={"command": "wget2 --output-document=/etc/passwd https://google.com"},
            headers=SAFE_HEADERS,
        )
        # This one is ALREADY caught because it splits at '='
        assert res.json()["ok"] is False, "wget2 --output-document=/etc/passwd should be blocked."


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-s"]))

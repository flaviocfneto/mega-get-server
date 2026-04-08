"""FastAPI smoke tests for diagnostics and core endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api_main


def test_diag_tools_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_main.td,
        "collect_tool_diagnostics",
        lambda: {
            "ok": False,
            "missing_tools": ["megacmd"],
            "tools": [
                {
                    "name": "megacmd",
                    "available": False,
                    "install_instructions": "Install MEGAcmd.",
                    "suggested_install_commands": ["brew install --cask megacmd"],
                }
            ],
        },
    )
    with TestClient(api_main.app) as client:
        res = client.get("/api/diag/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is False
    assert "megacmd" in data["missing_tools"]
    assert data["tools"][0]["install_instructions"]


def test_core_smoke_endpoints(monkeypatch):
    async def fake_ready():
        return True

    async def fake_transfer_list():
        return "1 ACTIVE 12% /data/sample.zip"

    monkeypatch.setattr(api_main.ms, "ensure_mega_cmd_server_running", fake_ready)
    monkeypatch.setattr(api_main.ms, "get_transfer_list", fake_transfer_list)

    with TestClient(api_main.app) as client:
        cfg = client.get("/api/config")
        logs = client.get("/api/logs")
        transfers = client.get("/api/transfers")
        tools = client.get("/api/diag/tools")

    assert cfg.status_code == 200
    assert logs.status_code == 200
    assert transfers.status_code == 200
    assert isinstance(transfers.json(), list)
    assert tools.status_code == 200


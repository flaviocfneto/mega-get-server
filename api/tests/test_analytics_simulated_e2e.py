"""
End-to-end simulated MEGAcmd output: multi-poll sequences through GET /api/analytics
without real mega-transfers. Validates parse + disappearance completion together.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

import api_main
import mega_service as ms


def _reset_analytics_globals() -> None:
    api_main._last_states.clear()
    api_main._last_row_snapshot.clear()
    api_main._analytics_completed = 0
    api_main._analytics_failed = 0


def _client_with_fake_megacmd(monkeypatch, frames: list[str]) -> TestClient:
    """Each async get_transfer_list() returns the next frame, then empty."""

    async def fake_ready():
        return True

    idx = [0]

    async def fake_get_transfer_list():
        i = idx[0]
        idx[0] += 1
        if i < len(frames):
            return frames[i]
        return ""

    monkeypatch.setattr(api_main.ms, "ensure_mega_cmd_server_running", fake_ready)
    monkeypatch.setattr(api_main.ms, "get_transfer_list", fake_get_transfer_list)
    return TestClient(api_main.app)


def test_simulated_ascii_arrow_active_then_vanish_increments_completed(monkeypatch):
    """MEGAcmd-style line with ASCII arrow; empty list next poll → inferred completion."""
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    frames = [
        "v    99  /data/document.pdf  45.0%  of  10 MB  ACTIVE\n",
        "",
    ]
    client = _client_with_fake_megacmd(monkeypatch, frames)

    r1 = client.get("/api/analytics")
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["active_count"] == 1
    assert b1["total_transfers_completed"] == 0

    r2 = client.get("/api/analytics")
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["active_count"] == 0
    assert b2["total_transfers_completed"] >= 1
    assert api_main._analytics_completed >= 1


def test_simulated_unicode_arrow_then_explicit_completed(monkeypatch):
    """Two polls: active transfer, then COMPLETED still listed (no disappearance)."""
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    frames = [
        "⇓    7  /Downloads/a.zip  80.0%  of  2 GB  ACTIVE\n",
        "⇓    7  /Downloads/a.zip  100.0%  of  2 GB  COMPLETED\n",
    ]
    client = _client_with_fake_megacmd(monkeypatch, frames)

    client.get("/api/analytics")
    r2 = client.get("/api/analytics")
    assert r2.status_code == 200
    assert r2.json()["total_transfers_completed"] >= 1


def test_simulated_parse_produces_nonzero_downloaded_bytes(monkeypatch):
    """Parsed size + progress flows into total_downloaded_bytes on /api/analytics."""
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    raw = "⇓    1  /x/f.bin  50.0%  of  100 MB  ACTIVE\n"
    assert len(ms.parse_transfer_list(raw)) == 1

    client = _client_with_fake_megacmd(monkeypatch, [raw])
    r = client.get("/api/analytics")
    assert r.status_code == 200
    assert r.json()["total_downloaded_bytes"] > 0


def test_simulated_table_style_download_keyword(monkeypatch):
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    frames = [
        "DOWNLOAD 3 ACTIVE 10% /tmp/file.dat\n",
        "",
    ]
    client = _client_with_fake_megacmd(monkeypatch, frames)

    r1 = client.get("/api/analytics")
    assert r1.json()["active_count"] == 1

    r2 = client.get("/api/analytics")
    assert r2.json()["total_transfers_completed"] >= 1

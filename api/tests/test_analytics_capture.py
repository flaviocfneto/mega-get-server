"""Analytics aggregation: disappearance inference and parse debug API."""

from __future__ import annotations

from fastapi.testclient import TestClient

import api_main


def _reset_analytics_globals() -> None:
    api_main._last_states.clear()
    api_main._last_row_snapshot.clear()
    api_main._analytics_completed = 0
    api_main._analytics_failed = 0
    api_main._daily_loaded = True
    api_main._daily_buckets = {}


def test_disappearance_infers_completion(monkeypatch):
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    row = {
        "tag": "42",
        "state": "ACTIVE",
        "downloaded_bytes": 50,
        "size_bytes": 500,
        "speed_bps": 1000,
    }
    r1 = api_main._update_analytics_from_rows([row])
    assert r1["active_count"] == 1
    assert api_main._last_states.get("42") == "ACTIVE"

    r2 = api_main._update_analytics_from_rows([])
    assert api_main._analytics_completed == 1
    assert r2["total_transfers_completed"] >= 1
    assert "42" not in api_main._last_states


def test_completed_row_then_vanish_counts_once(monkeypatch):
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    done = {
        "tag": "1",
        "state": "COMPLETED",
        "downloaded_bytes": 100,
        "size_bytes": 100,
        "speed_bps": 0,
    }
    api_main._update_analytics_from_rows([done])
    assert api_main._analytics_completed == 1
    api_main._update_analytics_from_rows([])
    assert api_main._analytics_completed == 1


def test_disappearance_after_failed_does_not_count_completed(monkeypatch):
    monkeypatch.setattr(api_main, "_bump_daily_on_completed", lambda _b: None)
    _reset_analytics_globals()

    row = {
        "tag": "9",
        "state": "FAILED",
        "downloaded_bytes": 0,
        "size_bytes": 0,
        "speed_bps": 0,
    }
    api_main._update_analytics_from_rows([row])
    api_main._update_analytics_from_rows([])
    assert api_main._analytics_completed == 0


def test_get_analytics_parse_debug_when_env(monkeypatch):
    monkeypatch.setenv("MEGA_ANALYTICS_PARSE_DEBUG", "1")

    async def fake_tl():
        return "1 ACTIVE 10% /x/sample.zip"

    async def fake_ready():
        return True

    monkeypatch.setattr(api_main.ms, "ensure_mega_cmd_server_running", fake_ready)
    monkeypatch.setattr(api_main.ms, "get_transfer_list", fake_tl)

    with TestClient(api_main.app) as client:
        res = client.get("/api/analytics")
    assert res.status_code == 200
    body = res.json()
    assert "parse_debug" in body
    assert body["parse_debug"]["parsed_count"] >= 1
    assert body["parse_debug"]["nonempty_line_count"] >= 1


def test_total_downloaded_persists_after_disappearance(monkeypatch):
    monkeypatch.setattr(api_main, "_persist_daily_buckets", lambda: None)
    _reset_analytics_globals()

    row = {
        "tag": "11",
        "state": "ACTIVE",
        "downloaded_bytes": 500,
        "size_bytes": 1000,
        "speed_bps": 100,
    }
    r1 = api_main._update_analytics_from_rows([row])
    assert r1["total_downloaded_bytes"] == 500

    r2 = api_main._update_analytics_from_rows([])
    assert r2["total_downloaded_bytes"] == 1000
    assert api_main._daily_buckets is not None
    today = next(iter(api_main._daily_buckets.values()))
    assert today["bytes"] == 1000

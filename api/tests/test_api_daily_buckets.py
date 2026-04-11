from __future__ import annotations

import json

import api_main


def test_daily_load_from_file_and_totals(tmp_path, monkeypatch):
    p = tmp_path / ".mega-analytics-daily.json"
    p.write_text(json.dumps({"2026-01-01": {"bytes": 123, "count": 2}}), encoding="utf-8")
    monkeypatch.setattr(api_main, "DAILY_ANALYTICS_PATH", p)
    api_main._daily_loaded = False
    api_main._daily_buckets = None

    api_main._ensure_daily_loaded()
    assert api_main._daily_buckets is not None
    assert api_main._total_persisted_downloaded_bytes() == 123


def test_daily_load_invalid_file_falls_back_empty(tmp_path, monkeypatch):
    p = tmp_path / ".mega-analytics-daily.json"
    p.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(api_main, "DAILY_ANALYTICS_PATH", p)
    api_main._daily_loaded = False
    api_main._daily_buckets = None
    api_main._ensure_daily_loaded()
    assert api_main._daily_buckets == {}


def test_bump_daily_and_stats_last_7_days(tmp_path, monkeypatch):
    p = tmp_path / ".mega-analytics-daily.json"
    monkeypatch.setattr(api_main, "DAILY_ANALYTICS_PATH", p)
    api_main._daily_loaded = True
    api_main._daily_buckets = {}
    api_main._bump_daily_on_completed(500)
    stats = api_main._daily_stats_last_7_days()
    assert len(stats) == 7
    assert any(day["bytes"] >= 500 for day in stats)

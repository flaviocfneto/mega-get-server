from __future__ import annotations

import os
import stat
from pathlib import Path

import mega_service
from services.json_store import write_json_atomic


def test_json_store_writes_with_strict_permissions(tmp_path: Path) -> None:
    test_file = tmp_path / "test_store.json"
    data = {"key": "value"}
    write_json_atomic(test_file, data)

    assert test_file.exists()
    # Check that file permissions are 0o600 on UNIX-like platforms
    if os.name == "posix":
        mode = test_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_save_history_writes_with_strict_permissions(tmp_path: Path, monkeypatch) -> None:
    history_file = tmp_path / "test_history.json"
    monkeypatch.setattr(mega_service, "_url_history", ["https://mega.nz/file/1", "https://mega.nz/file/2"])
    monkeypatch.setattr(mega_service, "_history_file_path", str(history_file))

    mega_service.save_history()

    assert history_file.exists()
    if os.name == "posix":
        mode = history_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_daily_analytics_writes_with_strict_permissions(tmp_path: Path, monkeypatch) -> None:
    import api_main

    analytics_file = tmp_path / "test_analytics.json"
    monkeypatch.setattr(api_main, "DAILY_ANALYTICS_PATH", analytics_file)
    monkeypatch.setattr(api_main, "_daily_loaded", True)
    monkeypatch.setattr(api_main, "_daily_buckets", {"2026-08-03": {"bytes": 100, "count": 1}})

    api_main._persist_daily_buckets()

    assert analytics_file.exists()
    if os.name == "posix":
        mode = analytics_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from cryptography.fernet import Fernet

import crypt_utils
import mega_service
import pending_queue
import ui_settings


def test_crypt_utils_existing_files_hardening(tmp_path: Path, monkeypatch) -> None:
    if os.name != "posix":
        return

    key_file = tmp_path / "test_existing_key.key"
    bin_file = tmp_path / "test_existing_bin.bin"
    monkeypatch.setattr(crypt_utils, "SECRET_KEY_PATH", str(key_file))
    monkeypatch.setattr(crypt_utils, "SECRETS_BIN_PATH", str(bin_file))

    # Pre-create files with permissive 0o644 permissions and a valid key
    valid_key = Fernet.generate_key()
    key_file.write_bytes(valid_key)
    os.chmod(key_file, 0o644)
    assert stat.S_IMODE(key_file.stat().st_mode) == 0o644

    # Trigger load_key and verify correction
    crypt_utils.load_key()
    assert stat.S_IMODE(key_file.stat().st_mode) == 0o600

    # Test load_vault
    bin_file.write_bytes(b"encrypted_data_stub")
    os.chmod(bin_file, 0o644)
    assert stat.S_IMODE(bin_file.stat().st_mode) == 0o644

    crypt_utils.load_vault()
    assert stat.S_IMODE(bin_file.stat().st_mode) == 0o600


def test_history_existing_file_hardening(tmp_path: Path, monkeypatch) -> None:
    if os.name != "posix":
        return

    history_file = tmp_path / "test_existing_history.json"
    monkeypatch.setattr(mega_service, "_url_history", [])
    monkeypatch.setattr(mega_service, "_history_file_path", str(history_file))

    history_file.write_text("[]", encoding="utf-8")
    os.chmod(history_file, 0o644)
    assert stat.S_IMODE(history_file.stat().st_mode) == 0o644

    mega_service.load_history()
    assert stat.S_IMODE(history_file.stat().st_mode) == 0o600


def test_pending_queue_existing_file_hardening(tmp_path: Path, monkeypatch) -> None:
    if os.name != "posix":
        return

    queue_file = tmp_path / "test_existing_queue.json"
    monkeypatch.setattr(pending_queue, "QUEUE_PATH", queue_file)

    queue_file.write_text('{"items": []}', encoding="utf-8")
    os.chmod(queue_file, 0o644)
    assert stat.S_IMODE(queue_file.stat().st_mode) == 0o644

    pending_queue._load_items_unlocked()
    assert stat.S_IMODE(queue_file.stat().st_mode) == 0o600


def test_ui_settings_existing_file_hardening(tmp_path: Path, monkeypatch) -> None:
    if os.name != "posix":
        return

    settings_file = tmp_path / "test_existing_settings.json"
    monkeypatch.setattr(ui_settings, "SETTINGS_PATH", settings_file)
    monkeypatch.setattr(ui_settings, "_cache", None)

    settings_file.write_text("{}", encoding="utf-8")
    os.chmod(settings_file, 0o644)
    assert stat.S_IMODE(settings_file.stat().st_mode) == 0o644

    ui_settings.load_stored()
    assert stat.S_IMODE(settings_file.stat().st_mode) == 0o600


def test_daily_analytics_existing_file_hardening(tmp_path: Path, monkeypatch) -> None:
    if os.name != "posix":
        return

    import api_main

    analytics_file = tmp_path / "test_existing_analytics.json"
    monkeypatch.setattr(api_main, "DAILY_ANALYTICS_PATH", analytics_file)
    monkeypatch.setattr(api_main, "_daily_loaded", False)
    monkeypatch.setattr(api_main, "_daily_buckets", None)

    analytics_file.write_text("{}", encoding="utf-8")
    os.chmod(analytics_file, 0o644)
    assert stat.S_IMODE(analytics_file.stat().st_mode) == 0o644

    api_main._ensure_daily_loaded()
    assert stat.S_IMODE(analytics_file.stat().st_mode) == 0o600

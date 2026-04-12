from __future__ import annotations

import json

import transfer_metadata as tm
import ui_settings as us


def test_transfer_metadata_update_and_get(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "META_PATH", tmp_path / "transfer_metadata.json")

    before = tm.get("42")
    assert before == {}

    updated = tm.update("42", {"priority": "HIGH", "tags": ["movie"]})
    assert updated["priority"] == "HIGH"
    assert updated["tags"] == ["movie"]
    assert tm.get("42")["priority"] == "HIGH"


def test_transfer_metadata_update_many_counts_only_updates(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "META_PATH", tmp_path / "transfer_metadata.json")
    tm.update("1", {"priority": "LOW"})
    tm.update("2", {"priority": "NORMAL"})

    affected = tm.update_many(
        ["1", "2", "3"],
        lambda tag, current: None if tag == "3" else {**current, "tagged": True},
    )
    assert affected == 2
    assert tm.get("1")["tagged"] is True
    assert tm.get("2")["tagged"] is True
    assert tm.get("3") == {}


def test_transfer_metadata_load_all_invalid_json_returns_empty(tmp_path, monkeypatch):
    p = tmp_path / "transfer_metadata.json"
    p.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(tm, "META_PATH", p)
    assert tm.load_all() == {}


def test_ui_settings_merge_post_applies_types(tmp_path, monkeypatch):
    settings_path = tmp_path / "ui_settings.json"
    monkeypatch.setattr(us, "SETTINGS_PATH", settings_path)

    us.merge_post_into_stored(
        {
            "history_limit": "25",
            "sound_alerts_enabled": 0,
            "watch_folder_path": "/mnt/watch",
            "unknown_key": "ignored",
            "history_retention_days": None,
        }
    )
    stored = us.load_stored()

    assert stored["history_limit"] == 25
    assert stored["sound_alerts_enabled"] is False
    assert stored["watch_folder_path"] == "/mnt/watch"
    assert "unknown_key" not in stored
    assert "history_retention_days" not in stored


def test_ui_settings_merge_invalid_int_is_skipped(tmp_path, monkeypatch):
    settings_path = tmp_path / "ui_settings.json"
    monkeypatch.setattr(us, "SETTINGS_PATH", settings_path)
    us.merge_post_into_stored({"history_limit": "not-a-number"})
    assert us.load_stored().get("history_limit") is None


def test_ui_settings_load_invalid_shape_returns_empty(tmp_path, monkeypatch):
    settings_path = tmp_path / "ui_settings.json"
    settings_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    monkeypatch.setattr(us, "SETTINGS_PATH", settings_path)
    assert us.load_stored() == {}

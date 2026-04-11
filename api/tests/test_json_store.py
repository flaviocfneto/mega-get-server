from __future__ import annotations

import json
from pathlib import Path

from services.json_store import read_json_dict, write_json_atomic


def test_write_json_atomic_and_read_roundtrip(tmp_path: Path):
    p = tmp_path / "state.json"
    payload = {"a": 1, "b": {"x": True}}
    write_json_atomic(p, payload)
    assert p.is_file()
    assert read_json_dict(p) == payload


def test_read_json_dict_handles_invalid_json(tmp_path: Path):
    p = tmp_path / "broken.json"
    p.write_text("{invalid", encoding="utf-8")
    assert read_json_dict(p) == {}


def test_write_json_atomic_replaces_existing_file(tmp_path: Path):
    p = tmp_path / "replace.json"
    p.write_text(json.dumps({"old": 1}), encoding="utf-8")
    write_json_atomic(p, {"new": 2})
    assert read_json_dict(p) == {"new": 2}

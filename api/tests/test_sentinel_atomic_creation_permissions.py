from __future__ import annotations

import os
import stat
from pathlib import Path

import crypt_utils
import mega_service
from services.json_store import write_json_atomic


def test_atomic_file_creation_json_store(tmp_path: Path) -> None:
    test_file = tmp_path / "atomic_store.json"
    data = {"hello": "world"}
    write_json_atomic(test_file, data)

    assert test_file.exists()
    if os.name == "posix":
        mode = test_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_atomic_file_creation_history(tmp_path: Path, monkeypatch) -> None:
    history_file = tmp_path / "atomic_history.json"
    monkeypatch.setattr(mega_service, "_url_history", ["https://mega.nz/file/1"])
    monkeypatch.setattr(mega_service, "_history_file_path", str(history_file))

    mega_service.save_history()

    assert history_file.exists()
    if os.name == "posix":
        mode = history_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_atomic_file_creation_crypt_utils(tmp_path: Path, monkeypatch) -> None:
    key_file = tmp_path / "atomic_key.key"
    bin_file = tmp_path / "atomic_bin.bin"
    monkeypatch.setattr(crypt_utils, "SECRET_KEY_PATH", str(key_file))
    monkeypatch.setattr(crypt_utils, "SECRETS_BIN_PATH", str(bin_file))
    monkeypatch.setattr(crypt_utils, "DEFAULT_DATA_DIR", str(tmp_path))

    # Generate key
    key = crypt_utils.generate_key()
    assert key is not None
    assert key_file.exists()
    if os.name == "posix":
        assert stat.S_IMODE(key_file.stat().st_mode) == 0o600

    # Save vault
    crypt_utils.save_vault({"secret_key": "secret_val"})
    assert bin_file.exists()
    if os.name == "posix":
        assert stat.S_IMODE(bin_file.stat().st_mode) == 0o600

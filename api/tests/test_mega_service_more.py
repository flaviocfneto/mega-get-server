from __future__ import annotations

import asyncio

import mega_service as ms


def test_infer_account_type_from_text():
    assert ms._infer_account_type_from_text("pro lite account") == "PRO"
    assert ms._infer_account_type_from_text("business user") == "BUSINESS"
    assert ms._infer_account_type_from_text("free tier") == "UNKNOWN"
    assert ms._infer_account_type_from_text("unknown output") == "UNKNOWN"


def test_parse_mega_df_invalid_payload():
    su, st, bu, bl, ok = ms._parse_mega_df_bytes_and_bw("nonsense")
    assert (su, st, bu, bl) == (0, 0, 0, 0)
    assert ok is False


def test_is_web_server_mode_force_flag(monkeypatch):
    monkeypatch.setenv("FLET_FORCE_WEB_SERVER", "1")
    assert ms.is_web_server_mode() is True


def test_get_transfer_list_simulate(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", True)
    out = asyncio.run(ms.get_transfer_list())
    assert "TRANSFER" in out


def test_get_transfer_list_ui_test_mode(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "UI_TEST_MODE", True)
    out = asyncio.run(ms.get_transfer_list())
    assert "ACTIVE" in out


def test_get_account_info_simulated(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", True)
    info = asyncio.run(ms.get_account_info())
    assert info["is_logged_in"] is True
    assert info["account_type"] == "FREE"


def test_get_account_info_logged_out(monkeypatch):
    async def fake_cmd(_args):
        return {"ok": False, "stdout": "", "stderr": "", "output": ""}

    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "run_megacmd_command", fake_cmd)
    info = asyncio.run(ms.get_account_info())
    assert info["is_logged_in"] is False
    assert info["details_partial"] is True


def test_wait_for_mega_server_ready_success(monkeypatch):
    class _Proc:
        returncode = 0

        async def wait(self):
            return 0

    async def fake_exec(*args, **kwargs):
        return _Proc()

    async def fake_wait_for(coro, timeout):
        return await coro

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(ms.asyncio, "wait_for", fake_wait_for)
    assert asyncio.run(ms.wait_for_mega_server_ready(max_wait_sec=0.2)) is True


def test_get_transfer_list_uses_stderr_when_stdout_empty(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "UI_TEST_MODE", False)

    class _Proc:
        returncode = 0

        async def communicate(self):
            return (b"", b"stderr-only-line\n")

    async def fake_exec(*args, **kwargs):
        return _Proc()

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    out = asyncio.run(ms.get_transfer_list())
    assert "stderr-only" in out


def test_get_transfer_list_merges_stderr_when_stdout_present(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    monkeypatch.setattr(ms, "UI_TEST_MODE", False)

    class _Proc:
        returncode = 0

        async def communicate(self):
            return (b"out-line\n", b"err-line\n")

    async def fake_exec(*args, **kwargs):
        return _Proc()

    monkeypatch.setattr(ms.asyncio, "create_subprocess_exec", fake_exec)
    out = asyncio.run(ms.get_transfer_list())
    assert "out-line" in out
    assert "err-line" in out


def test_parse_transfer_list_relaxed_progress_line():
    raw = "v 10 /some/nested/file.zip 45.2% ACTIVE\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "10"
    assert rows[0]["state"] == "ACTIVE"


def test_parse_transfer_list_download_keyword_row():
    raw = "DOWNLOAD 11 ACTIVE 12% /data/archive.tgz\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "11"
    assert rows[0]["progress_pct"] == 12.0


def test_normalize_transfer_state_maps_aliases():
    assert ms.normalize_transfer_state("FINISHED") == "COMPLETED"
    assert ms.normalize_transfer_state("CANCELED") == "FAILED"


def test_size_display_to_bytes_parses_units():
    assert ms.size_display_to_bytes("1.5 GB") > 1_000_000_000
    assert ms.size_display_to_bytes("512 KB") == 512 * 1024


def test_parse_mega_df_transfer_quota_fallback_line():
    text = "Transfer quota: 10 bytes of 20 bytes\n"
    _su, _st, bu, bl, _sc = ms._parse_mega_df_bytes_and_bw(text)
    assert (bu, bl) == (10, 20)


def test_parse_transfer_list_real_megacmd_style_line():
    raw = "\u21d3    1234  /Downloads/ubuntu-22.04.iso  45.2% of  3.54 GB ACTIVE\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "1234"
    assert rows[0]["size_display"] == "3.54 GB"


def test_parsed_transfer_to_api_row_merges_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(ms.tm, "META_PATH", tmp_path / "transfer_metadata.json")
    ms.tm.update(
        "77",
        {"url": "https://mega.nz/x", "priority": "low", "tags": "not-list", "speed_limit_kbps": 128},
    )
    row = ms.parsed_transfer_to_api_row(
        {
            "tag": "77",
            "size_display": "Unknown",
            "progress_pct": 0,
            "state": "QUEUED",
            "path": "/p",
            "filename": "f.bin",
        }
    )
    assert row["url"] == "https://mega.nz/x"
    assert row["priority"] == "LOW"
    assert row["speed_limit_kbps"] == 128
    assert row["tags"] == []

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

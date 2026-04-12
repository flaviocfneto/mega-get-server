"""Extra mega_service.get_account_info coverage (non-simulate paths, mocked MEGAcmd)."""
from __future__ import annotations

import asyncio

import mega_service as ms


def test_get_account_info_not_logged_in(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)

    async def fake_whoami(_args):
        return {"ok": False, "stdout": "", "stderr": "not logged in", "output": "not logged in"}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_whoami)

    async def main():
        return await ms.get_account_info()

    info = asyncio.run(main())
    assert info["is_logged_in"] is False
    assert info["account_type"] == "UNKNOWN"


def test_get_account_info_with_email_and_df(monkeypatch):
    monkeypatch.setattr(ms, "SIMULATE", False)
    calls: list[list[str]] = []

    async def fake_cmd(args):
        calls.append(list(args))
        if args[:1] == ["mega-whoami"]:
            return {"ok": True, "stdout": "email: user@example.com\n", "stderr": "", "output": ""}
        if args[:1] == ["mega-df"]:
            return {
                "ok": True,
                "stdout": "Storage: 1 GB of 20 GB\nTransfer: 0 B of 50 GB\n",
                "stderr": "",
                "output": "",
            }
        return {"ok": False, "stdout": "", "stderr": "", "output": ""}

    monkeypatch.setattr(ms, "run_megacmd_command", fake_cmd)

    info = asyncio.run(ms.get_account_info())
    assert info["is_logged_in"] is True
    assert info["email"] == "user@example.com"
    assert len(calls) >= 2

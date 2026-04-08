"""Tool diagnostics smoke tests."""

from __future__ import annotations

import tool_diagnostics as td


def test_collect_tool_diagnostics_missing_megacmd(monkeypatch):
    real_which = td.shutil.which

    def fake_which(name: str, path: str | None = None):
        if name == "mega-version":
            return None
        return real_which(name, path=path)

    monkeypatch.setattr(td.shutil, "which", fake_which)
    payload = td.collect_tool_diagnostics()

    assert "tools" in payload
    assert isinstance(payload["tools"], list)
    megacmd = next(t for t in payload["tools"] if t["name"] == "megacmd")
    assert megacmd["available"] is False
    assert megacmd["install_instructions"]
    assert megacmd["suggested_install_commands"]


def test_collect_tool_diagnostics_schema():
    payload = td.collect_tool_diagnostics()
    assert "ok" in payload
    assert "missing_tools" in payload
    assert "tools" in payload
    assert isinstance(payload["tools"], list)
    assert all("name" in tool and "available" in tool for tool in payload["tools"])


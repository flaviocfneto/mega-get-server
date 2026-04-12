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


def test_run_version_command_swallows_subprocess_errors(monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("no")

    monkeypatch.setattr(td.subprocess, "run", boom)
    assert td._run_version_command(["x"]) == ""


def test_wget2_diagnostic_uses_absolute_wget_http_bin(tmp_path, monkeypatch):
    exe = tmp_path / "wget2"
    exe.write_text("#!/bin/sh\necho wget2 2.0\n")
    exe.chmod(0o755)
    monkeypatch.setenv("WGET_HTTP_BIN", str(exe))
    monkeypatch.setattr(td.shutil, "which", lambda *a, **k: None)
    diag = td._wget2_diagnostic()
    assert diag["available"] is True
    assert "wget2" in (diag.get("detected_version") or "").lower() or diag["details"].get("resolved_path")


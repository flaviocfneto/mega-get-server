"""External tool diagnostics and user-facing install guidance."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from typing import Any

import mega_service as ms


def _run_version_command(cmd: list[str], *, env: dict[str, str] | None = None) -> str:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3,
            env=env or os.environ.copy(),
            check=False,
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        return out or err
    except Exception:
        return ""


def _megacmd_diagnostic() -> dict[str, Any]:
    env = ms.subprocess_env()
    version_cmd = shutil.which("mega-version", path=env.get("PATH", ""))
    available = bool(version_cmd)
    detected_version = _run_version_command(["mega-version"], env=env) if available else ""
    return {
        "name": "megacmd",
        "available": available,
        "detected_version": detected_version,
        "required_for": ["real transfers", "login/logout", "terminal megacmd commands"],
        "install_instructions": (
            "Install MEGAcmd and ensure its binaries are in PATH. "
            "On macOS app installs, binaries are typically at "
            "/Applications/MEGAcmd.app/Contents/MacOS."
        ),
        "suggested_install_commands": [
            "brew install --cask megacmd",
            "export MEGACMD_PATH=/Applications/MEGAcmd.app/Contents/MacOS",
        ],
        "details": {
            "resolved_path": version_cmd or "",
            "checked_with_subprocess_env": True,
        },
    }


def _python_runtime_diagnostic() -> dict[str, Any]:
    fastapi_available = importlib.util.find_spec("fastapi") is not None
    uvicorn_available = importlib.util.find_spec("uvicorn") is not None
    available = fastapi_available and uvicorn_available
    return {
        "name": "python_runtime",
        "available": available,
        "detected_version": f"python {sys.version.split()[0]}",
        "required_for": ["backend api server"],
        "install_instructions": "Install backend dependencies from api/requirements.txt.",
        "suggested_install_commands": [
            "python3 -m venv .venv",
            "source .venv/bin/activate",
            "pip install -r api/requirements.txt",
        ],
        "details": {
            "fastapi_available": fastapi_available,
            "uvicorn_available": uvicorn_available,
        },
    }


def _wget2_diagnostic() -> dict[str, Any]:
    """GNU Wget2 is the HTTP(S) client used by http_downloads (not wget 1.x)."""
    env = ms.subprocess_env()
    path = env.get("PATH", "")
    override = (os.environ.get("WGET_HTTP_BIN") or "").strip()
    wget2_bin: str | None = None
    if override and os.path.isabs(override) and os.path.isfile(override) and os.access(override, os.X_OK):
        wget2_bin = override
    if not wget2_bin:
        wget2_bin = shutil.which("wget2", path=path)
    available = bool(wget2_bin)
    cmd = [wget2_bin, "--version"] if wget2_bin else ["wget2", "--version"]
    version = _run_version_command(cmd, env=env) if available else ""
    first_line = version.splitlines()[0].strip() if version else ""
    legacy = shutil.which("wget", path=path)
    return {
        "name": "wget2",
        "available": available,
        "detected_version": first_line[:200],
        "required_for": ["generic HTTP(S) direct downloads"],
        "install_instructions": "Install GNU Wget2 (e.g. apt install wget2 on Debian/Ubuntu).",
        "suggested_install_commands": ["sudo apt-get install -y wget2"],
        "details": {
            "resolved_path": wget2_bin or "",
            "legacy_wget_resolved_path": legacy or "",
            "checked_with_subprocess_env": True,
        },
    }


def _node_runtime_diagnostic() -> dict[str, Any]:
    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    available = bool(node_bin and npm_bin)
    node_version = _run_version_command(["node", "--version"]) if node_bin else ""
    return {
        "name": "node_runtime",
        "available": available,
        "detected_version": node_version,
        "required_for": ["react frontend local dev/build"],
        "install_instructions": "Install Node.js (includes npm) for local frontend development.",
        "suggested_install_commands": ["brew install node", "cd web && npm install"],
        "details": {
            "node_found": bool(node_bin),
            "npm_found": bool(npm_bin),
        },
    }


def collect_tool_diagnostics() -> dict[str, Any]:
    tools = [
        _megacmd_diagnostic(),
        _wget2_diagnostic(),
        _python_runtime_diagnostic(),
        _node_runtime_diagnostic(),
    ]
    missing = [t["name"] for t in tools if not t.get("available")]
    return {
        "ok": len(missing) == 0,
        "missing_tools": missing,
        "tools": tools,
    }


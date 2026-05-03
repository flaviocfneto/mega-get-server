from __future__ import annotations

import os
import shlex

import mega_service as ms
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from security import rate_limit, require_csrf_boundary, require_scope

router = APIRouter(prefix="/api", tags=["terminal"])


class TerminalBody(BaseModel):
    command: str = Field(min_length=1, max_length=512)


@router.post("/terminal")
@rate_limit("terminal", limit=15, window_seconds=60)
async def api_terminal(body: TerminalBody, request: Request, _: None = Depends(require_scope("admin"))) -> dict[str, object]:
    require_csrf_boundary(request)
    raw = (body.command or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Command is required")

    parts = shlex.split(raw)
    if not parts:
        raise HTTPException(status_code=400, detail="Command is required")

    allowed = {
        "mega-whoami",
        "mega-version",
        "mega-transfers",
        "mega-get",
        "mega-ls",
        "mega-df",
        "mega-export",
    }
    cmd = parts[0]
    if cmd not in allowed:
        return {
            "ok": False,
            "command": raw,
            "exit_code": 126,
            "output": f"Blocked command: {cmd}. Allowed: {', '.join(sorted(allowed))}",
            "blocked_reason": "not_in_allowlist",
        }

    # Harden terminal commands: prevent arbitrary path access
    path_args = [p for p in parts[1:] if not p.startswith("-")]

    if cmd == "mega-get":
        # mega-get [OPTIONS] <remotepath> [localpath]
        if len(path_args) != 2:
            return {
                "ok": False,
                "command": raw,
                "exit_code": 126,
                "output": f"Blocked: mega-get requires exactly one remote path and one local path within {ms.DOWNLOAD_DIR}",
                "blocked_reason": "invalid_arguments",
            }
        local_path = path_args[1]
    elif cmd in ("mega-ls", "mega-export"):
        # For mega-ls and mega-export, ensure they don't use absolute local paths if we ever support them,
        # but primarily we want to block command injection via unusual arguments.
        # Currently we just allow them but we can add more checks if they start taking local paths.
        local_path = None
    else:
        local_path = None

    if local_path:
        # Ensure it's not trying to escape DOWNLOAD_DIR using a safer commonpath check
        abs_download_dir = os.path.abspath(ms.DOWNLOAD_DIR)
        abs_local_path = os.path.abspath(local_path)
        try:
            # Use os.path.commonpath to prevent /data vs /data_private prefix bypasses
            if os.path.commonpath([abs_local_path, abs_download_dir]) != abs_download_dir:
                return {
                    "ok": False,
                    "command": raw,
                    "exit_code": 126,
                    "output": f"Blocked: local path must be within {ms.DOWNLOAD_DIR}",
                    "blocked_reason": "path_traversal_attempt",
                }
        except ValueError:
            return {
                "ok": False,
                "command": raw,
                "exit_code": 126,
                "output": "Invalid path.",
                "blocked_reason": "invalid_path",
            }

    # Additional hardening: block common injection characters if shlex didn't catch them.
    # Though shlex.split is used, we double check the parts don't contain shell metacharacters.
    # Added $, (), \, {}, *, ? for defense-in-depth against variable expansion and globbing.
    for part in parts:
        if any(c in part for c in ";&|><`$()\\{}*?"):
            return {
                "ok": False,
                "command": raw,
                "exit_code": 126,
                "output": "Blocked: command contains restricted characters.",
                "blocked_reason": "injection_attempt",
            }

    result = await ms.run_megacmd_command(parts)
    return {
        "ok": bool(result["ok"]),
        "command": raw,
        "exit_code": result.get("exit_code", -1),
        "output": result.get("stdout") or result.get("output") or "(ok)",
    }

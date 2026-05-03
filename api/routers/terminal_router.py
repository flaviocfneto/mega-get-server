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

    # Harden mega-get: ensure it doesn't write to arbitrary paths
    if cmd == "mega-get":
        # mega-get [OPTIONS] <remotepath> [localpath]
        # We need to ensure that if localpath is provided, it's within DOWNLOAD_DIR
        # Also ensure we don't allow default path (CWD) bypass if it's not the download dir.
        args = [p for p in parts[1:] if not p.startswith("-")]

        # If no local path is provided, MEGAcmd defaults to CWD.
        # We must either block this or force it to DOWNLOAD_DIR.
        # Blocking is safer for the terminal router to prevent accidental overwrites in /app.
        if len(args) <= 1:
            return {
                "ok": False,
                "command": raw,
                "exit_code": 126,
                "output": f"Blocked: an explicit local path within {ms.DOWNLOAD_DIR} must be provided",
                "blocked_reason": "path_traversal_attempt",
            }

        local_path = args[1]
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

    result = await ms.run_megacmd_command(parts)
    return {
        "ok": bool(result["ok"]),
        "command": raw,
        "exit_code": result.get("exit_code", -1),
        "output": result.get("stdout") or result.get("output") or "(ok)",
    }

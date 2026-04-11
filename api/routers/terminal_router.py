from __future__ import annotations

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

    result = await ms.run_megacmd_command(parts)
    return {
        "ok": bool(result["ok"]),
        "command": raw,
        "exit_code": result.get("exit_code", -1),
        "output": result.get("stdout") or result.get("output") or "(ok)",
    }

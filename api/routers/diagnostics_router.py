from __future__ import annotations

import tool_diagnostics as td
import mega_service as ms
from fastapi import APIRouter, Depends, Request
from security import rate_limit, require_csrf_boundary, require_scope

router = APIRouter(prefix="/api/diag", tags=["diagnostics"])


@router.get("/commands")
@rate_limit("diag_commands", limit=20, window_seconds=60)
async def api_diag_commands(request: Request, _: None = Depends(require_scope("admin"))) -> dict[str, object]:
    return {"events": ms.get_command_events()}


@router.post("/probe")
@rate_limit("diag_probe", limit=10, window_seconds=60)
async def api_diag_probe(request: Request, _: None = Depends(require_scope("admin"))) -> dict[str, object]:
    require_csrf_boundary(request)
    results = await ms.command_probe()
    return {"results": results}


@router.get("/tools")
@rate_limit("diag_tools", limit=30, window_seconds=60)
async def api_diag_tools(request: Request, _: None = Depends(require_scope("admin"))) -> dict[str, object]:
    return td.collect_tool_diagnostics()

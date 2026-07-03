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
async def api_terminal(
    body: TerminalBody, request: Request, _: None = Depends(require_scope("admin"))
) -> dict[str, object]:
    require_csrf_boundary(request)
    raw = (body.command or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Command is required")

    if any(c in raw for c in "\n\r"):
        return {
            "ok": False,
            "command": raw,
            "exit_code": 126,
            "output": "Blocked: command contains restricted characters.",
            "blocked_reason": "injection_attempt",
        }

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
        "wget2",
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

    # SSRF protection for wget2 and URL-like arguments
    from urllib.parse import urlparse

    from http_downloads import _host_is_blocked

    # Harden terminal commands: prevent arbitrary path access and SSRF
    abs_download_dir = os.path.abspath(ms.DOWNLOAD_DIR)

    for part in parts[1:]:
        # 1. URL/SSRF Validation
        # Check for protocol prefixes anywhere in the argument (e.g., --base=http://...)
        part_l = part.lower()
        # Expanded protocol list to prevent SSRF and Local File Disclosure (LFD)
        for proto in ("http://", "https://", "ftp://", "file://", "data://", "gopher://", "php://", "dict://"):
            if proto in part_l:
                idx = part_l.find(proto)
                url_to_check = part[idx:]
                try:
                    parsed = urlparse(url_to_check)
                    host = (parsed.hostname or "").lower()
                    if _host_is_blocked(host):
                        return {
                            "ok": False,
                            "command": raw,
                            "exit_code": 126,
                            "output": f"Blocked: untrusted host in URL '{part}'",
                            "blocked_reason": "ssrf_attempt",
                        }
                except Exception:
                    pass
                break

        # 2. Path Traversal Validation (Check ALL arguments, even flags with paths)
        # Extract potential path from argument (e.g., --output-document=/path or just /path)
        potential_path = part
        if "=" in part:
            potential_path = part.split("=", 1)[1]
        elif part.startswith("-") and not part.startswith("--") and len(part) > 2 and ("/" in part or ".." in part):
            # Handle generic attached short flags with paths or traversal like -C/etc/passwd or -O../file
            potential_path = part[2:]

        # Heuristic: if it looks like a remote path, don't apply local traversal checks.
        # These heuristics should ONLY apply to MEGAcmd tools, not generic tools like wget2.
        is_mega_cmd = cmd.startswith("mega-")
        if is_mega_cmd:
            if potential_path.startswith("mega:/"):
                continue

            # In MEGAcmd, /Root, /Bin, /Incoming are the standard remote roots.
            # Restricted: removed '//' heuristic as it can be used for path traversal bypass.
            # If it looks remote, we skip local traversal checks UNLESS it contains '..'.
            is_likely_remote = any(potential_path.startswith(r) for r in ("/Root", "/Bin", "/Incoming"))
            if is_likely_remote and ".." not in potential_path:
                continue

        # Normalize and validate ALL arguments as potential local paths
        # (even if they don't contain a slash, to prevent local access relative to CWD)
        if os.path.isabs(potential_path):
            abs_arg = os.path.abspath(potential_path)
        else:
            abs_arg = os.path.abspath(os.path.join(abs_download_dir, potential_path))

        try:
            if os.path.commonpath([abs_arg, abs_download_dir]) != abs_download_dir:
                return {
                    "ok": False,
                    "command": raw,
                    "exit_code": 126,
                    "output": f"Blocked: local path access outside {ms.DOWNLOAD_DIR} in argument '{part}'",
                    "blocked_reason": "path_traversal_attempt",
                }
        except ValueError:
            # This can happen if paths are on different drives on Windows, or other oddities
            return {
                "ok": False,
                "command": raw,
                "exit_code": 126,
                "output": f"Invalid path in argument '{part}'",
                "blocked_reason": "invalid_path",
            }

    if cmd == "mega-get":
        # mega-get [OPTIONS] <remotepath> [localpath]
        # path_args for legacy check: non-dash arguments
        path_args = [p for p in parts[1:] if not p.startswith("-")]
        if len(path_args) != 2:
            return {
                "ok": False,
                "command": raw,
                "exit_code": 126,
                "output": f"Blocked: mega-get requires exactly one remote path and one local path within {ms.DOWNLOAD_DIR}",
                "blocked_reason": "invalid_arguments",
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

    result = await ms.run_megacmd_command(parts, cwd=abs_download_dir)
    return {
        "ok": bool(result["ok"]),
        "command": ms.redact_sensitive_text(raw),
        "exit_code": result.get("exit_code", -1),
        "output": result.get("stdout") or result.get("output") or "(ok)",
    }

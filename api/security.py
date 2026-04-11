from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Header, HTTPException, Request


def _auth_mode() -> str:
    return os.environ.get("API_AUTH_MODE", "optional").strip().lower()


def _key_for_scope(scope: str) -> str:
    if scope == "admin":
        return os.environ.get("API_ADMIN_KEY", "").strip()
    return os.environ.get("API_WRITE_KEY", "").strip()


def require_scope(scope: str) -> Callable[..., None]:
    def dependency(x_api_key: str | None = Header(default=None)) -> None:
        mode = _auth_mode()
        if mode != "strict":
            return
        expected = _key_for_scope(scope)
        if not expected:
            raise HTTPException(status_code=503, detail=f"Server auth misconfigured for scope: {scope}")
        if (x_api_key or "").strip() != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return dependency


# Per-client-host sliding windows; not shared across processes (see INFRASTRUCTURE.md section 8.1).
_rate_state: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(name: str, limit: int = 30, window_seconds: int = 60) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Limit requests per route name and client host using a sliding time window.

    Tests: ``api/tests/test_security_controls.py`` (429 behavior and window reset via
    ``test_rate_limit_resets_after_window``). Multi-replica and process boundaries:
    ``INFRASTRUCTURE.md`` section 8.1.
    """
    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            request = kwargs.get("request")
            if request is None:
                for a in args:
                    if isinstance(a, Request):
                        request = a
                        break
            client_host = request.client.host if isinstance(request, Request) and request.client else "unknown"
            key = f"{name}:{client_host}"
            now = time.time()
            q = _rate_state[key]
            while q and (now - q[0]) > window_seconds:
                q.popleft()
            if len(q) >= limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            q.append(now)
            return await fn(*args, **kwargs)

        return wrapped

    return deco


def _trusted_origins() -> set[str]:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173")
    return {o.strip().lower() for o in raw.split(",") if o.strip()}


def _auth_transport() -> str:
    return os.environ.get("API_AUTH_TRANSPORT", "header_key").strip().lower()


def _csrf_mode() -> str:
    return os.environ.get("CSRF_ENFORCEMENT_MODE", "origin_only").strip().lower()


def _csrf_header_name() -> str:
    return os.environ.get("CSRF_HEADER_NAME", "x-csrf-token").strip().lower()


def require_csrf_boundary(request: Request) -> None:
    """
    Enforce Origin/Referer checks for unsafe methods.
    This guards server-side state mutations from cross-site invocation.
    """
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    mode = _csrf_mode()
    transport = _auth_transport()
    if mode == "disabled":
        raise HTTPException(status_code=503, detail="CSRF enforcement disabled for unsafe methods")
    trusted = _trusted_origins()
    origin = (request.headers.get("origin") or "").strip().lower()
    referer = (request.headers.get("referer") or "").strip().lower()
    if origin:
        if origin not in trusted:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: untrusted origin")
    if referer:
        for allowed in trusted:
            if referer.startswith(allowed):
                break
        else:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: untrusted referer")
    elif not origin:
        raise HTTPException(status_code=403, detail="CSRF boundary violation: missing origin/referer")

    if transport == "cookie_session":
        if mode != "origin_plus_token":
            raise HTTPException(
                status_code=503,
                detail="CSRF policy misconfigured: cookie_session requires origin_plus_token mode",
            )
        header_name = _csrf_header_name()
        token = (request.headers.get(header_name) or "").strip()
        if not token:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: missing csrf token")
        return

    if mode == "origin_plus_token":
        header_name = _csrf_header_name()
        token = (request.headers.get(header_name) or "").strip()
        if not token:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: missing csrf token")
        return

    if mode == "origin_only":
        return

    raise HTTPException(status_code=503, detail=f"CSRF policy misconfigured: unsupported mode '{mode}'")

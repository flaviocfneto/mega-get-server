from __future__ import annotations

import os
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from functools import wraps
from typing import Any
from urllib.parse import urlparse

from fastapi import Header, HTTPException, Request, Response


def _auth_mode() -> str:
    return os.environ.get("API_AUTH_MODE", "strict").strip().lower()


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
        if not secrets.compare_digest((x_api_key or "").strip(), expected):
            raise HTTPException(status_code=401, detail="Unauthorized")

    return dependency


# Per-client-host sliding windows; not shared across processes (see INFRASTRUCTURE.md section 8.1).
_rate_state: dict[str, deque[float]] = defaultdict(deque)
_rate_windows: dict[str, int] = {}
_rate_state_lock = threading.Lock()
_last_cleanup_time = 0.0


def rate_limit(
    name: str, limit: int = 30, window_seconds: int = 60
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Limit requests per route name and client host using a sliding time window.

    Tests: ``api/tests/test_security_controls.py`` (429 behavior and window reset via
    ``test_rate_limit_resets_after_window``). Multi-replica and process boundaries:
    ``INFRASTRUCTURE.md`` section 8.1.
    """

    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            global _last_cleanup_time
            request = kwargs.get("request")
            if request is None:
                for a in args:
                    if isinstance(a, Request):
                        request = a
                        break
            client_host = request.client.host if isinstance(request, Request) and request.client else "unknown"
            key = f"{name}:{client_host}"
            now = time.time()

            with _rate_state_lock:
                # Periodic cleanup of expired rate limit entries across all keys to prevent memory exhaustion / DoS
                if now - _last_cleanup_time > 300.0:
                    _last_cleanup_time = now
                    for k in list(_rate_state.keys()):
                        dq = _rate_state[k]
                        win = _rate_windows.get(k, 60)
                        # Purge expired timestamps from this deque using the key's target window
                        while dq and (now - dq[0]) > win:
                            dq.popleft()
                        if not dq:
                            _rate_state.pop(k, None)
                            _rate_windows.pop(k, None)

                # Process current key
                _rate_windows[key] = window_seconds
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
    if mode == "disabled":
        raise HTTPException(status_code=503, detail="CSRF enforcement disabled for unsafe methods")

    trusted = _trusted_origins()
    origin = (request.headers.get("origin") or "").strip().lower()
    referer = (request.headers.get("referer") or "").strip().lower()
    if origin:
        if origin not in trusted:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: untrusted origin")
    if referer:
        try:
            ref_parsed = urlparse(referer)
            if not ref_parsed.scheme or not ref_parsed.netloc:
                raise HTTPException(status_code=403, detail="CSRF boundary violation: invalid referer")
            ref_origin = f"{ref_parsed.scheme}://{ref_parsed.netloc}".lower()
        except ValueError:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: invalid referer") from None
        if ref_origin not in trusted:
            # Also check if it's a trusted origin without a path, as urlparse might vary
            if referer.lower().rstrip("/") not in trusted:
                raise HTTPException(status_code=403, detail="CSRF boundary violation: untrusted referer")
    elif not origin:
        # Strict mode: one of Origin or Referer MUST be present for state-changing requests.
        # This protects against some edge-case CSRF bypasses in specific browser configurations.
        raise HTTPException(status_code=403, detail="CSRF boundary violation: missing origin/referer")

    if mode == "origin_plus_token" or _auth_transport() == "cookie_session":
        header_name = _csrf_header_name()
        header_token = (request.headers.get(header_name) or "").strip()
        cookie_token = request.cookies.get("csrftoken", "").strip()

        if not header_token:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: missing csrf token header")
        if not cookie_token:
            raise HTTPException(status_code=403, detail="CSRF boundary violation: missing csrf cookie")
        if not secrets.compare_digest(header_token, cookie_token):
            raise HTTPException(status_code=403, detail="CSRF boundary violation: token mismatch")
        return

    if mode == "origin_only":
        return

    raise HTTPException(status_code=503, detail=f"CSRF policy misconfigured: unsupported mode '{mode}'")


def _csrf_cookie_samesite() -> str:
    return os.environ.get("CSRF_COOKIE_SAMESITE", "strict").strip().lower()


def set_csrf_cookie(response: Response) -> str:
    """Generate and set a new CSRF cookie on the response."""
    token = secrets.token_urlsafe(32)
    samesite = _csrf_cookie_samesite()
    if samesite not in {"lax", "strict", "none"}:
        samesite = "strict"
    secure_cookie = os.environ.get("SECURE_COOKIES", "0") == "1"
    if samesite == "none":
        # None requires Secure=True in modern browsers
        secure_cookie = True
    response.set_cookie(
        key="csrftoken",
        value=token,
        httponly=False,  # Frontend needs to read it to put it in the header
        samesite=samesite,
        secure=secure_cookie,
    )
    return token


def generate_nonce(length: int = 16) -> str:
    """Generate a cryptographically secure nonce for CSP."""
    return secrets.token_urlsafe(length)

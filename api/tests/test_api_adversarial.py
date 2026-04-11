"""
Boundary and abuse-case checks for mutation routes: validation failures must not
leak stack traces, file paths, or framework internals (SEC-006 residual).
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
import api_main

SAFE_HEADERS = {"origin": "http://localhost:5173"}

_INTERNAL_MARKERS = (
    "traceback",
    "mega_service.py",
    "api_main.py",
    "/site-packages/",
    "file \"/",
    "line ",
)


def assert_no_server_internals_leaked(res: Response) -> None:
    text = res.text.lower()
    for marker in _INTERNAL_MARKERS:
        assert marker not in text, f"unexpected internal leak ({marker!r}) in response body"


def _cases() -> list[tuple[str, str, str, dict[str, Any], int]]:
    """name, method, path, extra client.request kwargs (json/data), expected status."""
    long_cmd = "a" * 600
    long_url = "https://mega.nz/file/" + ("b" * 5000)
    return [
        ("terminal_oversized_command", "POST", "/api/terminal", {"json": {"command": long_cmd}}, 422),
        ("download_url_too_long", "POST", "/api/download", {"json": {"url": long_url}}, 422),
        ("login_invalid_email_type", "POST", "/api/login", {"json": {"email": 1, "password": "x"}}, 422),
        ("bulk_empty_tags", "POST", "/api/transfers/bulk", {"json": {"tags": [], "action": "pause"}}, 422),
        ("bulk_action_too_long", "POST", "/api/transfers/bulk", {"json": {"tags": ["1"], "action": "x" * 40}}, 422),
        ("transfer_update_bad_priority", "POST", "/api/transfers/1/update", {"json": {"priority": "INVALID"}}, 400),
        ("transfer_update_tags_not_array", "POST", "/api/transfers/1/update", {"json": {"tags": "nope"}}, 400),
        ("transfer_limit_missing_field", "POST", "/api/transfers/1/limit", {"json": {}}, 400),
        (
            "config_body_not_object",
            "POST",
            "/api/config",
            {"content": "[]", "headers": {"content-type": "application/json"}},
            422,
        ),
    ]


@pytest.mark.parametrize(
    "name,method,path,kwargs,expected_status",
    _cases(),
    ids=[c[0] for c in _cases()],
)
def test_mutation_validation_errors_are_safe(
    name: str,
    method: str,
    path: str,
    kwargs: dict[str, Any],
    expected_status: int,
):
    del name  # used by ids only
    req_kw = dict(kwargs)
    extra_headers = req_kw.pop("headers", {})
    headers = {**SAFE_HEADERS, **extra_headers}
    with TestClient(api_main.app) as client:
        res = client.request(method, path, headers=headers, **req_kw)
    assert res.status_code == expected_status
    assert_no_server_internals_leaked(res)


def test_config_post_rejects_huge_json_object():
    """Very large JSON object should fail validation or parsing without leaking internals."""
    huge = {"k": "v" * 80_000}
    with TestClient(api_main.app) as client:
        res = client.post("/api/config", json=huge, headers=SAFE_HEADERS)
    assert res.status_code in (200, 413, 422)
    assert_no_server_internals_leaked(res)


def test_mutation_routes_safe_on_csrf_rejection():
    with TestClient(api_main.app) as client:
        res = client.post("/api/download", json={"url": "https://mega.nz/file/abc"})
    assert res.status_code == 403
    assert_no_server_internals_leaked(res)


def test_diag_probe_validation_safe(monkeypatch):
    async def fake_probe():
        return []

    monkeypatch.setattr(api_main.ms, "command_probe", fake_probe)
    with TestClient(api_main.app) as client:
        res = client.post("/api/diag/probe", headers=SAFE_HEADERS)
    assert res.status_code == 200
    assert_no_server_internals_leaked(res)


def test_logout_delete_routes_return_safe_json():
    with TestClient(api_main.app) as client:
        logout = client.post("/api/logout", headers=SAFE_HEADERS)
        hist = client.delete("/api/history", headers=SAFE_HEADERS)
        logs = client.delete("/api/logs", headers=SAFE_HEADERS)
        cancel_all = client.post("/api/transfers/cancel-all", headers=SAFE_HEADERS)
    for res in (logout, hist, logs, cancel_all):
        assert res.status_code == 200
        assert_no_server_internals_leaked(res)


def test_transfer_action_posts_safe(monkeypatch):
    async def noop_action(_action, _tag):
        return None

    async def noop_resume(_tag, log_label=""):
        return None

    monkeypatch.setattr(api_main.ms, "run_mega_transfers_action", noop_action)
    monkeypatch.setattr(api_main.ms, "run_mega_transfers_resume_for_tag", noop_resume)
    with TestClient(api_main.app) as client:
        pause = client.post("/api/transfers/9/pause", headers=SAFE_HEADERS)
        resume = client.post("/api/transfers/9/resume", headers=SAFE_HEADERS)
        retry = client.post("/api/transfers/9/retry", headers=SAFE_HEADERS)
        cancel = client.post("/api/transfers/9/cancel", headers=SAFE_HEADERS)
    for res in (pause, resume, retry, cancel):
        assert res.status_code == 200
        assert_no_server_internals_leaked(res)

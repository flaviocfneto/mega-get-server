"""
FastAPI server: /api/* for React SPA + optional static files from ./static (vite dist).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import mega_service as ms
import pending_correlation as pcorr
import pending_queue as pq
import tool_diagnostics as td
import transfer_metadata as tm
import ui_settings as us
from routers.diagnostics_router import router as diagnostics_router
from routers.terminal_router import router as terminal_router
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from security import require_csrf_boundary, require_scope, rate_limit

STATIC_DIR = Path(__file__).resolve().parent / "static"
APP_STARTED = time.time()
_analytics_completed = 0
_analytics_failed = 0
_last_states: dict[str, str] = {}
# Last known byte fields per transfer tag (for inferred completion when a row vanishes from mega-transfers).
_last_row_snapshot: dict[str, dict[str, int]] = {}

_IN_FLIGHT_STATES = frozenset({"ACTIVE", "QUEUED", "RETRYING", "PAUSED"})

_last_correlation_merge_at = 0.0
_CORRELATION_MERGE_MIN_SEC = 3.0

DAILY_ANALYTICS_PATH = Path(__file__).resolve().parent / ".mega-analytics-daily.json"
_daily_buckets: dict[str, dict[str, int]] | None = None
_daily_loaded = False


def _ensure_daily_loaded() -> None:
    global _daily_buckets, _daily_loaded
    if _daily_loaded:
        return
    _daily_loaded = True
    _daily_buckets = {}
    if DAILY_ANALYTICS_PATH.is_file():
        try:
            raw = json.loads(DAILY_ANALYTICS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if not isinstance(k, str) or not isinstance(v, dict):
                        continue
                    _daily_buckets[k] = {
                        "bytes": int(v.get("bytes", 0) or 0),
                        "count": int(v.get("count", 0) or 0),
                    }
        except (OSError, ValueError, TypeError):
            _daily_buckets = {}


def _persist_daily_buckets() -> None:
    if _daily_buckets is None:
        return
    try:
        DAILY_ANALYTICS_PATH.write_text(json.dumps(_daily_buckets, indent=2), encoding="utf-8")
    except OSError:
        pass


def _bump_daily_on_completed(bytes_done: int) -> None:
    _ensure_daily_loaded()
    assert _daily_buckets is not None
    key = date.today().isoformat()
    if key not in _daily_buckets:
        _daily_buckets[key] = {"bytes": 0, "count": 0}
    _daily_buckets[key]["count"] += 1
    _daily_buckets[key]["bytes"] += max(0, int(bytes_done))
    _persist_daily_buckets()


def _daily_stats_last_7_days() -> list[dict[str, Any]]:
    _ensure_daily_loaded()
    assert _daily_buckets is not None
    today = date.today()
    out: list[dict[str, Any]] = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        k = d.isoformat()
        b = _daily_buckets.get(k, {"bytes": 0, "count": 0})
        out.append({"date": k, "bytes": b["bytes"], "count": b["count"]})
    return out


def _total_persisted_downloaded_bytes() -> int:
    _ensure_daily_loaded()
    assert _daily_buckets is not None
    return sum(max(0, int(v.get("bytes", 0) or 0)) for v in _daily_buckets.values())


def _full_config() -> dict[str, Any]:
    merged = {**us.DEFAULT_UI_KEYS, **us.load_stored()}
    merged["download_dir"] = ms.DOWNLOAD_DIR
    merged["poll_interval"] = 1000
    merged["transfer_limit"] = int(ms.TRANSFER_LIST_LIMIT)
    return merged


def _update_analytics_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    global _analytics_completed, _analytics_failed
    active = 0
    queued = 0
    completed_now = 0
    failed_now = 0
    inflight_downloaded = 0
    total_speed = 0
    active_n = 0
    current_tags: set[str] = set()
    for r in rows:
        state = ms.normalize_transfer_state(str(r.get("state", "")))
        tag = str(r.get("tag", ""))
        if tag:
            current_tags.add(tag)
            _last_row_snapshot[tag] = {
                "size_bytes": int(r.get("size_bytes", 0) or 0),
                "downloaded_bytes": int(r.get("downloaded_bytes", 0) or 0),
            }
        downloaded_b = int(r.get("downloaded_bytes", 0) or 0)
        sp = int(r.get("speed_bps", 0) or 0)
        total_speed += sp
        prev = _last_states.get(tag)
        if state == "ACTIVE":
            active += 1
            active_n += 1
            inflight_downloaded += downloaded_b
        elif state == "QUEUED":
            queued += 1
            inflight_downloaded += downloaded_b
        elif state == "RETRYING":
            inflight_downloaded += downloaded_b
        elif state == "PAUSED":
            inflight_downloaded += downloaded_b
        elif state == "COMPLETED":
            completed_now += 1
            if prev != "COMPLETED":
                _analytics_completed += 1
                done_bytes = int(r.get("size_bytes", 0) or r.get("downloaded_bytes", 0) or 0)
                _bump_daily_on_completed(done_bytes)
        elif state == "FAILED":
            failed_now += 1
            if prev != "FAILED":
                _analytics_failed += 1
        if tag:
            _last_states[tag] = state

    # MEGAcmd often drops finished transfers from the list before we ever see state COMPLETED.
    # Infer one completion when a tag that was in-flight disappears (same server process only;
    # _last_states is cleared on restart so we do not replay stale completions).
    for tag in list(_last_states.keys()):
        if not tag or tag in current_tags:
            continue
        prev = _last_states.pop(tag)
        snap = _last_row_snapshot.pop(tag, {})
        bytes_done = int(snap.get("size_bytes", 0) or snap.get("downloaded_bytes", 0) or 0)
        if prev in _IN_FLIGHT_STATES:
            _analytics_completed += 1
            _bump_daily_on_completed(bytes_done)

    total_downloaded = _total_persisted_downloaded_bytes() + inflight_downloaded
    avg_speed = total_speed // active_n if active_n else 0
    return {
        "total_downloaded_bytes": total_downloaded,
        "total_transfers_completed": _analytics_completed if _analytics_completed else completed_now,
        "total_transfers_failed": _analytics_failed if _analytics_failed else failed_now,
        "average_speed_bps": avg_speed,
        "uptime_seconds": int(time.time() - APP_STARTED),
        "daily_stats": _daily_stats_last_7_days(),
        "active_count": active,
        "queued_count": queued,
    }


async def _transfer_by_tag(tag: str) -> dict[str, Any]:
    raw = await ms.get_transfer_list()
    parsed = ms.parse_transfer_list(raw)
    for t in parsed:
        if str(t.get("tag")) == tag:
            return ms.parsed_transfer_to_api_row(t)
    # Return metadata-backed fallback even if transfer is not currently listed.
    fallback = ms.parsed_transfer_to_api_row({"tag": tag, "size_display": "Unknown", "progress_pct": 0})
    return fallback


QUEUE_START_ALL_MAX = 20


def _redacted_client_error(raw: str | None) -> str:
    if not raw:
        return "Download failed"
    return ms.redact_sensitive_text(str(raw))[:512]


def _parse_queue_item_id(item_id: str) -> str:
    try:
        return str(uuid.UUID(item_id.strip()))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid queue item id") from None


async def _execute_dispatched_queue_row(row: dict[str, Any]) -> None:
    item_id = str(row["id"])
    url = str(row.get("url", ""))
    try:
        url = ms.validate_mega_download_url(url)
    except ValueError:
        await pq.set_item_status(item_id, status="FAILED", last_error=_redacted_client_error("Invalid stored URL"))
        return
    labels = row.get("tags") if isinstance(row.get("tags"), list) else []
    pr = str(row.get("priority") or "NORMAL")
    ok, err = await ms.run_mega_get_with_user_meta(
        url, [str(x) for x in labels], pr, pending_id=item_id
    )
    if ok:
        await pq.remove_item(item_id)
    else:
        await pq.set_item_status(item_id, status="FAILED", last_error=_redacted_client_error(err))


class DownloadBody(BaseModel):
    url: str = Field(max_length=4096)
    tags: list[str] | None = Field(default=None, max_length=50)
    priority: str | None = None
    autostart: bool = True


class QueueAddBody(BaseModel):
    url: str = Field(max_length=4096)
    tags: list[str] | None = Field(default=None, max_length=50)
    priority: str | None = None


class BulkBody(BaseModel):
    tags: list[str] = Field(min_length=1, max_length=200)
    action: str = Field(min_length=2, max_length=32)
    value: Any | None = None


class LoginBody(BaseModel):
    email: str | None = None
    password: str | None = None


class LogoutBody(BaseModel):
    email: str | None = None
    password: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    ms.set_history_path(ms.default_history_path())
    ms.load_history()
    ms.log_buffer.clear()

    if not ms.SIMULATE and not ms.UI_TEST_MODE:
        ms.log_buffer.append("⏳ Initializing MEGAcmd...")
    if ms.UI_TEST_MODE:
        ms.log_buffer.append("🧪 UI TEST MODE - Showing sample transfers for development")
        ms.log_buffer.append("ℹ Set UI_TEST_MODE=0 or remove env var to use real MEGAcmd")

    server_ready = await ms.ensure_mega_cmd_server_running()
    os.makedirs(ms.DOWNLOAD_DIR, exist_ok=True)

    if not server_ready and not ms.in_docker() and sys.platform == "darwin" and not ms.UI_TEST_MODE:
        ms.log_buffer.append("⚠ MEGAcmd server not detected. Open MEGAcmd from Applications, then restart this app.")
    elif server_ready and not ms.UI_TEST_MODE:
        ms.log_buffer.append(f"✓ MEGAcmd ready. Downloads will be saved to: {ms.DOWNLOAD_DIR}")
    if ms.SIMULATE:
        ms.log_buffer.append("ℹ Simulation mode (MEGA_SIMULATE=1) - no MEGA CMD required.")
    diag = td.collect_tool_diagnostics()
    for tool in diag.get("tools", []):
        if tool.get("available"):
            continue
        name = str(tool.get("name", "tool"))
        required_for = ", ".join(tool.get("required_for", []))
        ms.log_buffer.append(f"⚠ Missing external tool: {name} (required for: {required_for})")
        ms.log_buffer.append(str(tool.get("install_instructions", "")))
        suggestions = tool.get("suggested_install_commands", [])
        if suggestions:
            ms.log_buffer.append(f"Try: {suggestions[0]}")

    yield


app = FastAPI(lifespan=lifespan, title="FileTugger API")
app.include_router(diagnostics_router)
app.include_router(terminal_router)

_origins_env = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173")
_allow_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/config")
async def api_config_get():
    return _full_config()


@app.post("/api/config")
@rate_limit("config_post", limit=20, window_seconds=60)
async def api_config_post(request: Request, body: dict[str, Any] = Body(default_factory=dict), _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    us.merge_post_into_stored(body)
    if body.get("download_dir") is not None:
        ms.log_buffer.append("Note: download_dir is controlled by the server environment; UI value was not applied.")
    return _full_config()


@app.get("/api/account")
async def api_account():
    return await ms.get_account_info()


@app.post("/api/login")
@rate_limit("login", limit=10, window_seconds=60)
async def api_login(body: LoginBody, request: Request):
    require_csrf_boundary(request)
    email = (body.email or "").strip()
    password = body.password or ""
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    login_result = await ms.run_megacmd_command(["mega-login", email, password])
    account = await ms.get_account_info()
    if account["is_logged_in"]:
        ms.log_buffer.append(f"Login success: {account.get('email') or email}")
        return {"status": "success", "message": "Logged in.", "account": account, "command": login_result}
    return {
        "status": "error",
        "message": login_result.get("output") or "Login failed.",
        "account": account,
        "command": login_result,
    }


@app.post("/api/logout")
@rate_limit("logout", limit=20, window_seconds=60)
async def api_logout(request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    result = await ms.run_megacmd_command(["mega-logout"])
    account = await ms.get_account_info()
    if not account["is_logged_in"]:
        ms.log_buffer.append("Logout completed.")
        return {"status": "success", "message": "Logged out.", "command": result}
    return {"status": "error", "message": result.get("output") or "Logout failed.", "command": result}


def _analytics_parse_debug_enabled() -> bool:
    return os.environ.get("MEGA_ANALYTICS_PARSE_DEBUG", "").strip().lower() in ("1", "true", "yes")


@app.get("/api/analytics")
async def api_analytics():
    raw = await ms.get_transfer_list()
    parsed = ms.parse_transfer_list(raw)
    rows = [ms.parsed_transfer_to_api_row(t) for t in parsed]
    out = _update_analytics_from_rows(rows)
    if _analytics_parse_debug_enabled():
        out = {**out, "parse_debug": ms.summarize_transfer_parse(raw, parsed)}
    return out


@app.get("/api/transfers")
async def api_transfers():
    global _last_correlation_merge_at
    raw = await ms.get_transfer_list()
    parsed = ms.parse_transfer_list(raw)
    rows = [ms.parsed_transfer_to_api_row(t) for t in parsed]
    _update_analytics_from_rows(rows)
    now_m = time.monotonic()
    if now_m - _last_correlation_merge_at >= _CORRELATION_MERGE_MIN_SEC:
        _last_correlation_merge_at = now_m
        current_tags = {str(t.get("tag")) for t in parsed if t.get("tag")}
        await pcorr.try_attach_from_current_tags(current_tags)
    return rows


@app.get("/api/history")
async def api_history():
    return ms.get_history()


@app.delete("/api/history")
@rate_limit("history_delete", limit=20, window_seconds=60)
async def api_history_delete(request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    ms.clear_history()
    ms.log_buffer.append("History cleared.")
    return {"success": True}


@app.get("/api/logs")
async def api_logs():
    return [ms.redact_sensitive_text(line) for line in ms.log_buffer.get_lines()]


@app.delete("/api/logs")
@rate_limit("logs_delete", limit=20, window_seconds=60)
async def api_logs_delete(request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    ms.log_buffer.clear()
    ms.log_buffer.append("Logs cleared.")
    return {"success": True}


@app.get("/api/queue")
async def api_queue_list():
    return await pq.list_items()


@app.post("/api/queue")
@rate_limit("queue_add", limit=30, window_seconds=60)
async def api_queue_add(body: QueueAddBody, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    try:
        url = ms.validate_mega_download_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        item = await pq.add_item(url=url, tags=body.tags, priority=body.priority)
    except ValueError as e:
        msg = str(e)
        code = 409 if "full" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return {"success": True, "item": item}


@app.delete("/api/queue/{item_id}")
@rate_limit("queue_delete", limit=60, window_seconds=60)
async def api_queue_delete(item_id: str, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    sid = _parse_queue_item_id(item_id)
    row = await pq.get_item(sid)
    if row is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if str(row.get("status", "")).upper() == "DISPATCHING":
        raise HTTPException(status_code=409, detail="Queue item is starting")
    if not await pq.remove_item(sid):
        raise HTTPException(status_code=404, detail="Queue item not found")
    return {"success": True}


@app.post("/api/queue/{item_id}/start")
@rate_limit("queue_start_item", limit=60, window_seconds=60)
async def api_queue_start_item(item_id: str, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    sid = _parse_queue_item_id(item_id)
    row, code = await pq.mark_dispatching(sid)
    if code == "ok":
        asyncio.create_task(_execute_dispatched_queue_row(row))
        return {"success": True, "started": True, "item": pq.item_to_api_row(row)}
    if code == "already_dispatching":
        raise HTTPException(status_code=409, detail="Queue item is already starting")
    if code == "not_pending":
        raise HTTPException(status_code=409, detail="Queue item is not pending")
    raise HTTPException(status_code=404, detail="Queue item not found")


@app.post("/api/queue/start-next")
@rate_limit("queue_start_next", limit=30, window_seconds=60)
async def api_queue_start_next(request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    fid = await pq.first_pending_id()
    if not fid:
        return {"success": True, "started": False}
    row, code = await pq.mark_dispatching(fid)
    if code == "ok":
        asyncio.create_task(_execute_dispatched_queue_row(row))
        return {"success": True, "started": True, "item": pq.item_to_api_row(row)}
    return {"success": True, "started": False}


@app.post("/api/queue/start-all")
@rate_limit("queue_start_all", limit=8, window_seconds=60)
async def api_queue_start_all(request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    ids = (await pq.list_pending_ids_in_order())[:QUEUE_START_ALL_MAX]
    started: list[str] = []
    for iid in ids:
        row, code = await pq.mark_dispatching(iid)
        if code == "ok" and row:
            asyncio.create_task(_execute_dispatched_queue_row(row))
            started.append(iid)
    return {"success": True, "startedIds": started, "count": len(started)}


@app.post("/api/download")
@rate_limit("download", limit=30, window_seconds=60)
async def api_download(body: DownloadBody, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    try:
        url = ms.validate_mega_download_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not body.autostart:
        try:
            item = await pq.add_item(url=url, tags=body.tags, priority=body.priority)
        except ValueError as e:
            msg = str(e)
            code = 409 if "full" in msg.lower() else 400
            raise HTTPException(status_code=code, detail=msg) from e
        return {"success": True, "message": "Added to queue.", "queued": True, "item": item}

    ms.add_url_to_history(url)
    tags = [str(t).strip() for t in (body.tags or []) if str(t).strip()]
    pr = (body.priority or "NORMAL").strip().upper()
    if pr not in {"LOW", "NORMAL", "HIGH"}:
        pr = "NORMAL"

    async def job():
        await ms.run_mega_get_with_user_meta(url, tags, pr)

    asyncio.create_task(job())
    return {"success": True, "message": "Download command submitted."}


@app.post("/api/transfers/cancel-all")
@rate_limit("transfers_cancel_all", limit=20, window_seconds=60)
async def api_transfers_cancel_all(request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    await ms.run_mega_transfers_cancel_all()
    return {"success": True}


@app.post("/api/transfers/bulk")
@rate_limit("transfers_bulk", limit=20, window_seconds=60)
async def api_transfers_bulk(body: BulkBody, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    affected = 0
    metadata_affected = 0
    for tag in body.tags:
        if body.action == "pause":
            await ms.run_mega_transfers_action("pause", tag)
            affected += 1
        elif body.action == "resume":
            await ms.run_mega_transfers_resume_for_tag(tag, log_label="Resume")
            affected += 1
        elif body.action in ("cancel", "remove"):
            await ms.run_mega_transfers_action("cancel", tag)
            affected += 1
        elif body.action == "set_priority":
            pr = str(body.value or "NORMAL").upper()
            if pr in {"LOW", "NORMAL", "HIGH"}:
                tm.update(tag, {"priority": pr})
                metadata_affected += 1
        elif body.action == "add_tag":
            label = str(body.value or "").strip()
            if label:
                meta = tm.get(tag)
                tags = list(meta.get("tags", []))
                if label not in tags:
                    tags.append(label)
                tm.update(tag, {"tags": tags})
                metadata_affected += 1
        elif body.action == "remove_tag":
            label = str(body.value or "").strip()
            meta = tm.get(tag)
            tags = [t for t in meta.get("tags", []) if t != label]
            tm.update(tag, {"tags": tags})
            metadata_affected += 1
    return {"success": True, "affectedCount": affected + metadata_affected, "metadataAffected": metadata_affected}


@app.post("/api/transfers/{tag}/update")
@rate_limit("transfer_update", limit=40, window_seconds=60)
async def api_transfer_update(tag: str, request: Request, body: dict[str, Any] = Body(default_factory=dict), _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    values: dict[str, Any] = {}
    if "priority" in body and body["priority"] is not None:
        pr = str(body["priority"]).upper()
        if pr not in {"LOW", "NORMAL", "HIGH"}:
            raise HTTPException(status_code=400, detail="priority must be LOW, NORMAL or HIGH")
        values["priority"] = pr
    if "tags" in body and body["tags"] is not None:
        if not isinstance(body["tags"], list):
            raise HTTPException(status_code=400, detail="tags must be an array")
        values["tags"] = [str(t).strip() for t in body["tags"] if str(t).strip()]
    if "url" in body and body["url"] is not None:
        values["url"] = str(body["url"]).strip()
    if not values:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    tm.update(tag, values)
    return {"success": True, "tag": tag, "updated": values, "transfer": await _transfer_by_tag(tag)}


@app.post("/api/transfers/{tag}/limit")
@rate_limit("transfer_limit", limit=40, window_seconds=60)
async def api_transfer_limit(tag: str, request: Request, body: dict[str, Any] = Body(default_factory=dict), _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    if "speed_limit_kbps" not in body:
        raise HTTPException(status_code=400, detail="speed_limit_kbps is required")
    try:
        limit = int(body["speed_limit_kbps"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="speed_limit_kbps must be an integer")
    if limit < 0:
        raise HTTPException(status_code=400, detail="speed_limit_kbps must be >= 0")
    tm.update(tag, {"speed_limit_kbps": limit})
    return {
        "success": True,
        "tag": tag,
        "speed_limit_kbps": limit,
        "transfer": await _transfer_by_tag(tag),
        "applied_to_megacmd": False,
        "message": "Persisted speed limit for UI policy; per-transfer MEGAcmd enforcement is not available.",
    }


@app.post("/api/transfers/{tag}/pause")
@rate_limit("transfer_pause", limit=60, window_seconds=60)
async def api_transfer_pause(tag: str, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    await ms.run_mega_transfers_action("pause", tag)
    return {"success": True}


@app.post("/api/transfers/{tag}/resume")
@rate_limit("transfer_resume", limit=60, window_seconds=60)
async def api_transfer_resume(tag: str, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    await ms.run_mega_transfers_resume_for_tag(tag, log_label="Resume")
    return {"success": True}


@app.post("/api/transfers/{tag}/retry")
@rate_limit("transfer_retry", limit=60, window_seconds=60)
async def api_transfer_retry(tag: str, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    await ms.run_mega_transfers_resume_for_tag(tag, log_label="Retry")
    return {"success": True}


@app.post("/api/transfers/{tag}/cancel")
@rate_limit("transfer_cancel", limit=60, window_seconds=60)
async def api_transfer_cancel(tag: str, request: Request, _: None = Depends(require_scope("write"))):
    require_csrf_boundary(request)
    await ms.run_mega_transfers_action("cancel", tag)
    return {"success": True}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

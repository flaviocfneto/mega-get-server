"""
FastAPI server: /api/* for React SPA + optional static files from ./static (vite dist).
"""
from __future__ import annotations

import asyncio
import json
import os
import shlex
import sys
import time
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import mega_service as ms
import tool_diagnostics as td
import transfer_metadata as tm
import ui_settings as us
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(__file__).resolve().parent / "static"
APP_STARTED = time.time()
_analytics_completed = 0
_analytics_failed = 0
_last_states: dict[str, str] = {}
# Last known byte fields per transfer tag (for inferred completion when a row vanishes from mega-transfers).
_last_row_snapshot: dict[str, dict[str, int]] = {}

_IN_FLIGHT_STATES = frozenset({"ACTIVE", "QUEUED", "RETRYING", "PAUSED"})

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
    peak_speed = 0
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
        peak_speed = max(peak_speed, sp)
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
        "peak_speed_bps": peak_speed,
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


class DownloadBody(BaseModel):
    url: str
    tags: list[str] | None = None
    priority: str | None = None


class BulkBody(BaseModel):
    tags: list[str]
    action: str
    value: Any | None = None


class TerminalBody(BaseModel):
    command: str


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


app = FastAPI(lifespan=lifespan, title="MEGA Get API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/config")
async def api_config_get():
    return _full_config()


@app.post("/api/config")
async def api_config_post(body: dict[str, Any] = Body(default_factory=dict)):
    us.merge_post_into_stored(body)
    if body.get("download_dir") is not None:
        ms.log_buffer.append("Note: download_dir is controlled by the server environment; UI value was not applied.")
    return _full_config()


@app.get("/api/account")
async def api_account():
    return await ms.get_account_info()


@app.post("/api/login")
async def api_login(body: LoginBody):
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
async def api_logout():
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


@app.post("/api/terminal")
async def api_terminal(body: TerminalBody):
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
        "mega-quit",
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


@app.get("/api/diag/commands")
async def api_diag_commands():
    return {"events": ms.get_command_events()}


@app.post("/api/diag/probe")
async def api_diag_probe():
    results = await ms.command_probe()
    return {"results": results}


@app.get("/api/diag/tools")
async def api_diag_tools():
    return td.collect_tool_diagnostics()


@app.get("/api/transfers")
async def api_transfers():
    raw = await ms.get_transfer_list()
    parsed = ms.parse_transfer_list(raw)
    rows = [ms.parsed_transfer_to_api_row(t) for t in parsed]
    _update_analytics_from_rows(rows)
    return rows


@app.get("/api/history")
async def api_history():
    return ms.get_history()


@app.delete("/api/history")
async def api_history_delete():
    ms.clear_history()
    ms.log_buffer.append("History cleared.")
    return {"success": True}


@app.get("/api/logs")
async def api_logs():
    return ms.log_buffer.get_lines()


@app.delete("/api/logs")
async def api_logs_delete():
    ms.log_buffer.clear()
    ms.log_buffer.append("Logs cleared.")
    return {"success": True}


@app.post("/api/download")
async def api_download(body: DownloadBody):
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    ms.add_url_to_history(url)

    async def job():
        await ms.run_mega_get(url)

    asyncio.create_task(job())
    return {"success": True, "message": "Download command submitted."}


@app.post("/api/transfers/cancel-all")
async def api_transfers_cancel_all():
    await ms.run_mega_transfers_cancel_all()
    return {"success": True}


@app.post("/api/transfers/bulk")
async def api_transfers_bulk(body: BulkBody):
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
async def api_transfer_update(tag: str, body: dict[str, Any] = Body(default_factory=dict)):
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
async def api_transfer_limit(tag: str, body: dict[str, Any] = Body(default_factory=dict)):
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
async def api_transfer_pause(tag: str):
    await ms.run_mega_transfers_action("pause", tag)
    return {"success": True}


@app.post("/api/transfers/{tag}/resume")
async def api_transfer_resume(tag: str):
    await ms.run_mega_transfers_resume_for_tag(tag, log_label="Resume")
    return {"success": True}


@app.post("/api/transfers/{tag}/retry")
async def api_transfer_retry(tag: str):
    await ms.run_mega_transfers_resume_for_tag(tag, log_label="Retry")
    return {"success": True}


@app.post("/api/transfers/{tag}/cancel")
async def api_transfer_cancel(tag: str):
    await ms.run_mega_transfers_action("cancel", tag)
    return {"success": True}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

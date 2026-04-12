"""Exercise api_main._execute_dispatched_queue_row and queue start-all / start-next."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

import api_main
import pending_queue as pq

SAFE_HEADERS = {"origin": "http://localhost:5173"}


@pytest.fixture
def queue_path(tmp_path, monkeypatch):
    p = tmp_path / "pending_queue.json"
    monkeypatch.setattr(pq, "QUEUE_PATH", p)
    return p


async def _run_dispatch(row: dict) -> None:
    await api_main._execute_dispatched_queue_row(row)


def test_execute_dispatched_marks_failed_when_url_invalid(queue_path):
    item = asyncio.run(pq.add_item(url="https://example.com/ok", tags=None, priority="NORMAL"))
    iid = str(item["id"])
    row = {**item, "url": "http://127.0.0.1/bad"}
    asyncio.run(_run_dispatch(row))
    got = asyncio.run(pq.get_item(iid))
    assert got is not None
    assert str(got.get("status", "")).upper() == "FAILED"


def test_execute_dispatched_mega_success_removes_queue_item(queue_path, monkeypatch):
    item = asyncio.run(pq.add_item(url="https://mega.nz/file/x", tags=["a"], priority="HIGH"))
    iid = str(item["id"])

    async def mega_ok(url, labels, pr, pending_id=None):
        assert pending_id == iid
        assert url.startswith("https://mega.nz/")
        return True, None

    monkeypatch.setattr(api_main.ms, "run_mega_get_with_user_meta", mega_ok)
    row = {"id": iid, "url": "https://mega.nz/file/x", "tags": ["a"], "priority": "HIGH"}
    asyncio.run(_run_dispatch(row))
    assert asyncio.run(pq.get_item(iid)) is None


def test_execute_dispatched_mega_failure_sets_status(queue_path, monkeypatch):
    item = asyncio.run(pq.add_item(url="https://mega.nz/file/y", tags=None, priority="NORMAL"))
    iid = str(item["id"])

    async def mega_bad(url, labels, pr, pending_id=None):
        return False, "nope"

    monkeypatch.setattr(api_main.ms, "run_mega_get_with_user_meta", mega_bad)
    row = {"id": iid, "url": "https://mega.nz/file/y", "tags": [], "priority": "NORMAL"}
    asyncio.run(_run_dispatch(row))
    got = asyncio.run(pq.get_item(iid))
    assert got is not None
    assert str(got.get("status", "")).upper() == "FAILED"


def test_execute_dispatched_http_schedules(monkeypatch, queue_path):
    scheduled: list[tuple] = []

    def capture(url, labels, pr, pending_id=None):
        scheduled.append((url, list(labels), pr, pending_id))

    monkeypatch.setattr(api_main.hd, "schedule_http_download", capture)
    item = asyncio.run(pq.add_item(url="https://example.com/bin", tags=["z"], priority="LOW"))
    iid = str(item["id"])
    row = {"id": iid, "url": "https://example.com/bin", "tags": ["z"], "priority": "LOW"}
    asyncio.run(_run_dispatch(row))
    assert scheduled
    assert scheduled[0][0].startswith("https://example.com/")
    assert scheduled[0][3] == iid


def test_queue_start_next_empty(queue_path):
    with TestClient(api_main.app) as client:
        r = client.post("/api/queue/start-next", headers=SAFE_HEADERS)
    assert r.status_code == 200
    assert r.json().get("started") is False


def test_queue_start_all_starts_pending(queue_path, monkeypatch):
    async def noop_execute(_row):
        return None

    monkeypatch.setattr(api_main, "_execute_dispatched_queue_row", noop_execute)

    with TestClient(api_main.app) as client:
        for i in range(2):
            assert client.post(
                "/api/queue",
                json={"url": f"https://mega.nz/file/{i}", "tags": [], "priority": "NORMAL"},
                headers=SAFE_HEADERS,
            ).status_code == 200
        r = client.post("/api/queue/start-all", headers=SAFE_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body.get("count", 0) >= 1


def test_config_post_logs_download_dir_note(tmp_path, monkeypatch):
    settings_path = tmp_path / "ui_settings.json"
    monkeypatch.setattr(api_main.us, "SETTINGS_PATH", settings_path)
    api_main.ms.log_buffer.clear()
    with TestClient(api_main.app) as client:
        r = client.post(
            "/api/config",
            json={"is_compact_mode": True, "download_dir": "/should-not-apply"},
            headers=SAFE_HEADERS,
        )
    assert r.status_code == 200
    assert any("download_dir" in line.lower() for line in api_main.ms.log_buffer.get_lines())


def test_transfer_pause_http_driver_returns_400_when_not_active(queue_path):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    with TestClient(api_main.app) as client:
        r = client.post(f"/api/transfers/{tag}/pause", headers=SAFE_HEADERS)
    assert r.status_code == 400


def test_bulk_http_remove_tag_updates_metadata(tmp_path, monkeypatch):
    tag = "h-550e8400-e29b-41d4-a716-446655440000"
    monkeypatch.setattr(api_main.tm, "META_PATH", tmp_path / "transfer_metadata.json")
    api_main.tm.update(tag, {"tags": ["a", "b"]})

    with TestClient(api_main.app) as client:
        r = client.post(
            "/api/transfers/bulk",
            json={"tags": [tag], "action": "remove_tag", "value": "a"},
            headers=SAFE_HEADERS,
        )
    assert r.status_code == 200
    assert api_main.tm.get(tag).get("tags") == ["b"]

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

import api_main
import pending_queue as pq

SAFE_HEADERS = {"origin": "http://localhost:5173"}


@pytest.fixture
def isolated_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(pq, "QUEUE_PATH", tmp_path / "pending_queue.json")
    yield


def test_queue_add_list_delete(isolated_queue):
    with TestClient(api_main.app) as client:
        r = client.post(
            "/api/queue",
            json={"url": "https://mega.nz/file/a", "tags": ["t1"], "priority": "HIGH"},
            headers=SAFE_HEADERS,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
        item = body.get("item")
        assert item and item.get("url") == "https://mega.nz/file/a"
        gid = item["id"]

        lst = client.get("/api/queue")
        assert lst.status_code == 200
        assert len(lst.json()) == 1

        d = client.delete(f"/api/queue/{gid}", headers=SAFE_HEADERS)
        assert d.status_code == 200


def test_queue_post_requires_csrf(isolated_queue):
    with TestClient(api_main.app) as client:
        r = client.post("/api/queue", json={"url": "https://mega.nz/file/a"})
    assert r.status_code == 403


def test_queue_rejects_bad_url(isolated_queue):
    with TestClient(api_main.app) as client:
        r = client.post("/api/queue", json={"url": "https://example.com/x"}, headers=SAFE_HEADERS)
    assert r.status_code == 400


def test_download_autostart_false_enqueues(isolated_queue):
    with TestClient(api_main.app) as client:
        r = client.post(
            "/api/download",
            json={"url": "https://mega.nz/file/z", "autostart": False},
            headers=SAFE_HEADERS,
        )
    assert r.status_code == 200
    data = r.json()
    assert data.get("queued") is True
    assert data.get("item", {}).get("url") == "https://mega.nz/file/z"


def test_queue_invalid_uuid_on_delete(isolated_queue):
    with TestClient(api_main.app) as client:
        r = client.delete("/api/queue/not-a-uuid", headers=SAFE_HEADERS)
    assert r.status_code == 400


def test_queue_start_twice_while_dispatching_returns_409(isolated_queue, monkeypatch):
    async def noop_execute(_row):
        return

    monkeypatch.setattr(api_main, "_execute_dispatched_queue_row", noop_execute)

    with TestClient(api_main.app) as client:
        r = client.post(
            "/api/queue",
            json={"url": "https://mega.nz/file/a", "tags": ["t1"], "priority": "HIGH"},
            headers=SAFE_HEADERS,
        )
        assert r.status_code == 200
        gid = r.json()["item"]["id"]

        s1 = client.post(f"/api/queue/{gid}/start", json={}, headers=SAFE_HEADERS)
        assert s1.status_code == 200
        s2 = client.post(f"/api/queue/{gid}/start", json={}, headers=SAFE_HEADERS)
        assert s2.status_code == 409
        assert s2.json().get("detail") == "Queue item is already starting"


def test_pending_queue_concurrent_adds(isolated_queue):
    async def main():
        async def add(i: int):
            await pq.add_item(url=f"https://mega.nz/file/{i}", tags=None, priority="NORMAL")

        await asyncio.gather(*(add(i) for i in range(20)))
        return await pq.list_items()

    items = asyncio.run(main())
    assert len(items) == 20

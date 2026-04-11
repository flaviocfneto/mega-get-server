from __future__ import annotations

from fastapi.testclient import TestClient

import api_main

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_login_requires_email_and_password():
    with TestClient(api_main.app) as client:
        res = client.post("/api/login", json={"email": "", "password": ""}, headers=SAFE_HEADERS)
    assert res.status_code == 400
    assert "required" in res.json()["detail"].lower()


def test_login_returns_error_when_account_not_logged(monkeypatch):
    async def fake_run(args):
        return {"ok": False, "output": "bad credentials"}

    async def fake_account():
        return {"is_logged_in": False, "email": None}

    monkeypatch.setattr(api_main.ms, "run_megacmd_command", fake_run)
    monkeypatch.setattr(api_main.ms, "get_account_info", fake_account)

    with TestClient(api_main.app) as client:
        res = client.post("/api/login", json={"email": "x@example.com", "password": "bad"}, headers=SAFE_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "error"
    assert "bad credentials" in body["message"]


def test_transfer_update_validates_priority_and_tags(monkeypatch):
    async def fake_by_tag(tag: str):
        return {"tag": tag}

    monkeypatch.setattr(api_main, "_transfer_by_tag", fake_by_tag)

    with TestClient(api_main.app) as client:
        bad_priority = client.post("/api/transfers/9/update", json={"priority": "urgent"}, headers=SAFE_HEADERS)
        bad_tags = client.post("/api/transfers/9/update", json={"tags": "one"}, headers=SAFE_HEADERS)
        no_fields = client.post("/api/transfers/9/update", json={}, headers=SAFE_HEADERS)

    assert bad_priority.status_code == 400
    assert "priority" in bad_priority.json()["detail"].lower()
    assert bad_tags.status_code == 400
    assert "tags must be an array" in bad_tags.json()["detail"]
    assert no_fields.status_code == 400


def test_transfer_update_success_persists_values(monkeypatch):
    captured = {}

    def fake_update(tag, values):
        captured["tag"] = tag
        captured["values"] = values
        return values

    async def fake_by_tag(tag: str):
        return {"tag": tag, "priority": "HIGH"}

    monkeypatch.setattr(api_main.tm, "update", fake_update)
    monkeypatch.setattr(api_main, "_transfer_by_tag", fake_by_tag)

    with TestClient(api_main.app) as client:
        res = client.post("/api/transfers/22/update", json={"priority": "high", "tags": ["a", " ", "b"]}, headers=SAFE_HEADERS)

    assert res.status_code == 200
    assert captured["tag"] == "22"
    assert captured["values"]["priority"] == "HIGH"
    assert captured["values"]["tags"] == ["a", "b"]
    assert res.json()["success"] is True


def test_transfer_limit_validates_body():
    with TestClient(api_main.app) as client:
        missing = client.post("/api/transfers/1/limit", json={}, headers=SAFE_HEADERS)
        not_int = client.post("/api/transfers/1/limit", json={"speed_limit_kbps": "abc"}, headers=SAFE_HEADERS)
        negative = client.post("/api/transfers/1/limit", json={"speed_limit_kbps": -5}, headers=SAFE_HEADERS)

    assert missing.status_code == 400
    assert not_int.status_code == 400
    assert negative.status_code == 400


def test_transfer_bulk_add_tag_and_priority_update(monkeypatch):
    store = {"7": {"tags": ["old"]}}

    def fake_get(tag):
        return store.get(tag, {})

    def fake_update(tag, values):
        row = {**store.get(tag, {}), **values}
        store[tag] = row
        return row

    monkeypatch.setattr(api_main.tm, "get", fake_get)
    monkeypatch.setattr(api_main.tm, "update", fake_update)

    with TestClient(api_main.app) as client:
        r1 = client.post("/api/transfers/bulk", json={"tags": ["7"], "action": "add_tag", "value": "new"}, headers=SAFE_HEADERS)
        r2 = client.post("/api/transfers/bulk", json={"tags": ["7"], "action": "set_priority", "value": "high"}, headers=SAFE_HEADERS)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert "new" in store["7"]["tags"]
    assert store["7"]["priority"] == "HIGH"

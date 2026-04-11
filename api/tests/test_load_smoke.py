"""Burst of sequential GETs to a read-only endpoint (MEGA_SIMULATE) — load smoke baseline."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api_main


def test_burst_config_reads_smoke(monkeypatch):
    monkeypatch.setenv("MEGA_SIMULATE", "1")
    with TestClient(api_main.app) as client:
        for _ in range(60):
            r = client.get("/api/config")
            assert r.status_code == 200

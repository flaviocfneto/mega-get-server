from __future__ import annotations
import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from api_main import app
import mega_service as ms

client = TestClient(app)

def test_redact_sensitive_text_extended():
    # Test new patterns
    assert "password=***" in ms.redact_sensitive_text("password=mysecret")
    assert "sid=***" in ms.redact_sensitive_text("sid=ABC123XYZ")
    assert "Session:***" in ms.redact_sensitive_text("Session: ABC123XYZ789")
    # JWT-like
    assert ms.redact_sensitive_text("token: abc.def.ghi") == "token: ***"
    # URL params
    assert ms.redact_sensitive_text("http://localhost?sid=secret") == "http://localhost?sid=***"

def test_run_megacmd_command_redaction(monkeypatch):
    monkeypatch.setenv("MEGA_REDACT_OUTPUT", "1")

    # Mock create_subprocess_exec to return sensitive output
    class MockProcess:
        def __init__(self, stdout, stderr):
            self.stdout = asyncio.StreamReader()
            self.stdout.feed_data(stdout)
            self.stdout.feed_eof()
            self.stderr = asyncio.StreamReader()
            self.stderr.feed_data(stderr)
            self.stderr.feed_eof()
            self.returncode = 0
        async def communicate(self):
            return await self.stdout.read(), await self.stderr.read()
        async def wait(self):
            return 0

    async def mock_create_subprocess_exec(*args, **kwargs):
        return MockProcess(b"Login successful. Session: SECRET123", b"")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_subprocess_exec)

    result = asyncio.run(ms.run_megacmd_command(["mega-whoami"]))
    assert "Session:***" in result["stdout"]
    assert "SECRET123" not in result["stdout"]

def test_run_megacmd_command_no_redaction(monkeypatch):
    monkeypatch.setenv("MEGA_REDACT_OUTPUT", "0")

    class MockProcess:
        def __init__(self, stdout, stderr):
            self.stdout = asyncio.StreamReader()
            self.stdout.feed_data(stdout)
            self.stdout.feed_eof()
            self.stderr = asyncio.StreamReader()
            self.stderr.feed_data(stderr)
            self.stderr.feed_eof()
            self.returncode = 0
        async def communicate(self):
            return await self.stdout.read(), await self.stderr.read()
        async def wait(self):
            return 0

    async def mock_create_subprocess_exec(*args, **kwargs):
        return MockProcess(b"Login successful. Session: SECRET123", b"")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_subprocess_exec)

    result = asyncio.run(ms.run_megacmd_command(["mega-whoami"]))
    assert "Session: SECRET123" in result["stdout"]

def test_terminal_mega_get_argument_count_restrictions(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")

    # 0 paths
    response = client.post(
        "/api/terminal",
        json={"command": "mega-get"},
        headers={"Origin": "http://testserver"}
    )
    assert response.json()["blocked_reason"] == "invalid_arguments"

    # 1 path
    response = client.post(
        "/api/terminal",
        json={"command": "mega-get mega:/file"},
        headers={"Origin": "http://testserver"}
    )
    assert response.json()["blocked_reason"] == "invalid_arguments"

    # 3 paths
    response = client.post(
        "/api/terminal",
        json={"command": "mega-get mega:/file1 mega:/file2 /data/out"},
        headers={"Origin": "http://testserver"}
    )
    assert response.json()["blocked_reason"] == "invalid_arguments"

    # 2 paths (correct)
    monkeypatch.setattr(ms, "SIMULATE", True)
    response = client.post(
        "/api/terminal",
        json={"command": "mega-get mega:/file /data/out"},
        headers={"Origin": "http://testserver"}
    )
    assert response.status_code == 200
    assert response.json().get("blocked_reason") is None

from __future__ import annotations

import mega_service as ms
from api_main import app
from fastapi.testclient import TestClient
from security import _rate_state

client = TestClient(app)


def test_terminal_ssrf_bypass_uppercase_scheme(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 HTTP://127.0.0.1"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_ssrf_protocol_less_localhost(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 localhost"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_ssrf_protocol_less_ip(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 127.0.0.1"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_ssrf_protocol_less_ipv6(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 [::1]"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_ssrf_protocol_less_flag_value(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 --base=127.0.0.1 http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_ssrf_protocol_less_short_flag_value(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 -B localhost http://example.com"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"


def test_terminal_ssrf_ftp_bypass(monkeypatch):
    _rate_state.clear()
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://testserver")
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", "/data")
    monkeypatch.setattr(ms, "SIMULATE", True)

    response = client.post(
        "/api/terminal",
        json={"command": "wget2 ftp://127.0.0.1"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ok"] is False
    assert "Blocked: untrusted host in URL" in data["output"]
    assert data["blocked_reason"] == "ssrf_attempt"

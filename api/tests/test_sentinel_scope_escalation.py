from __future__ import annotations

import base64
from unittest.mock import mock_open

import api_main
import mega_service as ms
from fastapi.testclient import TestClient

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_sensitive_endpoints_reject_write_scope_accept_admin_scope(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_WRITE_KEY", "write-secret")
    monkeypatch.setenv("API_ADMIN_KEY", "admin-secret")

    # Mock to avoid disk I/O and permission errors
    monkeypatch.setattr("api_main.crypt_utils.SECRET_KEY_PATH", "/tmp/fake.key")
    monkeypatch.setattr("api_main.crypt_utils.SECRETS_BIN_PATH", "/tmp/fake.bin")
    monkeypatch.setattr("api_main.crypt_utils.DEFAULT_DATA_DIR", "/tmp/data")

    # Mock os.path.exists
    monkeypatch.setattr("os.path.exists", lambda p: True if "fake.key" in p else False)

    # Mock set_vault_item
    monkeypatch.setattr("api_main.crypt_utils.set_vault_item", lambda k, v: None)

    # Mock load_vault
    monkeypatch.setattr("api_main.crypt_utils.load_vault", lambda: {"EXISTING": "VAL"})

    # Mock loading secrets into env
    monkeypatch.setattr("api_main.ms.load_secrets_into_env", lambda: None)

    endpoints = [
        ("GET", "/api/logs", None),
        ("DELETE", "/api/logs", None),
        ("GET", "/api/secrets/status", None),
        ("POST", "/api/secrets/set", {"key": "TEST_KEY", "value": "TEST_VALUE"}),
        ("POST", "/api/secrets/unlock", {"key_base64": base64.urlsafe_b64encode(b"A" * 32).decode()}),
    ]

    # Mocking the open and chmod for the unlock endpoint
    m = mock_open()
    monkeypatch.setattr("builtins.open", m)
    monkeypatch.setattr("os.chmod", lambda p, m: None)

    with TestClient(api_main.app) as client:
        for method, url, json_body in endpoints:
            # Test with write key (should be REJECTED now)
            if method == "GET":
                res = client.get(url, headers={"x-api-key": "write-secret"})
            elif method == "DELETE":
                res = client.delete(url, headers={"x-api-key": "write-secret", **SAFE_HEADERS})
            else:
                res = client.post(url, json=json_body, headers={"x-api-key": "write-secret", **SAFE_HEADERS})

            assert res.status_code == 401, f"Expected 401 for {method} {url} with write key, got {res.status_code}"

            # Test with admin key (should be ACCEPTED)
            if method == "GET":
                res = client.get(url, headers={"x-api-key": "admin-secret"})
            elif method == "DELETE":
                res = client.delete(url, headers={"x-api-key": "admin-secret", **SAFE_HEADERS})
            else:
                res = client.post(url, json=json_body, headers={"x-api-key": "admin-secret", **SAFE_HEADERS})

            assert res.status_code == 200, f"Expected 200 for {method} {url} with admin key, got {res.status_code}"


def test_redaction_hardening():
    # Test new Authorization redaction
    # Authorization header with multiple spaces
    redacted = ms.redact_sensitive_text("Authorization: Bearer   mytoken123")
    assert "Authorization: ***" in redacted
    assert "mytoken123" not in redacted

    # Standalone API key
    redacted = ms.redact_sensitive_text("x-api-key: secret-key-here")
    assert "x-api-key: ***" in redacted
    assert "secret-key-here" not in redacted

    redacted = ms.redact_sensitive_text("API-KEY: secret-key-here")
    assert "API-KEY: ***" in redacted
    assert "secret-key-here" not in redacted

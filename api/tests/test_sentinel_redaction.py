from __future__ import annotations

import os

import mega_service as ms


def test_redact_localhost_and_ips():
    assert "***" in ms.redact_sensitive_text("Connect to localhost")
    assert "***" in ms.redact_sensitive_text("Connect to 127.0.0.1")
    assert "***" in ms.redact_sensitive_text("Connect to 0.0.0.0")
    assert "***" in ms.redact_sensitive_text("Connect to ::1")
    assert "***" in ms.redact_sensitive_text("Metadata at 169.254.169.254")


def test_redact_cgnat():
    assert "100.***.***.***" in ms.redact_sensitive_text("CGNAT IP 100.64.0.1")
    assert "100.***.***.***" in ms.redact_sensitive_text("CGNAT IP 100.127.255.255")
    # Outside CGNAT
    assert "100.63.0.1" in ms.redact_sensitive_text("Public 100.63.0.1")
    assert "100.128.0.1" in ms.redact_sensitive_text("Public 100.128.0.1")


def test_redact_env_keys():
    os.environ["API_ADMIN_KEY"] = "super-secret-admin-key"
    os.environ["API_WRITE_KEY"] = "write-key-12345"

    try:
        text = "Admin key is super-secret-admin-key and write key is write-key-12345"
        redacted = ms.redact_sensitive_text(text)
        assert "super-secret-admin-key" not in redacted
        assert "write-key-12345" not in redacted
        assert redacted.count("***") >= 2
    finally:
        del os.environ["API_ADMIN_KEY"]
        del os.environ["API_WRITE_KEY"]


def test_redact_session_and_extra_headers():
    assert "session: ***" in ms.redact_sensitive_text("session: abcdef123456")
    assert "session=***" in ms.redact_sensitive_text("session=abcdef123456")
    assert "x-api-key: ***" in ms.redact_sensitive_text("x-api-key: some-key")
    assert "auth: ***" in ms.redact_sensitive_text("auth: some-token")


def test_redact_url_credentials():
    # Test that inline credentials in URLs are redacted
    raw = "Downloading from http://user:password123@example.com/file.zip"
    redacted = ms.redact_sensitive_text(raw)
    assert "password123" not in redacted
    assert "user" not in redacted
    assert "http://***@" in redacted


def test_redact_x_csrf_token():
    # Test that x-csrf-token is redacted
    raw = "x-csrf-token: abc123def456"
    redacted = ms.redact_sensitive_text(raw)
    assert "abc123def456" not in redacted
    assert "x-csrf-token: ***" in redacted


def test_redact_quoted_login():
    # Test that mega-login with quoted arguments is fully redacted
    raw = 'mega-login "user name" "pass word"'
    redacted = ms.redact_sensitive_text(raw)
    assert "user name" not in redacted
    assert "pass word" not in redacted
    assert "mega-login *** ***" in redacted

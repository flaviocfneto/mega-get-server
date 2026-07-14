from __future__ import annotations

import mega_service as ms


def test_redact_cookies():
    # Basic cookie redaction
    assert "cookie: ***" in ms.redact_sensitive_text("cookie: session=12345")
    assert "set-cookie: ***" in ms.redact_sensitive_text("set-cookie: id=abc; Path=/")

    # Quoted and JSON-style
    assert '"cookie": ***' in ms.redact_sensitive_text('{"cookie": "my-secret-cookie"}')
    assert "'set-cookie': ***" in ms.redact_sensitive_text("{'set-cookie': 'val'}")

    # Case insensitivity
    assert "Cookie: ***" in ms.redact_sensitive_text("Cookie: any-value")
    assert "Set-Cookie: ***" in ms.redact_sensitive_text("Set-Cookie: any-value")


def test_redact_link_local_range():
    # Test various IPs in the 169.254.0.0/16 range
    assert "***" in ms.redact_sensitive_text("Metadata at 169.254.169.254")
    assert "***" in ms.redact_sensitive_text("Local 169.254.0.1")
    assert "***" in ms.redact_sensitive_text("Local 169.254.255.255")

    # Should not redact other similar ranges
    assert "169.255.0.1" in ms.redact_sensitive_text("169.255.0.1")
    assert "168.254.0.1" in ms.redact_sensitive_text("168.254.0.1")


def test_redact_paths_in_json():
    # Test that paths inside JSON braces are correctly redacted without consuming the brace
    json_log = '{"file": "/etc/passwd", "status": "ok"}'
    redacted = ms.redact_sensitive_text(json_log)
    assert '"file": "/etc/***"' in redacted
    assert '"status": "ok"' in redacted

    # Test multiple paths in JSON
    json_log_multi = '{"src": "/app/code.py", "dst": "/data/backup.zip"}'
    redacted_multi = ms.redact_sensitive_text(json_log_multi)
    assert '"src": "/app/***"' in redacted_multi
    assert '"dst": "/data/***"' in redacted_multi

    # Test path at the end of a JSON object
    json_end = '{"config": "/etc/shadow"}'
    assert '"config": "/etc/***"' in ms.redact_sensitive_text(json_end)


def test_redact_paths_with_delimiters():
    # Test other delimiters including the newly added braces
    assert "(/etc/***)" in ms.redact_sensitive_text("(/etc/passwd)")
    assert "{/app/***" in ms.redact_sensitive_text("{/app/main.py}")
    # Note: the trailing slash is consumed by the [^\s'\"(){}\]]* part of the regex
    assert "=/data/*** " in ms.redact_sensitive_text("path=/data/logs/ ")

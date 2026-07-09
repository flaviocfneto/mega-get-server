from __future__ import annotations

from mega_service import redact_sensitive_text


def test_redact_google_cloud_api_key():
    key = "AIzaSyB-abcdefghijklmnopqrstuvwxyz12345"
    text = f"Found Google API key: {key}"
    redacted = redact_sensitive_text(text)
    assert key not in redacted
    assert "Found Google API key: ***" in redacted


def test_redact_github_pat():
    # ghp_ for personal access tokens
    pat = "ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD"
    text = f"Using GitHub PAT: {pat}"
    redacted = redact_sensitive_text(text)
    assert pat not in redacted
    assert "Using GitHub PAT: ***" in redacted

    # gho_ for OAuth tokens
    pat = "gho_1234567890abcdefghijklmnopqrstuvwxyzABCD"
    text = f"OAuth token: {pat}"
    redacted = redact_sensitive_text(text)
    assert pat not in redacted
    assert "OAuth token: ***" in redacted


def test_redact_csrf_xsrf_keywords():
    csrf = "abc123csrf-token-val"
    xsrf = "xyz789xsrf-token-val"
    text = f"CSRF={csrf}, XSRF={xsrf}"
    redacted = redact_sensitive_text(text)
    assert csrf not in redacted
    assert xsrf not in redacted
    assert "CSRF=***" in redacted
    assert "XSRF=***" in redacted

    # Quoted JSON-like
    text = '{"csrf_token": "secret-csrf-value", "xsrf_token": "secret-xsrf-value"}'
    redacted = redact_sensitive_text(text)
    assert "secret-csrf-value" not in redacted
    assert "secret-xsrf-value" not in redacted
    assert '"csrf_token": ***' in redacted
    assert '"xsrf_token": ***' in redacted


def test_redact_aws_secret_access_key():
    aws_secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    text = f"aws_secret_access_key={aws_secret}"
    redacted = redact_sensitive_text(text)
    assert aws_secret not in redacted
    assert "aws_secret_access_key=***" in redacted

    text = f"secret_key: {aws_secret}"
    redacted = redact_sensitive_text(text)
    assert aws_secret not in redacted
    assert "secret_key: ***" in redacted


def test_avoid_false_positives():
    # UUID should NOT be redacted
    uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    assert redact_sensitive_text(uuid_str) == uuid_str

    # Short alphanumeric strings should NOT be redacted
    short = "a1B2c3D4"
    assert redact_sensitive_text(short) == short

    # Random 40-char string NOT following AWS keyword should NOT be redacted (by that specific rule)
    # Note: it might still be redacted by the general MEGA session ID rule (40-60 chars)
    # Let's use a 39-char string to avoid that
    random_39 = "A" * 39
    assert random_39 in redact_sensitive_text(random_39)

from __future__ import annotations

from mega_service import redact_sensitive_text


def test_redact_cookies():
    # Cookie header
    text = "Cookie: sessionid=secret-session-val; csrftoken=secret-csrf-val"
    redacted = redact_sensitive_text(text)
    assert "secret-session-val" not in redacted
    assert "secret-csrf-val" not in redacted
    assert "Cookie: ***" in redacted

    # Set-Cookie header
    text = "Set-Cookie: sessionid=secret-session-val; HttpOnly; Secure"
    redacted = redact_sensitive_text(text)
    assert "secret-session-val" not in redacted
    assert "Set-Cookie: ***" in redacted

    # JSON-like cookie
    text = '{"cookie": "user_id=123; token=abc"}'
    redacted = redact_sensitive_text(text)
    assert "user_id=123" not in redacted
    assert '"cookie": ***' in redacted


def test_redact_url_credentials_advanced():
    # user@host
    text = "http://user@example.com/path"
    redacted = redact_sensitive_text(text)
    # Both user and host might be redacted (host by email rule)
    assert "user@" not in redacted
    assert "http://***@" in redacted

    # user:pass@host
    text = "https://admin:password123@internal.service/api"
    redacted = redact_sensitive_text(text)
    assert "admin:password123@" not in redacted
    assert "https://***@" in redacted

    # :pass@host
    text = "ftp://:secret@ftp.example.com"
    redacted = redact_sensitive_text(text)
    assert ":secret@" not in redacted
    assert "ftp://***@" in redacted


def test_redact_link_local_ipv4():
    text = "Connecting to 169.254.10.20 for metadata"
    redacted = redact_sensitive_text(text)
    assert "169.254.10.20" not in redacted
    assert "Connecting to 169.254.***.*** for metadata" in redacted


def test_redact_paths_in_json():
    # Path inside JSON braces
    text = '{"log_file": "/var/log/app.log"}'
    redacted = redact_sensitive_text(text)
    assert "/var/log/app.log" not in redacted
    assert '{"log_file": "/var/log/***"' in redacted

    # Path at the very end of JSON
    text = '{"workdir":"/app"}'
    redacted = redact_sensitive_text(text)
    # Note: /app is the prefix we keep but mark as masked
    assert "/app/***" in redacted


def test_redact_webhooks():
    # Discord webhook
    discord_url = "https://discord.com/api/webhooks/1234567890/my-super-secret-token"
    redacted = redact_sensitive_text(discord_url)
    assert "my-super-secret-token" not in redacted
    assert "https://discord.com/api/webhooks/1234567890/***" in redacted

    discord_url_app = "https://discordapp.com/api/webhooks/1234567890/my-super-secret-token"
    redacted_app = redact_sensitive_text(discord_url_app)
    assert "my-super-secret-token" not in redacted_app
    assert "https://discordapp.com/api/webhooks/1234567890/***" in redacted_app

    # Slack webhook
    slack_url = "https://hooks.slack.com/services/T12345_678/B12345_678/my-super-secret-token-123"
    redacted_slack = redact_sensitive_text(slack_url)
    assert "T12345_678" not in redacted_slack
    assert "B12345_678" not in redacted_slack
    assert "my-super-secret-token-123" not in redacted_slack
    assert "https://hooks.slack.com/services/***/***/***" in redacted_slack

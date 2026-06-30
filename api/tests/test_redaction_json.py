from __future__ import annotations

import mega_service as ms


def test_redact_json_secrets():
    # JSON-like log entries often contain quoted keys and values
    raw = '{"event": "login", "password": "my secret password", "user": "admin"}'
    redacted = ms.redact_sensitive_text(raw)
    assert "my secret password" not in redacted
    assert ' "password": ***' in redacted or ' "password":***' in redacted or '"password": ***' in redacted
    assert '"user": "admin"' in redacted


def test_redact_quoted_auth_header():
    # Authorization headers in JSON logs
    raw = '{"headers": {"Authorization": "Bearer some-secret-token"}}'
    redacted = ms.redact_sensitive_text(raw)
    assert "some-secret-token" not in redacted
    assert '"Authorization": ***' in redacted


def test_redact_auth_header_with_spaces():
    # Plain text logs with Authorization: Bearer ...
    raw = "Sending request with Authorization: Bearer secret.token.here"
    redacted = ms.redact_sensitive_text(raw)
    assert "secret.token.here" not in redacted
    # Note: Authorization: Bearer *** or Authorization: *** depending on match
    assert "Authorization: ***" in redacted


def test_redact_single_quotes():
    raw = "{'token': 'secret123'}"
    redacted = ms.redact_sensitive_text(raw)
    assert "secret123" not in redacted
    assert "'token': ***" in redacted

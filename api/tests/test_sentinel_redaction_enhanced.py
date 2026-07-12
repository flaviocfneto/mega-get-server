from __future__ import annotations

from mega_service import redact_sensitive_text


def test_enhanced_redaction_headers():
    # Proxy-Authorization
    assert redact_sensitive_text("Proxy-Authorization: Basic c2VjcmV0") == "Proxy-Authorization: ***"
    assert redact_sensitive_text('Proxy-Authorization: "secret"') == "Proxy-Authorization: ***"
    assert redact_sensitive_text("proxy-authorization: bearer abc.123.def") == "proxy-authorization: ***"

    # x-amz-security-token
    assert redact_sensitive_text("x-amz-security-token: fda879f87ds9f8") == "x-amz-security-token: ***"
    assert redact_sensitive_text('{"x-amz-security-token": "secret"}') == '{"x-amz-security-token": ***}'

    # x-api-token
    assert redact_sensitive_text("x-api-token: mysecret") == "x-api-token: ***"


def test_enhanced_redaction_paths():
    # New system paths
    assert "found in /proc/*** " in redact_sensitive_text("found in /proc/self/environ ")
    assert "check /tmp/*** " in redact_sensitive_text("check /tmp/secret.txt ")
    assert "under /sys/*** " in redact_sensitive_text("under /sys/class/net ")
    assert "accessing /dev/*** " in redact_sensitive_text("accessing /dev/shm ")

    # Enclosed paths
    # Note: the regex consumes up to the space or delimiter.
    # If the path is followed by a closing paren, and we used it as a delimiter,
    # it is correctly excluded from the redaction match by using [^\s'\"()\]]*.
    # Current regex: r"(?i)(^|\s|['\"(\[:=])(/app|/data|/home/mega|/root|/etc|/var/log|/tmp|/proc|/sys|/dev)(?:/|(?=[\s'\"()\]$])|$)[^\s'\"()\]]*"

    assert redact_sensitive_text("(file: /etc/passwd)") == "(file: /etc/***)"
    assert redact_sensitive_text("[path=/proc/cpuinfo]") == "[path=/proc/***]"
    assert redact_sensitive_text("'see /tmp/foo'") == "'see /tmp/***'"

    # Existing paths still work
    assert "/etc/*** " in redact_sensitive_text("cat /etc/shadow ")
    assert "/app/*** " in redact_sensitive_text("app is in /app/bin ")


def test_enhanced_redaction_regression():
    # Authorization header
    assert redact_sensitive_text("Authorization: Bearer secret") == "Authorization: ***"
    # AWS Secret Access Key
    assert redact_sensitive_text("aws_secret_access_key=1234567890123456789012345678901234567890") == (
        "aws_secret_access_key=***"
    )

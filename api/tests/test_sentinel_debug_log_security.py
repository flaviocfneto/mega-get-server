from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import mega_service as ms


def test_debug_log_redaction_and_permissions(tmp_path: Path, monkeypatch) -> None:
    # Set a custom DEBUG_LOG_PATH pointing to tmp_path
    log_file = tmp_path / "test-mega-debug.log"
    monkeypatch.setattr(ms, "DEBUG_LOG_PATH", str(log_file))

    # Trigger a debug log with sensitive information
    sensitive_data = {
        "password": "my-secret-password-1234",
        "email": "user@securehost.com",
        "webhook_url": "https://hooks.slack.com/services/T123/B456/my-slack-secret-token",
        "private_ip": "192.168.1.1",
    }

    ms._debug_log(
        location="test_security_redaction",
        message="Simulating a transaction with sensitive data",
        data=sensitive_data,
        hypothesis_id="T_SEC"
    )

    # 1. Verify that the file exists
    assert log_file.exists()

    # 2. Verify strict owner-only file permissions (0o600) on UNIX/POSIX environments
    if os.name == "posix":
        mode = log_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    # 3. Read the log content and assert sensitive fields are properly redacted
    log_content = log_file.read_text(encoding="utf-8")

    # Credentials should not be in the plaintext log file
    assert "my-secret-password-1234" not in log_content
    assert "user@securehost.com" not in log_content
    assert "my-slack-secret-token" not in log_content
    assert "192.168.1.1" not in log_content

    # Key keywords or patterns should be masked with asterisks
    assert "***" in log_content

    # Ensure it's still valid JSON per line
    lines = log_content.strip().split("\n")
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["location"] == "test_security_redaction"
    assert "test_security_redaction" in log_content

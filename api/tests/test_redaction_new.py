from __future__ import annotations
import mega_service as ms

def test_redact_ips():
    assert "10.***.***.***" in ms.redact_sensitive_text("Connect to 10.0.0.5")
    assert "172.***.***.***" in ms.redact_sensitive_text("Host 172.16.0.10 is up")
    assert "192.168.***.***" in ms.redact_sensitive_text("Router at 192.168.1.1")
    assert "f***:***" in ms.redact_sensitive_text("IPv6 addr: fd00::1")
    # Public IPs should not be redacted (this regex is simple so it might have false positives, but let's check basic ones)
    assert "1.1.1.1" in ms.redact_sensitive_text("1.1.1.1")
    assert "8.8.8.8" in ms.redact_sensitive_text("8.8.8.8")

def test_redact_paths():
    assert "/app/*** " in ms.redact_sensitive_text("/app/api_main.py is starting")
    assert "/data/*** " in ms.redact_sensitive_text("File saved to /data/myfile.zip ")
    assert "/home/mega/*** " in ms.redact_sensitive_text("Home is /home/mega/.bashrc ")
    assert "/root/*** " in ms.redact_sensitive_text("Logged as /root/admin ")
    assert "/etc/*** " in ms.redact_sensitive_text("Config in /etc/passwd ")
    assert "/var/log/*** " in ms.redact_sensitive_text("Logs are in /var/log/syslog ")

    # Relative paths or other paths should not be redacted
    assert "./local/path" in ms.redact_sensitive_text("./local/path")
    assert "Downloads/folder" in ms.redact_sensitive_text("Downloads/folder")

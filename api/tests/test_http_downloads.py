from __future__ import annotations

import pytest

import http_downloads as hd
import mega_service as ms


def test_normalize_download_url_mega():
    kind, u = hd.normalize_download_url("https://mega.nz/file/abc")
    assert kind == "mega"
    assert "mega.nz" in u


def test_normalize_download_url_http():
    kind, u = hd.normalize_download_url("https://example.com/file.bin")
    assert kind == "http"
    assert u == "https://example.com/file.bin"


def test_validate_http_rejects_mega_host():
    with pytest.raises(ValueError):
        hd.validate_http_download_url("https://mega.nz/file/x")


def test_validate_http_rejects_loopback():
    with pytest.raises(ValueError):
        hd.validate_http_download_url("http://127.0.0.1/x")


def test_validate_http_rejects_private_ip():
    with pytest.raises(ValueError):
        hd.validate_http_download_url("http://10.0.0.1/x")


def test_parse_wget_stderr_progress():
    pct, _ = hd.parse_wget_stderr_progress("  45% [............] ")
    assert pct == 45.0


def test_http_download_argv_wget2_flags(monkeypatch):
    monkeypatch.delenv("WGET_HTTP_BIN", raising=False)
    argv = hd._http_download_argv("/usr/bin/wget2", "https://example.com/a.bin", "/data/out.bin", 0)
    assert argv[0] == "/usr/bin/wget2"
    assert argv[1] == "-q"
    assert "--force-progress" in argv
    assert "--progress=bar:force" in argv
    assert "--http2" in argv
    assert "--compression=gzip,deflate,br" in argv
    assert "--show-progress" not in argv
    assert argv[-1] == "https://example.com/a.bin"


def test_http_download_argv_limit_rate_after_quiet(monkeypatch):
    monkeypatch.delenv("WGET_HTTP_BIN", raising=False)
    argv = hd._http_download_argv("/bin/wget2", "https://x/y", "/o", 800)
    i_q = argv.index("-q")
    assert argv[i_q + 1].startswith("--limit-rate=")


def test_is_http_driver_tag():
    assert hd.is_http_driver_tag("h-550e8400-e29b-41d4-a716-446655440000") is True
    assert hd.is_http_driver_tag("h-not-uuid") is False
    assert hd.is_http_driver_tag("12") is False


def test_safe_unlink_job_paths_under_download_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    f = tmp_path / "partial.bin"
    f.write_bytes(b"x")
    hd.safe_unlink_job_paths([str(f)])
    assert not f.is_file()


def test_safe_unlink_skips_outside_download_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "DOWNLOAD_DIR", str(tmp_path))
    outside = tmp_path.parent / "evil.txt"
    outside.write_text("nope")
    hd.safe_unlink_job_paths([str(outside)])
    assert outside.is_file()

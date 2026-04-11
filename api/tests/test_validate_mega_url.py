from __future__ import annotations

import pytest

import mega_service as ms


def test_validate_mega_download_url_strips():
    assert ms.validate_mega_download_url("  https://mega.nz/file/x  ") == "https://mega.nz/file/x"


def test_validate_mega_download_url_rejects_non_mega_host():
    with pytest.raises(ValueError, match="MEGA"):
        ms.validate_mega_download_url("https://evil.com/x")


def test_validate_mega_download_url_rejects_bad_scheme():
    with pytest.raises(ValueError, match="http"):
        ms.validate_mega_download_url("file:///etc/passwd")


def test_validate_mega_download_url_requires_non_empty():
    with pytest.raises(ValueError, match="URL"):
        ms.validate_mega_download_url("  ")

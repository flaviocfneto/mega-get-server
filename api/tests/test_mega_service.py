"""Smoke tests for mega_service helpers (no MEGAcmd required)."""

import mega_service as ms


def test_size_display_to_bytes_gb():
    assert ms.size_display_to_bytes("3.54 GB") > 1024**3


def test_size_display_to_bytes_unknown():
    assert ms.size_display_to_bytes("Unknown") == 0
    assert ms.size_display_to_bytes("") == 0


def test_parsed_transfer_to_api_row_unknown_size():
    row = ms.parsed_transfer_to_api_row(
        {
            "tag": "1",
            "progress_pct": 50.0,
            "state": "ACTIVE",
            "path": "/x/a.zip",
            "filename": "a.zip",
            "size_display": "Unknown",
        }
    )
    assert row["size_bytes"] == 0
    assert row["downloaded_bytes"] == 0
    assert row["progress_pct"] == 50.0
    assert row["url"] == ""
    assert row["speed_bps"] == 0
    assert row["priority"] == "NORMAL"

"""Smoke tests for mega_service helpers (no MEGAcmd required)."""

import mega_service as ms


def test_size_display_to_bytes_gb():
    assert ms.size_display_to_bytes("3.54 GB") > 1024**3


def test_size_display_to_bytes_unknown():
    assert ms.size_display_to_bytes("Unknown") == 0
    assert ms.size_display_to_bytes("") == 0


def test_normalize_transfer_state_maps_finished():
    assert ms.normalize_transfer_state("FINISHED") == "COMPLETED"
    assert ms.normalize_transfer_state("ACTIVE") == "ACTIVE"


def test_summarize_transfer_parse():
    raw = "line1\n\n  line2  \n"
    s = ms.summarize_transfer_parse(raw, [])
    assert s["nonempty_line_count"] == 2
    assert s["parsed_count"] == 0
    assert s["raw_char_len"] == len(raw)


def test_parse_transfer_list_ascii_arrow_with_of_clause():
    raw = "v    12  /data/file.zip  10.0%  of  100 MB  ACTIVE\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "12"
    assert rows[0]["state"] == "ACTIVE"
    assert rows[0]["size_display"] == "100 MB"


def test_parse_transfer_list_ascii_relaxed_without_of():
    raw = "^    3  /upload/a.bin  99.0%  COMPLETING\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "3"
    assert rows[0]["progress_pct"] == 99.0


def test_parse_transfer_list_download_keyword_line():
    raw = "DOWNLOAD 5 ACTIVE 25.5% /tmp/a.bin\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "5"
    assert rows[0]["state"] == "ACTIVE"


def test_parse_transfer_list_path_may_contain_state_substring():
    raw = "7 ACTIVE 1% /Volumes/STATE_drive/file.zip\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "7"


def test_parse_transfer_list_relaxed_line_without_of_clause():
    raw = "⇓    9999  /Downloads/x.iso  50.0%  ACTIVE\n"
    rows = ms.parse_transfer_list(raw)
    assert len(rows) == 1
    assert rows[0]["tag"] == "9999"
    assert rows[0]["state"] == "ACTIVE"
    assert rows[0]["size_display"] == "Unknown"


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


def test_parsed_transfer_to_api_row_normalizes_state():
    row = ms.parsed_transfer_to_api_row(
        {
            "tag": "1",
            "progress_pct": 100.0,
            "state": "FINISHED",
            "path": "/x/a.zip",
            "filename": "a.zip",
            "size_display": "10 MB",
        }
    )
    assert row["state"] == "COMPLETED"


def test_parse_mega_df_bandwidth_labeled_lines():
    txt = """
Storage used: 100 bytes
Storage total: 1000 bytes
Bandwidth used: 200 bytes
Bandwidth quota: 500 bytes
"""
    su, st, bu, bl, ok = ms._parse_mega_df_bytes_and_bw(txt)
    assert ok is True
    assert (su, st) == (100, 1000)
    assert (bu, bl) == (200, 500)


def test_parse_mega_df_bandwidth_of_format():
    txt = """
Storage used: 100 bytes
Storage total: 1000 bytes
Transfer quota: 250 bytes of 400 bytes
"""
    su, st, bu, bl, ok = ms._parse_mega_df_bytes_and_bw(txt)
    assert ok is True
    assert (su, st) == (100, 1000)
    assert (bu, bl) == (250, 400)

from __future__ import annotations

from api_main import app
from fastapi.testclient import TestClient


def test_csp_frame_ancestors_none():
    """
    Verify that the Content-Security-Policy header includes frame-ancestors 'none'
    for enhanced clickjacking protection (modern alternative to X-Frame-Options).
    """
    with TestClient(app) as client:
        # /api/config is a simple endpoint to check headers
        response = client.get("/api/config")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "frame-ancestors 'none'" in csp

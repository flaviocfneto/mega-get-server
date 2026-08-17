from __future__ import annotations

from api_main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_api_cache_control_headers():
    """
    Verify that API responses include Cache-Control and Pragma security headers
    to prevent browser/proxy caching of sensitive user data and server state.
    """
    response = client.get("/api/diag/tools")
    assert response.headers.get("Cache-Control") == "no-store, no-cache, must-revalidate"
    assert response.headers.get("Pragma") == "no-cache"


def test_non_api_cache_control_headers():
    """
    Verify that non-API routes (or root requests) do not get forced API Cache-Control headers.
    """
    response = client.get("/")
    # Check that Cache-Control is not overridden for non-api endpoints if they return static/404
    assert response.headers.get("Pragma") is None or response.headers.get("Pragma") != "no-cache"

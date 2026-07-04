from __future__ import annotations

from api_main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

def test_security_headers_enhancement():
    """
    Verify that the enhanced security headers are present in the response.
    """
    # Use a public endpoint or any endpoint that doesn't require complex setup
    response = client.get("/api/diag/tools")

    # Check for basic headers that should still be there
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # Check for new/enhanced headers
    assert response.headers.get("X-XSS-Protection") == "0"

    permissions_policy = response.headers.get("Permissions-Policy")
    assert "camera=()" in permissions_policy
    assert "microphone=()" in permissions_policy
    assert "geolocation=()" in permissions_policy
    assert "payment=()" in permissions_policy
    assert "usb=()" in permissions_policy
    assert "bluetooth=()" in permissions_policy

    csp = response.headers.get("Content-Security-Policy")
    assert "default-src 'self'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp
    assert "object-src 'none'" in csp
    # Verify nonces are present for script and style
    assert "script-src 'self' 'nonce-" in csp
    assert "style-src 'self' 'nonce-" in csp

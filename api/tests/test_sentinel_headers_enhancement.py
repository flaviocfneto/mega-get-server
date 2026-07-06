from __future__ import annotations

from api_main import app
from fastapi.testclient import TestClient

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

    # Check for defense-in-depth headers
    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
    assert response.headers.get("X-Permitted-Cross-Domain-Policies") == "none"
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert response.headers.get("X-Download-Options") == "noopen"


def test_csp_connect_src_sanitization(monkeypatch):
    """
    Verify that connect-src is sanitized to prevent directive injection.
    """
    # Inject a semicolon into CORS_ALLOW_ORIGINS to attempt directive injection
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:5173; script-src 'unsafe-inline'")

    response = client.get("/api/diag/tools")
    csp = response.headers.get("Content-Security-Policy")

    # The injected script-src should be sanitized away
    assert "connect-src 'self' http://localhost:5173script-src" in csp
    # Semicolon should NOT be in the CSP for that origin
    assert "http://localhost:5173;" not in csp

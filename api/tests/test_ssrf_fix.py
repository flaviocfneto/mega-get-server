from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import http_downloads as hd
import pytest


def test_host_is_blocked_resolves_local(monkeypatch):
    # Mock socket.getaddrinfo to return a local IP for a "public" looking domain
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "evil-local.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
        return socket.getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    assert hd._host_is_blocked("evil-local.com") is True


def test_host_is_blocked_allows_public(monkeypatch):
    # Mock socket.getaddrinfo to return a public IP
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "safe-public.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]
        return socket.getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    assert hd._host_is_blocked("safe-public.com") is False


def test_host_is_blocked_handles_unresolvable():
    assert hd._host_is_blocked("this-does-not-exist.invalid") is True


@pytest.mark.asyncio
async def test_resolve_and_validate_url_scheme_bypass():
    # Mocking urllib.request.build_opener to return a redirect to ftp:// on first call.
    mock_resp_redirect = MagicMock()
    mock_resp_redirect.status = 302
    mock_resp_redirect.headers = {"Location": "ftp://1.1.1.1/evil"}
    mock_resp_redirect.__enter__.return_value = mock_resp_redirect

    mock_opener = MagicMock()
    mock_opener.open.return_value = mock_resp_redirect

    with patch("urllib.request.build_opener", return_value=mock_opener):
        final_url, cl = await hd._resolve_and_validate_url("http://attacker.com/redirect")

        # After fix, it should return None, None because ftp:// is not http/https
        assert final_url is None
        assert cl is None

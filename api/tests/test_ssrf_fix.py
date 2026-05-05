from __future__ import annotations

import socket

import http_downloads as hd


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

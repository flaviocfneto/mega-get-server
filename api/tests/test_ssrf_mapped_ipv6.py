from __future__ import annotations

import ipaddress

from http_downloads import _host_is_blocked


def test_ipv4_mapped_ipv6_is_global():
    # Test common IPv4-mapped IPv6 address for localhost
    ip = ipaddress.ip_address("::ffff:127.0.0.1")
    print(f"\nIP: {ip}")
    print(f"is_global: {ip.is_global}")
    print(f"is_private: {ip.is_private}")
    print(f"is_loopback: {ip.is_loopback}")

    # If this prints is_global: True and is_private: False, then our SSRF check might be bypassable
    # if it only checks these properties.


def test_host_is_blocked_mapped_ipv6():
    # This should be blocked
    assert _host_is_blocked("::ffff:127.0.0.1") is True
    assert _host_is_blocked("::ffff:192.168.1.1") is True

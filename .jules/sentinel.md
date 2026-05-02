## 2025-05-15 - [SSRF via DNS Resolution and Path Traversal in Admin Terminal]
**Vulnerability:**
1. SSRF: The application allowed downloading from arbitrary HTTP(S) URLs and only blocked private IP addresses when provided directly. It didn't resolve hostnames, allowing attackers to use domains pointing to internal IPs.
2. Path Traversal: The admin terminal allowed `mega-get` to write files to arbitrary locations on the filesystem, potentially overwriting sensitive files.

**Learning:**
1. Always resolve hostnames before validating IP addresses for SSRF prevention. Multiple IPs for a single host should all be checked.
2. Even in admin-restricted endpoints, it's crucial to apply the principle of least privilege. An admin terminal should still be constrained by the application's intended operational boundaries (like `DOWNLOAD_DIR`).

**Prevention:**
1. Use `socket.getaddrinfo` to resolve and validate all IP addresses for a given hostname against a blocklist of private/reserved ranges.
2. Implement path validation and normalization (e.g., `os.path.abspath`) for all user-provided file paths, even in administrative tools.

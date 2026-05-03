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

## 2025-05-16 - [Path Traversal via Default CWD in mega-get]
**Vulnerability:**
MEGAcmd's `mega-get` command defaults to downloading files into the current working directory (CWD) if no local path is specified. In the server context, this allowed users to download files directly into the `/app` directory, potentially overwriting application source code or sensitive configuration.

**Learning:**
Application-level path traversal checks must account for default behaviors of underlying tools. Even if explicit paths are validated, "no path" can be equally dangerous if it implies an insecure default.

**Prevention:**
Always enforce explicit, absolute, and validated destination paths when invoking external download tools from the backend.

## 2026-05-03 - [Exposure of Sensitive Data in Command Output and Ambiguous Terminal Arguments]
**Vulnerability:**
1. MEGAcmd command outputs (stdout/stderr) were recorded and returned via API without redaction, potentially leaking session IDs or login details.
2. The admin terminal's `mega-get` implementation allowed for ambiguous argument counts, which could be exploited to bypass path traversal checks if multiple remote/local paths were provided.

**Learning:**
1. Redacting command arguments is insufficient if the tool's output itself contains echoed secrets or session-specific tokens. Redaction must be applied to the entire execution lifecycle (input AND output) in production.
2. Strict argument count validation (e.g., requiring exactly N paths) is a powerful defense-in-depth measure against command-line ambiguity and bypass attempts.

**Prevention:**
1. Implement a centralized command execution wrapper that applies multi-pattern regex redaction to all output streams by default.
2. In administrative interfaces, strictly parse and validate the number of positional arguments for critical commands to ensure validation logic cannot be confused by unexpected inputs.

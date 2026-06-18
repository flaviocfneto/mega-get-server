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

## 2026-05-04 - [Comprehensive Security Hardening: CSRF, SSRF, Redaction, Terminal, and CSP]
**Vulnerability:**
1. CSRF: The `origin_plus_token` mode only checked for header presence, not token validity.
2. SSRF: Redirects were not validated against private IP blocklists.
3. Sensitive Data: MEGA session IDs and AWS keys were not fully redacted.
4. Terminal: Administrative commands like `mega-ls` had no character-level hardening against injection.
5. CSP: Overly permissive `unsafe-inline` policy.

**Learning:**
1. CSRF protection must link the request header to a client-side secret (cookie) to be effective against cross-site attacks.
2. SSRF protection is incomplete if redirects are followed by the underlying tool without re-validating the target IP.
3. Defense-in-depth requires hardening even administrative interfaces against shell metacharacters, even when using `shlex`.

**Prevention:**
1. Use a double-submit cookie pattern for CSRF validation.
2. Manually follow and validate redirects before passing URLs to external downloaders.
3. Block shell metacharacters in administrative command inputs.
4. Enforce strict CSP by removing `unsafe-inline`.

## 2026-05-03 - [CSRF Referer Bypass and Terminal Hardening]
**Vulnerability:**
1. CSRF Referer Bypass: The CSRF check used `referer.startswith(allowed)`, which could be bypassed by an attacker using a domain that starts with the trusted origin (e.g., `http://localhost:5173.attacker.com`).
2. Administrative Endpoint Exposure: The `/api/logs` endpoint was missing authentication and rate limiting, allowing unauthorized access to sensitive server activity.
3. Terminal Injection Surface: The terminal command character blacklist was missing common shell metacharacters like $\, \(\), and \.

**Learning:**
1. String prefix checks are insufficient for URL-based security validation; exact origin matching (scheme + netloc) is required.
2. Administrative and diagnostic endpoints should follow the same security protocols (authentication, authorization, rate limiting) as functional API endpoints.
3. Defense-in-depth for command execution should include character-level blacklisting even when using supposedly safe APIs like `shlex.split` and `create_subprocess_exec`.

**Prevention:**
1. Always parse URLs and compare origins (scheme + host + port) for security-critical domain validation.
2. Ensure every API endpoint has appropriate scope dependencies and rate limits.
3. Maintain a comprehensive list of restricted shell metacharacters for any interface that executes system commands.

## 2026-05-05 - [Terminal Path Confusion and Secure Webhook SSRF]
**Vulnerability:**
1. Terminal Path Confusion: Attempting to harden local filesystem access in MEGAcmd terminal commands can inadvertently block standard remote MEGA paths (which also start with '/') if the heuristic for distinguishing them is too broad.
2. Webhook SSRF: Saving a webhook URL in settings is insufficient; SSRF protection must also be applied at the moment of execution to prevent bypasses if the target resolves to a restricted IP at runtime or if the URL was manipulated.
3. CSRF suppression: Allowing state-changing requests without both Origin and Referer headers (to accommodate CLI clients) creates a risk if a browser-based attack can suppress these headers.

**Learning:**
1. In tools like MEGAcmd where remote and local path syntax overlaps, path validation must use specific heuristics (e.g., checking for standard remote roots like /Root, /Bin, /Incoming) to avoid breaking core functionality while still blocking local traversal (e.g., ../).
2. Defense-in-depth for webhooks requires validating the hostname against a blocklist IMMEDIATELY before sending the request, disabling redirects, and using strict timeouts.
3. For applications primarily served as a web SPA, enforcing the presence of either Origin or Referer for all mutating requests is a safer default.

**Prevention:**
1. Implement context-aware path validation that identifies and permits expected remote path patterns before applying strict local filesystem traversal checks.
2. Use a dedicated webhook service that encapsulates SSRF protection logic (host validation, redirect suppression) and is called by the application's event loop.
3. Set a strict CSRF policy that requires security headers for all state-changing methods, rejecting requests where both Origin and Referer are absent.

## 2026-05-06 - [Terminal Flag Bypass and Default Insecurity]
**Vulnerability:**
1. Terminal Flag Bypass: Hardening only non-flag arguments allowed attackers to use flags like `--output-document=/etc/passwd` or `-O /etc/passwd` in `wget2` to bypass path traversal checks.
2. SSRF in Terminal: While generic downloads were protected, the administrative terminal allowed `wget2` to hit internal/private IP ranges.
3. Insecure Defaults: `API_AUTH_MODE` defaulted to `optional`, leaving the API open if not explicitly configured.
4. Secret Key Injection: Lack of validation on secret keys allowed characters that could lead to shell injection when exported via `decrypt_env.py`.

**Learning:**
1. Defense-in-depth for terminal wrappers must inspect ALL command tokens. Attackers will use standard tool options (flags) to provide malicious paths or targets that are ignored by heuristics looking only at positional arguments.
2. "Secure by Default" is a critical principle; fallbacks for authentication modes should always lean toward the most restrictive state.
3. Any user input that eventually ends up being evaluated in a shell context (like environment variable names) MUST be strictly validated against a whitelist of safe characters (e.g., `[a-zA-Z0-9_]`).

**Prevention:**
1. Iterate over every token in a command and apply both SSRF (for URL-like tokens) and Path Traversal (for path-like tokens, including flag values after `=`) checks.
2. Set default security modes to `strict`.
3. Use Pydantic patterns to enforce strict character sets for keys and identifiers.

## 2026-05-04 - [Defense in Depth: SSRF, Redaction, and Dependency Pinning]
**Vulnerability:**
1. IPv6 SSRF: SSRF protection was missing explicit checks for IPv6 Unique Local Addresses (ULA) and site-local ranges.
2. Configuration Leakage: The `GET /api/config` endpoint was accessible without authentication in strict mode, leaking internal filesystem paths.
3. Insufficient Redaction: Internal IP addresses and sensitive app/system paths (e.g., `/app`, `/etc`) were exposed in log buffers.
4. Tool Integrity: External dependencies like `wget2` were installed without version pinning or checksum verification in the Dockerfile.

**Learning:**
1. SSRF blocklists must be protocol-agnostic and explicitly cover all reserved ranges for both IPv4 and IPv6.
2. Diagnostic and configuration endpoints are high-value targets for reconnaissance; they should require authorization even for read-only access in hardened environments.
3. Redaction should cover not just secrets, but any infrastructure details (IPs, paths) that aid an attacker in mapping the internal environment.
4. Supply chain security requires pinning and verifying every external binary introduced at build time.

**Prevention:**
1. Use `ipaddress` library to check for `is_private`, `is_site_local`, and specific ULA prefixes (fc00::/7) during SSRF validation.
2. Apply scope-based dependency checks to all API endpoints that return environment-specific data.
3. Maintain a comprehensive list of infrastructure patterns for log redaction.
4. Pin external tool versions and verify them with SHA256 checksums in the Dockerfile.

## 2024-05-22 - [Case-Insensitive SSRF and Timing Attacks]
**Vulnerability:**
1. SSRF bypass: Protocol scheme checks (e.g. `startswith("http://")`) were case-sensitive, allowing bypass via uppercase schemes like `HTTP://`.
2. Timing attack: API key validation used standard `==` string comparison.
3. Log leakage: `Authorization: Basic` headers were not redacted in logs.

**Learning:**
1. Security validation of URLs must be case-insensitive for schemes.
2. Constant-time comparison is essential for verifying secrets to prevent timing side-channels.
3. Redaction filters should cover both modern (Bearer) and legacy (Basic) authentication patterns.

**Prevention:**
1. Normalize input to lowercase before prefix-based protocol validation.
2. Use `secrets.compare_digest` for all cryptographic or security-critical string comparisons.
3. Regularly audit and expand redaction regex patterns to cover common authentication headers.

## 2026-05-07 - [Context-Specific Terminal Heuristics and Proactive Redaction]
**Vulnerability:**
1. Terminal Heuristic Leakage: Remote path heuristics (e.g., skipping validation for paths starting with '//') intended for MEGAcmd were being applied to generic tools like 'wget2', allowing attackers to access local paths via '//etc/passwd'.
2. Reactive Redaction: Sensitive data was being stored in the in-memory log buffer unredacted, only being masked when served via the API. This left secrets exposed in memory.
3. Incomplete SSRF Blocklist: Obscure non-global IP ranges like CGNAT (100.64.0.0/10) were missing from the manual blocklist.

**Learning:**
1. Security heuristics must be scoped to the specific command context. What is a "safe" remote path for one tool is a "dangerous" local path for another.
2. Defense-in-depth requires redacting sensitive information at the point of ingestion (proactive) rather than just at the point of display (reactive) to minimize the window of exposure in RAM.
3. Leverage built-in library properties like 'ipaddress.IPv4Address.is_global' for comprehensive SSRF protection instead of manually maintaining blocklists of reserved ranges.

**Prevention:**
1. Apply command-specific validation logic in terminal wrappers.
2. Implement redaction in the logging service's storage method.
3. Use 'is_global' to block all non-routable/reserved IP addresses in SSRF checks.

## 2026-06-16 - [Missing Authentication on History and Queue Endpoints]
**Vulnerability:**
The `GET /api/history` and `GET /api/queue` endpoints were accessible without authentication even when `API_AUTH_MODE` was set to 'strict'. This allowed unauthorized users to view download history and the pending queue, which may contain sensitive metadata like filenames and source URLs.

**Learning:**
Security audits should verify that ALL endpoints returning user-specific or system-state data are consistently protected by the application's authentication middleware. It is easy to overlook read-only GET endpoints when focusing on state-changing POST/DELETE operations.

**Prevention:**
Enforce a "secure by default" policy where all endpoints in a specific path prefix (e.g., `/api/*`) require authentication unless explicitly marked as public. In FastAPI, this can be achieved by adding dependencies to the APIRouter or the main app instance.

## 2024-06-16 - [Shell Injection in Decrypt Env and Terminal Flag Bypass]
**Vulnerability:**
1. Shell Injection: `api/decrypt_env.py` used manual single-quote escaping (`replace("'", "'\\''")`) which is insufficient when the resulting string is evaluated by a shell in an `eval $(...)` context, especially if the value contains newlines or other shell-sensitive characters.
2. Path Traversal Bypass: The terminal's path validation only looked for `=` in flags or separate arguments. It missed paths attached directly to short flags (e.g., `-O/etc/passwd`), allowing attackers to specify output files outside the permitted directory.

**Learning:**
1. Never implement manual shell escaping. The `shlex.quote()` function in the Python standard library is the only reliable way to escape strings for POSIX shells.
2. Command-line parsers are complex. When hardening a terminal wrapper, you must account for all ways a tool might accept a path, including attached short flags, which are common in tools like `wget`, `wget2`, and `curl`.

**Prevention:**
1. Use `shlex.quote()` for all data intended for shell evaluation.
2. Robustly parse CLI arguments by checking for attached values in known short flags (e.g., `-O`, `-o`) when performing path-based security validation.

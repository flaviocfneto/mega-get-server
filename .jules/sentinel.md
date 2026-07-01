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

## 2026-06-29 - [Insecure Configuration Update via Generic Dictionaries]
**Vulnerability:**
The `/api/config` endpoint accepted arbitrary JSON dictionaries without validation. This allowed attackers (with 'write' scope) to set configuration values to extreme ranges (e.g., millions of retries) or provide massive strings for webhook URLs, potentially leading to resource exhaustion, application instability, or bypassing intended UI limits.

**Learning:**
Generic dictionary input in state-changing API endpoints is a security risk even with authentication. Defense-in-depth requires strict schema validation at the API entry point (e.g., Pydantic models) AND consistent enforcement in the underlying storage/service layers to ensure system invariants are maintained regardless of the input vector.

**Prevention:**
1. Always use structured Pydantic models for POST/PUT/PATCH request bodies to enforce type safety, numeric ranges, string length limits, and format validation (e.g., regex for time strings).
2. Use `model_dump(exclude_unset=True)` to support partial updates safely.
3. Implement secondary validation in the service layer (e.g., `ui_settings.py`) to protect against internal misuse or future API regressions.

## 2026-06-16 - [Missing Authentication on History and Queue Endpoints]
**Vulnerability:**
The `GET /api/history` and `GET /api/queue` endpoints were accessible without authentication even when `API_AUTH_MODE` was set to 'strict'. This allowed unauthorized users to view download history and the pending queue, which may contain sensitive metadata like filenames and source URLs.

**Learning:**
Security audits should verify that ALL endpoints returning user-specific or system-state data are consistently protected by the application's authentication middleware. It is easy to overlook read-only GET endpoints when focusing on state-changing POST/DELETE operations.

**Prevention:**
Enforce a "secure by default" policy where all endpoints in a specific path prefix (e.g., `/api/*`) require authentication unless explicitly marked as public. In FastAPI, this can be achieved by adding dependencies to the APIRouter or the main app instance.

## 2024-05-23 - [Incomplete Defense-in-Depth for Shell Exports]
**Vulnerability:**
The `decrypt_env.py` script and `ft_setup.py` CLI tool lacked strict validation for secret keys, which were later used in a shell `eval` context. While the web API enforced safe key patterns, an attacker could use the CLI or manipulate the encrypted vault to inject shell commands via malicious key names (e.g., `VAR='v'; pwned;`).

**Learning:**
Defense-in-depth requires consistent validation across ALL input vectors (API, CLI, and direct file manipulation). Furthermore, manual string escaping for shell consumption is error-prone; standard library functions like `shlex.quote` should always be preferred.

**Prevention:**
1. Apply strict regex validation (`^[a-zA-Z_][a-zA-Z0-9_]*$`) to all identifiers used in shell commands or environment variable exports.
2. Use `shlex.quote()` for all values being passed to a shell context to ensure robust escaping.

## 2024-05-24 - [Terminal Bypass via Attached Flags and Embedded URLs]
**Vulnerability:**
1. Path Traversal Bypass: Short flags in CLI tools like `wget2` (e.g., `-O/path`) can have values attached directly without a space or `=`. Standard heuristics that only checked for `=` or positional arguments missed these.
2. SSRF Bypass: URLs can be embedded within flags (e.g., `--base=http://...`). A simple `startswith` check on the argument failed to detect these.

**Learning:**
1. Heuristics for command-line security must account for the flexible syntax of CLI flags. Both attached short flags and flag values following `=` are common vectors for providing sensitive paths or URLs.
2. Protocol detection for SSRF must be performed on the entire argument string, not just the prefix, to ensure no embedded URLs bypass validation.

**Prevention:**
1. Implement flag-aware parsing that explicitly checks for and extracts values from attached short flags (e.g., `-O`, `-o`).
2. Scan the entire argument for protocol prefixes (`http://`, `https://`, `ftp://`) to detect and validate any embedded URLs.

## 2024-05-25 - [Terminal Heuristic Bypass via Double Slashes]
**Vulnerability:**
The administrative terminal allowed `mega-*` commands to bypass local path traversal checks if a path started with `//`. This heuristic was intended to identify remote MEGA paths, but since most Unix-like systems resolve `//` to `/`, it could be used to access arbitrary local files (e.g., `mega-get /Root/file //etc/passwd`).

**Learning:**
Heuristics that grant security exemptions (like skipping validation for "remote" paths) must be extremely narrow. If a "safe" pattern overlaps with a "dangerous" one due to OS-level normalization, it becomes a bypass vector.

**Prevention:**
1. Avoid using broad prefixes like `//` as a sole indicator of "remoteness" if the underlying system might treat it as a local root.
2. Subject all paths to validation against allowed directories (like `DOWNLOAD_DIR`) unless they match a strictly defined and non-overlapping remote pattern (e.g., `/Root`, `/Bin`).

## 2024-05-26 - [Terminal Heuristic Bypass via Directory Traversal in Remote Paths]
**Vulnerability:**
The administrative terminal's MEGAcmd path heuristics allowed any path starting with `/Root`, `/Bin`, or `/Incoming` to bypass local filesystem traversal checks. This enabled attackers to access arbitrary local files by using these prefixes followed by directory traversal sequences (e.g., `mega-ls /Root/../etc`).

**Learning:**
Heuristics that exempt specific input patterns from security checks must be extremely defensive. In this case, simply checking for a "safe" prefix was insufficient because the OS still resolves `..` regardless of the prefix, allowing escape from the intended "remote" context.

**Prevention:**
Always validate that "safe" patterns do not contain malicious sequences like `..` even if they match a trusted prefix. When a path is intended for a specific remote namespace, enforce that it remains within that namespace by forbidding traversal markers.

## 2025-05-27 - [Terminal Path Traversal Bypass via CWD and Incomplete Argument Validation]
**Vulnerability:**
1. The administrative terminal only performed path traversal checks on arguments that appeared to be paths (containing slashes or being absolute). This allowed bypasses using filename-only arguments (e.g., `wget2 -O myfile.txt ...`) which would be written to the server's current working directory (CWD), potentially outside the allowed `DOWNLOAD_DIR`.
2. Subprocesses were executed in the server's default CWD, providing an escape vector if path validation was bypassed.

**Learning:**
1. Heuristics that decide *whether* to validate an argument based on its content are dangerous. All arguments should be treated as potentially malicious and validated against expected boundaries.
2. Defence-in-depth for shell-like interfaces should include restricting the execution environment (CWD) to the most restrictive path possible.

**Prevention:**
1. Explicitly set the `cwd` for all subprocesses executed from user-controlled input to a safe, restricted directory.
2. Normalize and validate every command argument against the intended directory constraint, even if it doesn't look like a path.

## 2025-06-18 - [Incomplete Protocol Blocklist and Generalized Attached Flag Bypasses]
**Vulnerability:**
1. Protocol-based SSRF/LFD: The administrative terminal's SSRF protection only checked for a small subset of protocols (http, https, ftp). This allowed for Local File Disclosure (LFD) via the 'file://' protocol and potential SSRF via other obscure protocols like 'gopher://' or 'php://'.
2. Attached Flag Path Traversal: While the terminal tried to check for paths in flags, it only looked for specific flags like '-O' or '-o'. Other tools or flags (e.g., '-C/path') could be used to provide malicious local paths by attaching them directly to the flag.

**Learning:**
1. SSRF and LFD protection must be comprehensive in terms of supported protocols. Any protocol that can resolve to a local file or an internal service should be blocked.
2. CLI flag heuristics must be generic. Instead of whitelisting specific "dangerous" flags, any argument that follows the common "attached short flag" pattern (e.g., -X/path) and contains a slash or traversal marker should be treated as a potential path and validated.

**Prevention:**
1. Use an exhaustive list of dangerous protocols in SSRF/LFD checks.
2. Implement generic flag parsing that extracts potential paths from any short flag where the value is attached without a space or equals sign.

## 2024-05-28 - [Log Redaction Bypass via Structured Formats and Quoted Keys]
**Vulnerability:**
The `redact_sensitive_text` function used simple key-value patterns (e.g., `key=value`) that failed to redact secrets in structured formats like JSON, where keys and values are typically quoted (e.g., `"password": "secret"`). Additionally, Authorization headers with multi-word values (e.g., `Bearer <token>`) were only partially redacted if they contained spaces.

**Learning:**
Security redaction logic must account for the diverse ways sensitive data is serialized in logs. Structured formats like JSON and specific header schemes like 'Bearer' introduce delimiters (quotes, spaces) that can bypass naive regex patterns.

**Prevention:**
Use comprehensive regex patterns that explicitly handle optional quotes (single and double) for both keys and values, and accommodate multi-word tokens in sensitive fields like Authorization.

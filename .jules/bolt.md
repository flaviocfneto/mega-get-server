## 2025-05-15 - Redundant Subprocess Spawns from Concurrent Polling
**Learning:** In applications where multiple API endpoints (e.g., /api/transfers and /api/analytics) poll the same underlying CLI tool (MEGAcmd) via subprocesses, concurrent frontend requests can lead to a surge in CPU usage and slower response times due to redundant process creation.
**Action:** Implement short-lived (sub-second) backend caching for expensive CLI-wrapper functions to collapse multiple concurrent requests into a single subprocess execution.

## 2025-05-16 - Rapid Polling on User Account Metrics & Test Contamination
**Learning:** High-frequency frontend polling of endpoints that invoke multiple underlying CLI commands (like `mega-whoami` and `mega-df`) creates a severe idle CPU bottleneck on the host. Caching this data with a 5.0-second TTL solves the issue, but introduces test state leakage since multiple test cases mock/patch different login/auth contexts. Caches must be explicitly cleared in a test suite teardown/autouse fixture.
**Action:** Implement short-lived backend caches for expensive status commands, clear them instantly on mutation triggers (login/logout/completed downloads), and always register cache-clearing helpers in pytest's `clear_caches` autouse fixture.

## 2025-05-17 - Pre-compiling Regex in Core Log Redaction & Parsing Routines
**Learning:** Text-heavy, highly-frequent operations like log redaction (which runs for every appended log line) and CLI output transfer parsing suffer from substantial CPU overhead when compiling regular expressions dynamically inside loops or functions at runtime. Hoisting all regular expression definitions to the module scope using `re.compile()` completely eliminates dynamic compilation and cache lookup overhead.
**Action:** Always pre-compile regular expression patterns at the module scope for hot paths, loops, or functions called repeatedly under rapid load or continuous log streams.

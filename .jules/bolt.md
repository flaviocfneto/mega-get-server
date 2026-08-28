## 2025-05-15 - Redundant Subprocess Spawns from Concurrent Polling
**Learning:** In applications where multiple API endpoints (e.g., /api/transfers and /api/analytics) poll the same underlying CLI tool (MEGAcmd) via subprocesses, concurrent frontend requests can lead to a surge in CPU usage and slower response times due to redundant process creation.
**Action:** Implement short-lived (sub-second) backend caching for expensive CLI-wrapper functions to collapse multiple concurrent requests into a single subprocess execution.

## 2025-05-16 - Rapid Polling on User Account Metrics & Test Contamination
**Learning:** High-frequency frontend polling of endpoints that invoke multiple underlying CLI commands (like `mega-whoami` and `mega-df`) creates a severe idle CPU bottleneck on the host. Caching this data with a 5.0-second TTL solves the issue, but introduces test state leakage since multiple test cases mock/patch different login/auth contexts. Caches must be explicitly cleared in a test suite teardown/autouse fixture.
**Action:** Implement short-lived backend caches for expensive status commands, clear them instantly on mutation triggers (login/logout/completed downloads), and always register cache-clearing helpers in pytest's `clear_caches` autouse fixture.

## 2025-05-17 - Pre-compiling Regex in Core Log Redaction & Parsing Routines
**Learning:** Text-heavy, highly-frequent operations like log redaction (which runs for every appended log line) and CLI output transfer parsing suffer from substantial CPU overhead when compiling regular expressions dynamically inside loops or functions at runtime. Hoisting all regular expression definitions to the module scope using `re.compile()` completely eliminates dynamic compilation and cache lookup overhead.
**Action:** Always pre-compile regular expression patterns at the module scope for hot paths, loops, or functions called repeatedly under rapid load or continuous log streams.

## 2025-05-18 - Deepcopying Entire Cache Structure in Transfer List Hot Paths
**Learning:** Standard memory/state defense techniques (e.g. returning deep copies of cached dictionaries to prevent mutation) can cause severe O(N^2) CPU overhead when called sequentially inside rendering or API loops. In our transfer metadata registry, lookup of a single tag's metadata triggered a deepcopy of the entire database, which was performed N times for every poll, resulting in massive CPU waste and GC thrashing.
**Action:** Always lookup target entries directly in the cached collections and deepcopy *only* the specific requested element (O(1)) instead of copying the whole structure.

## 2025-05-19 - Safe In-Memory JSON Store Caching with Disk Modification Validation
**Learning:** High-frequency API polling endpoints reading JSON store files off disk (e.g., `/api/queue` calling `read_json_dict`) incur noticeable filesystem and JSON parsing overhead per request. Caching store contents in memory eliminates disk reads, but updating state before atomic disk writes can pollute memory if disk writes fail or validation raises errors. Furthermore, naive caching ignores external process modifications on disk unless `os.stat().st_mtime_ns` is verified prior to serving cached data.
**Action:** Always validate state and write atomically to disk *before* updating module-level in-memory caches, track `st_mtime_ns` to validate cache freshness against disk changes across process boundaries, and register cache clear hooks in test fixtures.

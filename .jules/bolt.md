## 2025-05-15 - Redundant Subprocess Spawns from Concurrent Polling
**Learning:** In applications where multiple API endpoints (e.g., /api/transfers and /api/analytics) poll the same underlying CLI tool (MEGAcmd) via subprocesses, concurrent frontend requests can lead to a surge in CPU usage and slower response times due to redundant process creation.
**Action:** Implement short-lived (sub-second) backend caching for expensive CLI-wrapper functions to collapse multiple concurrent requests into a single subprocess execution.

# Changelog

All notable changes to this project are documented in this file.

## [Unreleased] - 2026-04-08

### Repository layout
- **Canonical folders:** active backend code lives under `api/` (formerly `flet-app/`); active frontend under `web/` (formerly `react-new/`).
- **Legacy sources:** the old minimal React app was removed from the tracked tree; the Flet entrypoint `main.py` was removed from the backend tree. Local copies may exist under gitignored `archive/`; retrieve historical files from git if needed.
- **Tooling and docs** reference `api/` and `web/` (Dockerfiles, CI, launchers, `README.md`, `INFRASTRUCTURE.md`).
- **Final cleanup:** removed temporary root symlinks `flet-app` and `react-new`; use `api/` and `web/` only.

### Added
- New transfer metadata persistence helper at `api/transfer_metadata.py` with JSON-backed storage per transfer tag.
- New diagnostics helper at `api/tool_diagnostics.py` for external tool availability checks and install guidance.
- New API endpoint `GET /api/diag/tools` to report runtime/tool readiness and suggested install commands.
- New backend tests:
  - `api/tests/test_tool_diagnostics.py`
  - `api/tests/test_api_diag_tools.py`
- New backend endpoint `DELETE /api/logs` to clear server-side logs.
- New root launch scripts for running backend + frontend together:
  - `start-dev.sh` (macOS/Linux)
  - `start-dev.bat` (Windows CMD)
  - `start-dev.ps1` (Windows PowerShell)
- New cross-platform Node launcher `start-dev.mjs` to run backend + frontend from a single command.
- New backend analytics tests:
  - `api/tests/test_analytics_capture.py`
  - `api/tests/test_analytics_simulated_e2e.py`

### Changed
- `api/api_main.py`
  - Implemented real transfer metadata operations for:
    - `POST /api/transfers/{tag}/limit`
    - `POST /api/transfers/{tag}/update`
    - `POST /api/transfers/bulk` with metadata actions (`set_priority`, `add_tag`, `remove_tag`).
  - Added structured terminal response fields (`ok`, `command`, `exit_code`, `output`, `blocked_reason`).
  - Expanded terminal command allowlist to include `mega-quit`, enabling in-app daemon recovery workflows.
  - Improved analytics aggregation with live counters and uptime.
  - Added persisted daily analytics buckets (`api/.mega-analytics-daily.json`) and 7-day rollups used by `GET /api/analytics`.
  - Added env-gated analytics parse diagnostics (`MEGA_ANALYTICS_PARSE_DEBUG=1`) to include a `parse_debug` payload in `GET /api/analytics`.
  - Added completion inference when in-flight transfers disappear from `mega-transfers` output, reducing missed completion counts.
  - Fixed `total_downloaded_bytes` to persist after transfer completion/removal by combining persisted completed bytes with current in-flight bytes.
  - Integrated startup diagnostics logging for missing external tools.
- `api/mega_service.py`
  - Merged persisted metadata into canonical transfer rows in `parsed_transfer_to_api_row`.
  - Improved account info handling with best-effort detail enrichment and `details_partial`.
  - Improved `mega-transfers` parsing compatibility by merging stdout/stderr output and supporting additional line formats (Unicode/ASCII arrows, relaxed forms, and `DOWNLOAD/UPLOAD` table-style rows).
  - Added transfer state normalization for analytics (`FINISHED/DONE` -> `COMPLETED`, `CANCELLED/ERROR` -> `FAILED`).
  - Extended account parsing to use combined command output and infer account type when possible.
  - Extended `mega-df` bandwidth/storage parsing with label-driven extraction and `X bytes of Y bytes` quota formats.
  - Improved download reliability and diagnostics for MEGAcmd edge cases:
    - surfaces clearer log context when `mega-get` is accepted but no active transfer appears,
    - retries submit once using a fallback invocation when intermittent `mega-exec` segmentation faults occur,
    - treats `Already exists` as an explicit non-fatal skip outcome instead of a generic parse failure.
- `web/src/App.tsx`
  - Wired UI actions to backend-authoritative responses for terminal, bulk actions, and transfer limit updates.
  - Added explicit warning flow for persisted-only limits (`applied_to_megacmd: false`).
  - Switched log clearing to backend API (`DELETE /api/logs`) and server refresh.
  - Added a frontend diagnostics panel that calls `GET /api/diag/tools`.
  - Added per-tool status rendering and install UX with `Install` / `Copy command` actions.
  - Replaced `UNKNOWN Account` fallback label with `MEGA Account` when account type cannot be inferred.
  - Guarded account quota math against divide-by-zero in account quota calculations.
  - Aligned analytics chart keys with API/types (`daily_stats[].bytes` and `daily_stats[].count`) and added empty-state handling when no daily data exists.
  - In the settings account card only, hides the bandwidth quota block when quota limit is unavailable (`bandwidth_limit_bytes <= 0`).
- `.gitignore`
  - Added `api/.mega-analytics-daily.json` to ignore persisted local analytics counters.
- `web/server.ts`
  - Removed conflicting body parsing from the dev proxy server path so `POST /api/download` reliably forwards request payloads.
- `web/src/types.ts`
  - Added tool diagnostics interfaces and optional `details_partial` in `AccountInfo`.
- `README.md`
  - Added local launcher documentation and now prefers `node start-dev.mjs` as the primary startup command.
- `.github/workflows/test.yml`
  - Expanded coverage targets to include `api_main` and `tool_diagnostics`.
  - Added deterministic test env flags (`MEGA_SIMULATE=1`, `UI_TEST_MODE=1`).

### Documentation
- Updated `README.md` with diagnostics endpoint details, smoke test instructions, and missing-tool install guidance.
- Updated `api/README.md` with API diagnostics usage and manual install guidance.
- Added `docs/COMPAT-LAYOUT.md` describing the folder rename and archive policy.
- Refreshed `INFRASTRUCTURE.md` for FastAPI + React static deployment (replacing outdated Flet-only description).

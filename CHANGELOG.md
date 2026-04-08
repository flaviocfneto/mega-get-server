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

### Changed
- `api/api_main.py`
  - Implemented real transfer metadata operations for:
    - `POST /api/transfers/{tag}/limit`
    - `POST /api/transfers/{tag}/update`
    - `POST /api/transfers/bulk` with metadata actions (`set_priority`, `add_tag`, `remove_tag`).
  - Added structured terminal response fields (`ok`, `command`, `exit_code`, `output`, `blocked_reason`).
  - Expanded terminal command allowlist to include `mega-quit`, enabling in-app daemon recovery workflows.
  - Improved analytics aggregation with live counters and uptime.
  - Integrated startup diagnostics logging for missing external tools.
- `api/mega_service.py`
  - Merged persisted metadata into canonical transfer rows in `parsed_transfer_to_api_row`.
  - Improved account info handling with best-effort detail enrichment and `details_partial`.
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

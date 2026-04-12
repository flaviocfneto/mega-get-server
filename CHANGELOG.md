# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Version **0.3** and **0.4** were not published as tagged releases; development continued from **0.2** to the **0.5** stack migration.

## [Unreleased]

Nothing yet.

## [0.5] - 2026-04-11

FastAPI + React (Vite) stack, canonical `api/` and `web/` layout, MEGAcmd integration hardening, analytics and diagnostics, FileTugger branding, design-system and accessibility work, and documentation updates.

### Breaking changes

- **Repository paths:** Backend code now lives under `api/` (not `flet-app/`); frontend under `web/` (not `react-new/`). Temporary root symlinks were removed—update scripts, Docker contexts, and CI paths accordingly. See [docs/COMPAT-LAYOUT.md](docs/COMPAT-LAYOUT.md).
- **Removed from the tracked tree:** Flet entrypoint `main.py` and the previous minimal React app. Recover old paths from git history or a local gitignored `archive/` copy if needed.
- **Docker / images:** Dockerfiles and CI workflows target the new layout; MEGAcmd image and non-interactive frontend behavior were updated—rebuild and re-validate deploy pipelines.
- **API consumers:** Terminal-related endpoints now return structured fields where applicable: `ok`, `command`, `exit_code`, `output`, `blocked_reason`. `GET /api/analytics` uses persisted daily buckets and may include `parse_debug` when `MEGA_ANALYTICS_PARSE_DEBUG=1`. Account objects may include `details_partial` when MEGAcmd output is incomplete. Client code that assumed older JSON shapes or only stdout parsing should be updated.
- **Web / E2E:** Primary navigation labels and section routing changed (e.g. **History and Queue**, **Logs & Terminal**). The download form and active transfers are scoped to **Transfers**; queue UI moved to **History**. Extensions and Playwright tests must follow the new routes, `TransfersSessionProvider` wrapping, and hash routing helpers.

### 2026-04-08

#### Repository layout

- **Canonical folders:** active backend code lives under `api/` (formerly `flet-app/`); active frontend under `web/` (formerly `react-new/`).
- **Legacy sources:** the old minimal React app was removed from the tracked tree; the Flet entrypoint `main.py` was removed from the backend tree. Local copies may exist under gitignored `archive/`; retrieve historical files from git if needed.
- **Tooling and docs** reference `api/` and `web/` (Dockerfiles, CI, launchers, `README.md`, `INFRASTRUCTURE.md`).
- **Final cleanup:** removed temporary root symlinks `flet-app` and `react-new`; use `api/` and `web/` only.

#### Added

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

#### Changed

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
- `.gitignore`
  - Added `api/.mega-analytics-daily.json` to ignore persisted local analytics counters.
- `web/server.ts`
  - Removed conflicting body parsing from the dev proxy server path so `POST /api/download` reliably forwards request payloads.
- `web/src/types.ts`
  - Added tool diagnostics interfaces and optional `details_partial` in `AccountInfo`.
- `README.md`
  - Added local launcher documentation and now prefers `node start-dev.mjs` as the primary startup command.

#### Documentation

- Updated `README.md` with diagnostics endpoint details, smoke test instructions, and missing-tool install guidance.
- Updated `api/README.md` with API diagnostics usage and manual install guidance.
- Added `docs/COMPAT-LAYOUT.md` describing the folder rename and archive policy.
- Refreshed `INFRASTRUCTURE.md` for FastAPI + React static deployment (replacing outdated Flet-only description).

### 2026-04-09

#### Changed

- `.github/workflows/test.yml`
  - Expanded coverage targets to include `api_main` and `tool_diagnostics`.
  - Added deterministic test env flags (`MEGA_SIMULATE=1`, `UI_TEST_MODE=1`).

### 2026-04-11

#### Web — section-scoped layout, session context, and navigation

- Main column shows the download form and active transfer list only on **Transfers**; **History and Queue** hosts **History and Queue Management** (saved / app queue) and **Download History**.
- Added `TransfersSessionProvider` (`web/src/context/TransfersSessionContext.tsx`) and wrapped the app in `web/src/main.tsx`; transfer/queue domain helpers and last-download messaging live in context.
- Primary navigation labels: **History and Queue**, **Logs & Terminal** (`web/src/navigation/primaryNav.ts`); page title case for **History and Queue Management** and **Download History**.
- Moved `PendingQueuePanel` from `TransfersView` to `HistoryView`; `App.tsx` wires queue props only to History.

#### Tests (web)

- Vitest: global `testTimeout` in `web/vite.config.ts`; `App.test.tsx` and view tests use `TransfersSessionProvider` / hash routing helpers; `web/src/test/renderWithTransfersSession.tsx` for shared setup.
- Playwright: `app-flows.spec.ts` updated for section gating, History queue flow, and nav labels; `e2e/visual-home.spec.ts` baseline snapshot refreshed for the current shell and per-test timeout raised for full-page screenshots; `playwright.config.ts` `webServer` timeout raised so a cold `vite build` can finish before preview binds.

#### Design system — typography and accessibility

- Adopted **Atkinson Hyperlegible Next**, **Atkinson Hyperlegible Mono**, **Lora**, and **Fraunces** in `DESIGN/tokens/ft-tokens.css` (mirrored in `DESIGN/ft-tokens.css`) with new `--ft-font-serif` and `--ft-font-display` tokens; extended `DESIGN/tokens/ft-tailwind.config.js` / `DESIGN/ft-tailwind.config.js` with `serif` and `display` font families.
- Documented type roles, scale, and WCAG 2.2 AA criteria in `docs/FRONTEND-DESIGN-PHILOSOPHY.md` (§5.3, expanded §9); added `docs/ACCESSIBILITY.md` and linked regression checks to `commands/accessibility-tester.md`.
- Updated `DESIGN/docs/BRAND.md` wordmark/tagline typefaces and aligned SVG wordmarks/banners under `DESIGN/logos/` and root `DESIGN/*` duplicates.
- Web app: `web/src/main.tsx` imports design tokens; `web/src/index.css` maps Tailwind font tokens to `--ft-font-*`; `web/index.html` loads Google Fonts and sets `lang="en-GB"`; `web/README.md` documents the pipeline.
- Added a skip-to-main link and `id="main-content"` on `<main>` in `web/src/App.tsx`.

#### Branding

- Renamed the app brand from `LinkTugger` to `FileTugger` across frontend runtime labels, backend API title, and repository docs.
- Updated webpage branding in `web/index.html`:
  - set browser tab title to `FileTugger`,
  - added favicon wiring to `/icons/ft-favicon.svg`,
  - added PWA manifest/theme-color metadata.
- Integrated DESIGN assets into frontend static paths:
  - `web/public/icons/ft-favicon.svg`
  - `web/public/icons/ft-icon-app.svg`
  - `web/public/branding/ft-logo-wordmark.svg`
  - `web/public/manifest.webmanifest`
- Updated frontend notification icon usage to the new app icon asset (`/icons/ft-icon-app.svg`).
- Updated `README.md` with FileTugger visual assets from `DESIGN/` and added a dedicated branding assets section.
- Aligned small in-app UX copy in `web/src/App.tsx` with FileTugger brand tone while keeping technical MEGA/MEGAcmd wording where required.
- Expanded `README.md` with dedicated logs/diagnostics endpoint examples and refreshed branding section language.

#### Changed

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

## [0.2] - 2026-02-02

- Bumped internal **fleet** / app packaging to **version 0.2** (see git history: `fleet version 0.2`, `version 0.2`).

## [0.1] - 2026-02-01

- Initial **Flet**-based application milestone (**Flet version 0.1**).

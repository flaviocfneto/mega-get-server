# Changelog

All notable changes to **FileTugger** (MEGA.nz downloads with a web UI and FastAPI backend) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries are written for **operators and end users** first: what changed in behavior, deployment, or the UI, then what integrators need to know. Internal-only refactors and test-only churn are summarized lightly or omitted.

Version **0.3** and **0.4** were not published as tagged releases; development continued from **0.2** through the **0.5** stack migration.

---

## [Unreleased]

### Added

- **Generic HTTP(S) downloads** alongside MEGA links: paste a normal `https://` or `http://` URL (not `mega.nz`) and the app can fetch it with **GNU Wget2**, using the same queue, transfer list, pause/resume/cancel, and cancel-all flows as MEGAcmd-driven transfers. MEGA URLs still use the dedicated MEGA path.
- **Wget2 in container images** so HTTP downloads work out of the box in Docker; diagnostics can report Wget2 availability and suggest install commands where it is missing.
- **`HTTP_DOWNLOADS_ENABLED`** (default on): set to `0` / `false` / `no` / `off` to disable generic HTTP downloads on a given server.
- **Host safety rules** for HTTP mode: localhost, private IPs, and similar hosts are rejected so the feature is harder to abuse as an open proxy.
- **Large expansion of automated tests** around downloads, queue dispatch, HTTP transfer APIs, security boundaries, and related modules—supporting safer iteration on dual-driver (MEGA + HTTP) behavior.

### Changed

- **CI quality bar**: backend test coverage is now enforced at a higher threshold (85%) so regressions in core API paths are caught earlier.
- **Tool diagnostics** extended to cover the HTTP client stack (Wget2) alongside existing MEGAcmd-oriented checks.

### Documentation

- **Design playbooks**: added improvement checklists under `DESIGN/docs/` aligned with common review dimensions (code review, security, performance, QA, UI/UX, Docker, chaos)—useful for humans and agents working on `api/`, `web/`, and container layout.

---

## [0.5] - 2026-04-11

This release is the **FastAPI + React (Vite)** stack as the primary product surface: canonical **`api/`** and **`web/`** layout, hardened MEGAcmd integration, richer **analytics and diagnostics**, **FileTugger** branding and design system work, and **navigation** that separates transfers from history and logs.

### Breaking changes

Read this section if you **upgrade containers**, **maintain CI**, or **embed the API**.

- **Repository layout:** Backend code lives under `api/` (not `flet-app/`); frontend under `web/` (not `react-new/`). Temporary root symlinks were removed—update Docker build contexts, scripts, and CI paths. See [docs/COMPAT-LAYOUT.md](docs/COMPAT-LAYOUT.md).
- **Removed from the tracked tree:** the Flet entrypoint `main.py` and the previous minimal React app. Recover old paths from git history or a local gitignored `archive/` copy if you still need them.
- **Docker and images:** Dockerfiles and workflows target the new layout; MEGAcmd image bumps and non-interactive package installs (`DEBIAN_FRONTEND`) changed image behavior—**rebuild** images and re-validate deploy pipelines.
- **API JSON shapes:** Terminal-related endpoints return structured fields where applicable: `ok`, `command`, `exit_code`, `output`, `blocked_reason`. `GET /api/analytics` uses **persisted daily buckets** and may include `parse_debug` when `MEGA_ANALYTICS_PARSE_DEBUG=1`. Account payloads may include `details_partial` when MEGAcmd output is incomplete. Clients that assumed older shapes or stdout-only parsing must be updated.
- **Web routes and labels:** Primary navigation and section routing changed (e.g. **History and Queue**, **Logs & Terminal**). The download form and active transfers live under **Transfers**; queue-oriented UI moved to **History**. E2E tests, deep links, and any automation must follow the new routes, `TransfersSessionProvider` wrapping, and hash-routing helpers.

### Added

- **Transfer metadata persistence** (`api/transfer_metadata.py`): JSON-backed per-transfer tags for limits, labels, and bulk metadata actions from the API.
- **Runtime tool diagnostics** (`api/tool_diagnostics.py`) and **`GET /api/diag/tools`**: reports whether external tools are present, versions when detectable, impact if missing, and suggested install commands—without auto-installing anything on your host.
- **`DELETE /api/logs`**: clear server-side logs from the API (mirrored in the UI).
- **One-command local dev**: `start-dev.sh`, `start-dev.bat`, `start-dev.ps1`, and cross-platform `start-dev.mjs` to run backend and frontend together; README prefers `node start-dev.mjs`.
- **Backend tests** for diagnostics, analytics capture/simulation, and the new API surface areas.
- **Accessibility and design documentation:** skip link to main content, `id="main-content"` on `<main>`, expanded typography tokens (**Atkinson Hyperlegible Next/Mono**, **Lora**, **Fraunces**), WCAG-oriented notes in `docs/FRONTEND-DESIGN-PHILOSOPHY.md` and `docs/ACCESSIBILITY.md`.
- **PWA-oriented metadata** in `web/index.html`: FileTugger title, favicon, manifest, theme color; static branding assets under `web/public/`.

### Changed

- **Transfers and queue API:** Real implementations for `POST /api/transfers/{tag}/limit`, `POST /api/transfers/{tag}/update`, and `POST /api/transfers/bulk` (including metadata actions: `set_priority`, `add_tag`, `remove_tag`). Terminal allowlist extended with `mega-quit` for in-app daemon recovery.
- **Analytics:** Live counters and uptime, **7-day rollups** and daily persistence to `api/.mega-analytics-daily.json` (gitignored locally), optional parse diagnostics, better completion inference when rows disappear from `mega-transfers`, and corrected **`total_downloaded_bytes`** persistence across completion/removal.
- **MEGAcmd parsing and reliability:** Merged stdout/stderr, broader line-format support, state normalization for analytics, improved account and `mega-df` parsing, clearer logging when `mega-get` accepts but no transfer appears, retry on intermittent `mega-exec` faults, and **`Already exists`** treated as a non-fatal skip.
- **Account UI:** `UNKNOWN Account` replaced with **`MEGA Account`** when type cannot be inferred; quota math guarded against divide-by-zero; bandwidth block hidden in settings when quota is unavailable.
- **Frontend dev proxy:** Fixed body forwarding so **`POST /api/download`** reliably receives payloads through the Vite dev server.
- **UI wiring:** Terminal, bulk actions, and transfer limits respect **backend-authoritative** responses; warning when persisted limits are not applied to MEGAcmd (`applied_to_megacmd: false`); log clearing uses `DELETE /api/logs`; **diagnostics panel** in the app calls `GET /api/diag/tools` with install/copy-command affordances.
- **Branding:** Renamed from **LinkTugger** to **FileTugger** across runtime labels, API title, and docs; README documents design assets and diagnostics.

### Fixed

- **Dev server:** Removed conflicting body parsing on the dev proxy path so downloads work reliably during local development.

### Documentation

- **README:** Diagnostics endpoint, smoke tests, missing-tool guidance, launcher docs, branding assets.
- **api/README:** Diagnostics usage and manual install notes.
- **docs/COMPAT-LAYOUT.md:** Folder rename and archive policy.
- **INFRASTRUCTURE.md:** Updated for FastAPI + React static deployment (replacing Flet-only description).

### Release timeline (0.5 development)

#### 2026-04-08 — Layout, API, and MEGAcmd hardening

Canonical **`api/`** / **`web/`** folders replaced `flet-app/` / `react-new/`; symlinks removed after transition. New persistence, diagnostics endpoint, log clearing, dev launchers, and the analytics/transfer behavior described above landed in this window.

#### 2026-04-09 — CI

- GitHub Actions **`test.yml`**: broader coverage targets (`api_main`, `tool_diagnostics`), deterministic flags (`MEGA_SIMULATE=1`, `UI_TEST_MODE=1`) for stable automated runs.

#### 2026-04-11 — Web structure, design system, branding

- **Section-scoped UI:** Transfers vs History vs Logs; **`TransfersSessionProvider`** and context-driven helpers; **`PendingQueuePanel`** lives on History; Playwright/Vitest updated for gating and navigation.
- **Design system:** Token and Tailwind updates; Google Fonts pipeline; `lang="en-GB"` on `index.html`.
- **FileTugger** visual identity wired through favicon, icons, wordmark, notifications, and copy aligned to brand tone where appropriate.

---

## [0.2] - 2026-02-02

### Summary

Internal **fleet** / packaging bump to **version 0.2** with continued iteration on the download server and UI (see git history: `fleet version 0.2`, `version 0.2`).

---

## [0.1] - 2026-02-01

### Summary

Initial **Flet**-based application milestone (**Flet version 0.1**): early web UI for MEGA-linked downloads and container-oriented workflow.

---

## Earlier history (high level)

The following older milestones are preserved as context; see `git log` for exact commits.

- **Dependency and base-image updates:** MEGAcmd and Ubuntu version bumps over time (e.g. 1.2.x through 1.7.x, Ubuntu 20.04 → 24.04 on various tracks), **websocketd** updates, and related Dockerfile maintenance.
- **Web over WebSocket:** Enabled serving the web UI over WebSocket alongside backend work.
- **Transfer controls:** Cancel, pause, and resume for selected transfers; horizontal scroll for long paths when `PATH_DISPLAY_SIZE` is large on small screens; clearer status output when `INPUT_TIMEOUT` is slow.
- **Networking and permissions:** **`EXTERNAL_PORT`** decoupled from internal port settings; **`--user`** support documented for better file ownership in Docker; filename display fixes.

---

## For maintainers

- Prefer tagging releases when a version is shipped to users; this file’s **[Unreleased]** section should be rolled into a dated version section at release time.
- When adding entries, describe **user-visible behavior** and **migration steps** before listing file-level edits.

# Changelog

All notable changes to **FileTugger** (MEGA.nz downloads with a web UI and FastAPI backend) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries are written for **operators and end users** first: what changed in behavior, deployment, or the UI, then what integrators need to know. Internal-only refactors and test-only churn are summarized lightly or omitted.

Version **0.3** and **0.4** were not published as tagged releases; development continued from **0.2** through the **0.5** stack migration.

---

## [0.5.0] - 2026-05-22

### Added

- **Tiered CI System**: Implemented a proportional Quality Assurance system gating checks based on version bumps (Patch, Minor, Major).
  - **Tier 1 (Patch/PR)**: Fast feedback with Ruff, Mypy, and Core Unit Tests.
  - **Tier 2 (Minor)**: Exhaustive testing including Bandit, Semgrep, E2E (Playwright), and Lighthouse.
  - **Tier 3 (Major)**: Full release readiness with Docker builds and multi-platform validation.
- **Python Quality Tools**: Integrated **Ruff** (lint/format), **Mypy** (strict typing), **Bandit** (SAST), and **Semgrep** (SAST) into the backend pipeline.
- **Version Synchronization**: Centralized versioning in `pyproject.toml` with automated synchronization to `web/package.json` via GitHub Actions.
- **Generic HTTP(S) downloads** alongside MEGA links: paste a normal `https://` or `http://` URL (not `mega.nz`) and the app can fetch it with **GNU Wget2**.
- **Wget2 in container images** for out-of-the-box HTTP download support.
- **Host safety rules** for HTTP mode to prevent SSRF and open proxy abuse.
- **Large expansion of automated tests** around downloads, queue dispatch, and security boundaries.

### Changed

- **CI Infrastructure**: Consolidated and specialized workflows with tiered execution logic.
- **Frontend CI**: Migrated to **pnpm** for faster and more reliable dependency management and builds.
- **CI quality bar**: Backend test coverage now enforced at 80%+ across core modules.
- **Tool diagnostics** extended to cover the HTTP client stack (Wget2).

---

## [0.5-beta] - 2026-04-11

This release is the **FastAPI + React (Vite)** stack as the primary product surface: canonical **`api/`** and **`web/`** layout, hardened MEGAcmd integration, richer **analytics and diagnostics**, **FileTugger** branding and design system work, and **navigation** that separates transfers from history and logs.

### Breaking changes

- **Repository layout:** Backend code lives under `api/`; frontend under `web/`.
- **Docker and images:** Dockerfiles and workflows target the new layout.
- **API JSON shapes:** Terminal-related endpoints return structured fields; `GET /api/analytics` uses persisted daily buckets.

### Added

- **Transfer metadata persistence**: JSON-backed per-transfer tags.
- **Runtime tool diagnostics**: `GET /api/diag/tools` reports external tool status.
- **Log management**: `DELETE /api/logs` to clear server-side logs.
- **One-command local dev**: `start-dev.mjs` launcher.

### Changed

- **Analytics**: 7-day rollups and daily persistence.
- **MEGAcmd reliability**: Improved parsing, retry on faults, and non-fatal skip for existing files.
- **UI wiring**: Authoritative backend responses for transfers and limits.

---

## [0.2] - 2026-02-02

### Summary

Internal packaging bump to **version 0.2** with continued iteration on the download server and UI.

---

## [0.1] - 2026-02-01

### Summary

Initial **Flet**-based application milestone (**Flet version 0.1**).

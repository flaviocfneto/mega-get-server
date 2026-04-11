# Infrastructure Document — FileTugger

This document describes how the **FileTugger** project is built, deployed, and how its components interact at runtime.

---

## 1. Overview

**FileTugger** is a containerized service that provides a web UI for downloading files from MEGA.nz. It is intended to run on a NAS or similar host, with a configurable download directory (typically a mounted share).

- **Purpose:** Download MEGA export links via a browser, with transfer control (cancel, pause, resume).
- **Stack:** Ubuntu 24.04 (default image), MEGA CMD, Python 3, **FastAPI** (backend), **React** SPA (built from `web/`, served as static files from `/app/static`).
- **Delivery:** Single Docker image; **Uvicorn** serves FastAPI on port **8080** (see `files/entrypoint.sh`). The browser loads the React UI from the same origin (`/`); API routes are under `/api/*`. No EXTERNAL_HOST or EXTERNAL_PORT configuration is required.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Container                                 │
│                                                                          │
│  ┌──────────────┐    ┌─────────────────────┐    ┌──────────────────────┐ │
│  │ mega-cmd-    │    │  FastAPI (Uvicorn)   │    │  Browser             │ │
│  │ server       │◄───│  + static SPA        │◄───│  HTTP same origin    │ │
│  └──────┬───────┘    │  port 8080           │    └──────────────────────┘ │
│         │            └──────────┬───────────┘                             │
│         │                       │ asyncio subprocess                     │
│         │                       ▼                                        │
│         │             mega-get / mega-transfers                            │
│         ▼                                                                │
│  ┌──────────────────────────────────────┐                               │
│  │  /data/ (DOWNLOAD_DIR)                │                               │
│  └──────────────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘
```

- **mega-cmd-server:** MEGA’s background service; all `mega-*` CLI commands talk to it.
- **FastAPI app (`api_main.py`):** REST API for the React UI; runs MEGAcmd via subprocesses; optional static mount for the built frontend.

---

## 3. Component Details

### 3.1 Dockerfile (root `Dockerfile`)

- **Base:** multi-stage — Node builds `web/`, then Ubuntu runtime.
- **External assets (at build time):** MEGA CMD `.deb` for Ubuntu (version pinned in Dockerfile).
- **Build steps:** Build React to `dist/`, copy into `/app/static`; copy `api/` to `/app`; install Python deps from `requirements.txt`; copy `files/` to `$HOME`.
- **Expose:** 8080.
- **Entrypoint:** `$HOME/entrypoint.sh` — starts `mega-cmd-server`, then runs Uvicorn for `api_main:app`.

### 3.2 entrypoint.sh

1. **Start MEGA:** `mega-cmd-server &`.
2. **Permissions:** `mega-permissions` for default file/folder modes.
3. **Delay:** Short sleep so mega-cmd-server can bind.
4. **Run API:** `exec ... uvicorn api_main:app` with `--app-dir /app`.

### 3.3 Application code

- **Backend:** `api/` — `api_main.py`, `mega_service.py`, tests.
- **Frontend:** `web/` — Vite + React; production build consumed by Docker as `/app/static`.

---

## 4. Data and Request Flow

1. User opens `http://host:8080` → FastAPI serves the React SPA from `/` and API under `/api/*`.
2. User submits a download URL → backend runs `mega-get` (and related) toward `DOWNLOAD_DIR`.
3. UI polls `/api/transfers`, `/api/logs`, etc., for status.

Persistent transfer state is primarily in MEGA CMD; the server adds logging, metadata, and API shaping.

---

## 5. Configuration (Environment Variables)

| Variable | Default | Role |
|----------|---------|------|
| `DOWNLOAD_DIR` | `/data/` | Where MEGA saves files; usually a volume mount. |
| `HOME` | `/home/mega` | Used by entrypoint; MEGA CMD session/cache. |
| `NEW_FILE_PERMISSIONS` | `600` | Default permissions for downloaded files. |
| `NEW_FOLDER_PERMISSIONS` | `700` | Default permissions for new folders. |
| `TRANSFER_LIST_LIMIT` | `50` | Max transfers surfaced to the UI. |
| `PATH_DISPLAY_SIZE` | `80` | Max characters for file path in transfer list. |
| `INPUT_TIMEOUT` | `0.0166` | Poll interval lower bound (seconds). |
| `FLET_SERVER_PORT` | `8080` | Listen port (name retained for compatibility with older env files). |

---

## 6. CI/CD — GitHub Actions

- **Quality gate:** `.github/workflows/quality.yml`
  - Backend tests + coverage threshold.
  - Frontend type checks (`lint` + `lint:strict`), tests, and build.
  - Playwright E2E smoke test.
- **Security gate:** `.github/workflows/security.yml`
  - Python dependency audit (`pip-audit`).
  - Node dependency audit (`npm audit --audit-level=high`).
  - Secret scanning with gitleaks.
  - Container vulnerability scan with Trivy.
- **Static analysis:** `.github/workflows/codeql.yml` for Python and JavaScript/TypeScript. **Note:** CodeQL is **not** executed inside the Security Gate workflow; it is a separate workflow. Merge policy should treat both as important; see [docs/security/VERIFICATION-PACK.md](docs/security/VERIFICATION-PACK.md) and [docs/security/OPERATIONS-GITHUB.md](docs/security/OPERATIONS-GITHUB.md) for requiring checks on the default branch.
- **Release publish:** `.github/workflows/publish.yml`
  - Triggered on release events (`published` and `edited`) and pushes tagged container images.
- **Legacy backend test workflow:** `.github/workflows/test.yml` remains available for focused API test runs.

---

## 7. Deployment Summary

- **Single service:** One container; no separate database.
- **Port:** One port (8080) for HTTP; same-origin SPA + API.
- **Persistence:** Mounted volume for `DOWNLOAD_DIR`.
- **Process user:** The default `Dockerfile` runs the API as a non-root user (`mega`); use a hardened or custom image only if you understand the user/permission model.
- **TLS:** No TLS in the image (use a reverse proxy for HTTPS).

Repository layout is documented in [docs/COMPAT-LAYOUT.md](docs/COMPAT-LAYOUT.md).

---

## 8. Security and scaling notes

### 8.1 Rate limiting (API)

- Route limits are implemented in `api/security.py` using **in-memory** per-process state (`_rate_state`).
- A single container sees consistent limits across requests hitting that process.
- **Multiple replicas** (or multiple processes without shared state) do **not** share counters; a client could send more requests in total than the per-route limit implies by spreading traffic across instances.
- **Mitigations (deployment-level):** enforce limits at a reverse proxy or API gateway; use a shared rate-limit store (e.g. Redis) if you implement it in application code; or accept single-instance semantics. See [docs/security/FINDINGS-REGISTER.md](docs/security/FINDINGS-REGISTER.md) (SEC-006 residual).

### 8.2 Pending download queue (application-level)

- The **saved link queue** is stored in `api/pending_queue.json` beside other local JSON state. It is intended for a **single API process / one replica**; multiple replicas without a shared store will not see one global queue.
- **`GET /api/queue`** returns pending MEGA URLs with the same **read-path trust model** as **`GET /api/history`**: when `API_AUTH_MODE` is not `strict`, treat the API as reachable only on a **trusted network** or protect it at the reverse proxy.
- **`api/pending_correlation.json`** holds short-lived rows used to attach user labels/priority to a MEGAcmd transfer tag when tag correlation was ambiguous immediately after dispatch. Same trust model and single-process assumptions as the pending queue; entries are capped and TTL-pruned.

### 8.3 Static analysis and CI gates

- CodeQL and the Security Gate workflow are separate; repository owners configure **branch protection** in GitHub to require both (or your chosen subset). Follow [docs/security/OPERATIONS-GITHUB.md](docs/security/OPERATIONS-GITHUB.md).

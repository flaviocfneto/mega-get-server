# Infrastructure Document — mega-get-server

This document describes how the **mega-get-server** project is built, deployed, and how its components interact at runtime.

---

## 1. Overview

**mega-get-server** is a containerized service that provides a web UI for downloading files from MEGA.nz. It is intended to run on a NAS or similar host, with a configurable download directory (typically a mounted share).

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

- **Workflow file:** `.github/workflows/publish.yml`
- **Trigger:** On release events `published` or `edited`.
- **Steps:** Log in to Docker Hub, set up QEMU and Buildx, build and push with version and `latest` tags.

**Tests:** `.github/workflows/test.yml` runs `pytest` against `api/tests` with `PYTHONPATH=api`.

---

## 7. Deployment Summary

- **Single service:** One container; no separate database.
- **Port:** One port (8080) for HTTP; same-origin SPA + API.
- **Persistence:** Mounted volume for `DOWNLOAD_DIR`.
- **Security:** Runs as root unless overridden; no TLS in the image (use a reverse proxy for HTTPS).

Repository layout is documented in [docs/COMPAT-LAYOUT.md](docs/COMPAT-LAYOUT.md).

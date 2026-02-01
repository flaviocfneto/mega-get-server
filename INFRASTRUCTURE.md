# Infrastructure Document — mega-get-server

This document describes how the **mega-get-server** project is built, deployed, and how its components interact at runtime.

---

## 1. Overview

**mega-get-server** is a containerized service that provides a web UI for downloading files from MEGA.nz. It is intended to run on a NAS or similar host, with a configurable download directory (typically a mounted share).

- **Purpose:** Download MEGA export links via a browser, with transfer control (cancel, pause, resume).
- **Stack:** Ubuntu 24.04, MEGA CMD, Python 3, Flet (web UI).
- **Delivery:** Single Docker image; one process serves HTTP and WebSocket on port 8080. No EXTERNAL_HOST or EXTERNAL_PORT configuration is required.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Container (Ubuntu 24.04)                  │
│                                                                          │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────────────┐  │
│  │ mega-cmd-    │    │  Flet app       │    │  Browser                │  │
│  │ server       │◄───│  (port 8080)    │◄───│  (HTTP + WebSocket)     │  │
│  └──────┬───────┘    └────────┬────────┘    └────────────────────────┘  │
│         │                      │                         ▲               │
│         │                      │ asyncio subprocess       │ same origin   │
│         │                      ▼                         │               │
│         │             mega-get / mega-transfers          │               │
│         ▼                      │                                          │
│  ┌──────────────────────────────────────┐     ┌───────────────────────┐  │
│  │  /data/ (DOWNLOAD_DIR)                │     │  http://host:8080     │  │
│  │  (mounted volume for downloads)       │     │  (user’s browser)     │  │
│  └──────────────────────────────────────┘     └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

- **mega-cmd-server:** MEGA’s background service; all `mega-*` CLI commands talk to it.
- **Flet app:** Python app (Uvicorn under the hood) that serves the web UI and WebSocket on port 8080. It runs `mega-get` and `mega-transfers` via `asyncio.create_subprocess_exec()`, polls the transfer list periodically, and updates the UI. Same origin, so no URL configuration is needed for the browser.

---

## 3. Component Details

### 3.1 Dockerfile

- **Base:** `ubuntu:24.04`
- **External assets (at build time):**
  - **MEGA CMD** 2.1.1 (amd64 .deb) from MEGA’s Ubuntu 24.04 repo — provides `mega-cmd-server`, `mega-get`, `mega-transfers`, `mega-permissions`.
- **Build steps:** Install Python 3, pip, and the MEGA CMD .deb; create `HOME` (`/home/mega`) and `DOWNLOAD_DIR` (`/data/`); copy `flet-app/` to `/app` and install Python dependencies from `requirements.txt`; copy `files/` (entrypoint only) to `$HOME`.
- **Expose:** 8080.
- **Entrypoint:** `$HOME/entrypoint.sh` — starts mega-cmd-server, then runs the Flet app.

### 3.2 entrypoint.sh

1. **Start MEGA:** `mega-cmd-server &` — required for all `mega-get` / `mega-transfers` usage.
2. **Permissions:** `mega-permissions` sets default file and folder permissions from `NEW_FILE_PERMISSIONS` and `NEW_FOLDER_PERMISSIONS`.
3. **Delay:** Short sleep so mega-cmd-server can bind its socket.
4. **Run Flet:** `exec python3 /app/main.py` — Flet serves HTTP and WebSocket on port 8080 (`FLET_FORCE_WEB_SERVER=true` and `FLET_SERVER_PORT=8080` are set in the Dockerfile).

### 3.3 Flet app (`/app/main.py`)

- **UI:** URL input, Get button, transfer tag input, Cancel/Pause/Resume buttons, log/transfer area (read-only text).
- **Actions:** On Get, runs `mega-get -q --ignore-quota-warn <url> <DOWNLOAD_DIR>` via asyncio subprocess. On Cancel/Pause/Resume, runs `mega-transfers -c/-p/-r <tag>`.
- **Polling:** Background task runs `mega-transfers --limit=... --path-display-size=...` at a configurable interval and updates the log area.
- **Env vars:** Reads `DOWNLOAD_DIR`, `TRANSFER_LIST_LIMIT`, `PATH_DISPLAY_SIZE`, `INPUT_TIMEOUT` from the environment.

---

## 4. Data and Request Flow

1. User opens `http://host:8080` → Flet serves the web UI from the same origin.
2. User submits a MEGA URL → Flet runs `mega-get ... "$DOWNLOAD_DIR"` in a background task → MEGA CMD downloads into `/data/` (or mounted volume).
3. A background task periodically runs `mega-transfers ...` and updates the log area with the current transfer list.
4. Cancel/Pause/Resume send the chosen tag to Flet, which runs `mega-transfers -c/-p/-r`.

All persistent state (active transfers, queue) lives in MEGA CMD; the Flet app is stateless and only forwards commands and displays status.

---

## 5. Configuration (Environment Variables)

| Variable | Default | Role |
|----------|---------|------|
| `DOWNLOAD_DIR` | `/data/` | Where MEGA saves files; usually a volume mount. |
| `HOME` | `/home/mega` | Used by entrypoint; MEGA CMD also uses it for session/cache. |
| `NEW_FILE_PERMISSIONS` | `600` | Default permissions for downloaded files. |
| `NEW_FOLDER_PERMISSIONS` | `700` | Default permissions for new folders. |
| `TRANSFER_LIST_LIMIT` | `50` | Max lines from `mega-transfers` shown in the UI. |
| `PATH_DISPLAY_SIZE` | `80` | Max characters for file path in transfer list. |
| `INPUT_TIMEOUT` | `0.0166` | Poll interval lower bound (seconds); affects UI update frequency and CPU. |
| `FLET_FORCE_WEB_SERVER` | `true` | Set in Dockerfile so Flet runs as a web server in the container. |
| `FLET_SERVER_PORT` | `8080` | Port the Flet app listens on. |

---

## 6. CI/CD — GitHub Actions

- **Workflow file:** `.github/workflows/publish.yml`
- **Trigger:** On release events `published` or `edited`.
- **Steps:** Log in to Docker Hub, set up QEMU and Buildx, build and push with version and `latest` tags.

---

## 7. Deployment Summary

- **Single service:** One container; no database or external backend.
- **Port:** One port (8080) for HTTP and WebSocket; no EXTERNAL_HOST/EXTERNAL_PORT.
- **Persistence:** Only the mounted volume for `DOWNLOAD_DIR`.
- **Gluetun:** Use `network_mode: "service:protonvpn"` and expose `8383:8080` on the VPN service; the Flet app listens on 8080 inside the shared network.
- **Security:** Runs as root unless overridden with `docker run --user`; permissions for new files/folders are set via env vars. No TLS in the image (reverse proxy recommended for HTTPS/WSS).

This infrastructure document reflects the behavior of the code as of the current repository state.

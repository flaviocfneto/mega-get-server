# mega-get-server

A simple Docker image with a web UI for downloading exported links from https://mega.nz/

Deploy this image to a NAS server to facilitate direct download of files via the **React** UI in [`web/`](web/) and a **FastAPI** backend (MEGAcmd) in [`api/`](api/). Folder layout notes: [docs/COMPAT-LAYOUT.md](docs/COMPAT-LAYOUT.md).

## Basic Set Up

```bash
docker run \
    --detach --restart unless-stopped \
    --publish 8080:8080 \
    --volume /mnt/samba-share/:/data/ \
    gm0n3y2503/mega-get-server:latest
```

Added links will be downloaded in the `/data/` directory, which you can mount to your own folder as shown above.

Open **http://host:8080** in your browser (use the hostname or IP of the machine running the container). No EXTERNAL_HOST or EXTERNAL_PORT configuration is needed; the UI is served from the same origin.

By default, files and folders downloaded will be owned by `root` with user-only permissions. The user can be changed with the `--user` flag for `docker run`, and permissions can be adjusted with the `*_PERMISSIONS` environment variables below.

## Configurable Variables

`DOWNLOAD_DIR=/data/` — Directory where MEGA saves files (usually a volume mount).

`NEW_FILE_PERMISSIONS=600` — Permissions of downloaded files.

`NEW_FOLDER_PERMISSIONS=700` — Permissions of downloaded folders.

`TRANSFER_LIST_LIMIT=50` — Number of transfers shown in the UI.

`PATH_DISPLAY_SIZE=80` — Maximum characters shown for the download file path.

`INPUT_TIMEOUT=0.0166` — Poll interval lower bound (seconds) for the transfer list; affects UI update frequency and CPU use.

## Diagnostics and smoke tests

The backend exposes tool readiness diagnostics at `GET /api/diag/tools`.
This endpoint reports:

- whether each external dependency is available
- detected version (when available)
- what features are impacted if missing
- install instructions and suggested commands to run manually

The app does not auto-install dependencies; it only reports availability and suggests commands.

### Run backend smoke tests locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt pytest
PYTHONPATH=api MEGA_SIMULATE=1 UI_TEST_MODE=1 pytest api/tests -v
```

If MEGAcmd is missing, install it and set the binary path when needed:

```bash
brew install --cask megacmd
export MEGACMD_PATH=/Applications/MEGAcmd.app/Contents/MacOS
```

## Local launcher (frontend + backend)

From project root, use the cross-platform Node launcher:

- `node start-dev.mjs`

This launcher starts:

- FastAPI backend (`api/api_main.py`) on `http://127.0.0.1:8000`
- React frontend (`web`) dev server on `http://localhost:5173`

Optional overrides:

- `API_HOST` (default `127.0.0.1`)
- `API_PORT` (default `8000`)
- `UI_PORT` (default `5173`)

Legacy platform-specific scripts are still available if needed:

- `./start-dev.sh`
- `start-dev.bat`
- `.\start-dev.ps1`

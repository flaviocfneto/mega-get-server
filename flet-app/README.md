# MEGA Get – Flet prototype

Minimal Flet web UI for mega-get-server: add MEGA URLs, view transfers, cancel/pause/resume. Runs as a **desktop app** (native window), **web app** (browser or server), or inside **Docker** (web server on port 8080). The app adapts at startup: it detects the environment and sets Flet view, port, and a platform-aware default for `DOWNLOAD_DIR`.

## Run modes

- **Desktop** — Native window (Windows, macOS, Linux). Run `flet run main.py` or `python main.py` (do not set `FLET_FORCE_WEB_SERVER`). Downloads default to `~/Downloads` (or `%USERPROFILE%\Downloads` on Windows) when `DOWNLOAD_DIR` is unset.
- **Web** — Browser or web server. Run `flet run --web --port 8080 main.py`, or set `FLET_FORCE_WEB_SERVER=true` and run `python main.py`, then open **http://localhost:8080**. Same `DOWNLOAD_DIR` default as desktop when unset.
- **Docker** — Headless web server on port 8080. The image sets `FLET_FORCE_WEB_SERVER=true` and runs `python main.py`; the app detects Docker and uses web server mode. `DOWNLOAD_DIR` defaults to `/data/` (mount a volume there).

### Run as desktop app (native window)

```bash
cd flet-app
source .venv/bin/activate   # Windows: .venv\Scripts\activate
flet run main.py
# or: python main.py
```

Do not set `FLET_FORCE_WEB_SERVER`. Downloads go to `~/Downloads` (or your platform’s Downloads folder) unless you set `DOWNLOAD_DIR`.

## Run locally (simulation, no MEGA CMD)

```bash
cd flet-app
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
MEGA_SIMULATE=1 FLET_FORCE_WEB_SERVER=true flet run --web --port 8080 main.py
```

Then open **http://localhost:8080** in your browser. You’ll see a fake transfer list and can click Get (simulated “URL Accepted”).

## Run with MEGA CMD

1. Start **mega-cmd-server** (e.g. in another terminal or in Docker). On **macOS**, either open **MEGAcmd** from Applications once (this starts the server), or the server may start automatically on first `mega-get` / `mega-transfers` call.
2. From `flet-app` (with venv activated):

```bash
pip install -r requirements.txt
FLET_FORCE_WEB_SERVER=true flet run --web --port 8080 main.py
```

Or run directly (port 8080 is set in `main.py`):

```bash
FLET_FORCE_WEB_SERVER=true python main.py
```

3. Open **http://localhost:8080**.

### macOS: use local MEGAcmd

If MEGAcmd is installed from [Applications](https://github.com/meganz/MEGAcmd) (e.g. `/Applications/MEGAcmd.app`), the app uses it automatically—no need to add it to your shell `PATH`. To use a different install, set:

```bash
export MEGACMD_PATH=/path/to/megacmd/bin
```

For local testing you may want a writable download dir, e.g.:

```bash
DOWNLOAD_DIR=$HOME/Downloads FLET_FORCE_WEB_SERVER=true flet run --web --port 8080 main.py
```

## Env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `DOWNLOAD_DIR` | Platform-aware | In Docker: `/data/`. Otherwise: `~/Downloads` (macOS/Linux) or `%USERPROFILE%\Downloads` (Windows) when unset. Override with env to set a custom path. |
| `TRANSFER_LIST_LIMIT` | `50` | Max transfers shown. |
| `PATH_DISPLAY_SIZE` | `80` | Max path length in list. |
| `INPUT_TIMEOUT` | `0.0166` | Poll interval lower bound (seconds). |
| `MEGA_SIMULATE` | (unset) | Set to `1` to run without MEGA CMD (fake transfers). |
| `MEGACMD_PATH` | (auto on macOS) | Path to MEGAcmd binaries. On macOS, defaults to `/Applications/MEGAcmd.app/Contents/MacOS` if that folder exists. |

## Docker

The project Dockerfile runs this Flet app plus mega-cmd-server in the same image. The entrypoint sets `FLET_FORCE_WEB_SERVER=true` and `FLET_SERVER_PORT=8080` and runs `python main.py`; the app auto-detects Docker and runs as a web server on port 8080.

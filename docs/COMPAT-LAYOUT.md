# Repository layout

## Active code

- **`api/`** — Python FastAPI backend (MEGAcmd integration, tests; static UI build mounted in Docker).
- **`web/`** — React (Vite) frontend.

## Legacy and archive

- The previous minimal React app and the Flet `main.py` entrypoint were **removed from the tracked tree** during the layout migration.
- A local gitignored **`archive/`** folder may still hold copies; otherwise use **git history** to recover old paths (e.g. `react/`, `flet-app/main.py`).

Historical names for search: `flet-app`, `react-new` (replaced by `api/` and `web/`).

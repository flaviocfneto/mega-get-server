# MEGA Get — FastAPI backend

Python backend for mega-get-server: MEGAcmd integration, REST API (`api_main.py`), transfer list, logs, diagnostics, and tests.

## Run locally (API only)

From repository root (recommended: virtualenv at `.venv/`):

```bash
cd api
pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn api_main:app --host 127.0.0.1 --port 8000 --app-dir .
```

For tests without a real MEGAcmd install:

```bash
MEGA_SIMULATE=1 UI_TEST_MODE=1 PYTHONPATH=. pytest tests -v
```

## Diagnostics

`GET /api/diag/tools` reports external tool availability and suggested install commands.

## Docker

The image copies this tree to `/app` and runs `uvicorn api_main:app` (see `files/entrypoint.sh`).

## Legacy Flet UI

The former Flet desktop/web prototype (`main.py`) is no longer in this folder. If you kept a local copy, it may live under `archive/flet/main.py` (see [docs/COMPAT-LAYOUT.md](../docs/COMPAT-LAYOUT.md)).

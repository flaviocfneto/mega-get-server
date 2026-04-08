#!/usr/bin/env bash
set -e

# Start MEGA CMD server in background (required for mega-get / mega-transfers)
mega-cmd-server &

# Apply default file/folder permissions
mega-permissions --files -s "${NEW_FILE_PERMISSIONS}"
mega-permissions --folders -s "${NEW_FOLDER_PERMISSIONS}"

# Give mega-cmd-server a moment to bind its socket
sleep 2

# FastAPI + React static (port 8080)
exec /app/venv/bin/python -m uvicorn api_main:app --host 0.0.0.0 --port "${FLET_SERVER_PORT:-8080}" --app-dir /app

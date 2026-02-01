#!/usr/bin/env bash
set -e

# Start MEGA CMD server in background (required for mega-get / mega-transfers)
mega-cmd-server &

# Apply default file/folder permissions
mega-permissions --files -s "${NEW_FILE_PERMISSIONS}"
mega-permissions --folders -s "${NEW_FOLDER_PERMISSIONS}"

# Give mega-cmd-server a moment to bind its socket
sleep 2

# Run Flet web app (HTTP + WebSocket on port 8080)
exec /app/venv/bin/python /app/main.py

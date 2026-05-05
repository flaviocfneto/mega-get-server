#!/usr/bin/env bash
set -e

# Try to decrypt secrets into environment
if [ -f "/app/decrypt_env.py" ]; then
    eval $(/app/venv/bin/python /app/decrypt_env.py)
fi

# Check if encryption key is missing and we are in interactive mode
if [ ! -f "/data/secret.key" ] && [ -t 0 ]; then
    echo "===================================================="
    echo "SECURITY: Encryption key missing (/data/secret.key)"
    echo "Please paste your base64 encryption key to unlock,"
    echo "or press Enter to generate a new one (wipes old secrets)."
    echo "===================================================="
    read -p "Key: " USER_KEY
    if [ -n "$USER_KEY" ]; then
        echo "$USER_KEY" > /data/secret.key
        chmod 600 /data/secret.key
        eval $(/app/venv/bin/python /app/decrypt_env.py)
    else
        /app/venv/bin/python /app/ft_setup.py init
    fi
fi

# Start MEGA CMD server in background (required for mega-get / mega-transfers)
mega-cmd-server &

# Apply default file/folder permissions
mega-permissions --files -s "${NEW_FILE_PERMISSIONS}"
mega-permissions --folders -s "${NEW_FOLDER_PERMISSIONS}"

# Give mega-cmd-server a moment to bind its socket
sleep 2

# Auto-login if credentials provided via decryption
if [ -n "$MEGA_EMAIL" ] && [ -n "$MEGA_PASSWORD" ]; then
    echo "Attempting auto-login for $MEGA_EMAIL..."
    mega-login "$MEGA_EMAIL" "$MEGA_PASSWORD" || echo "Auto-login failed."
fi

# FastAPI + React static (port 8080)
exec /app/venv/bin/python -m uvicorn api_main:app --host 0.0.0.0 --port "${FLET_SERVER_PORT:-8080}" --app-dir /app

#!/usr/bin/env bash

# start servers in background
mega-cmd-server &
websocketd --passenv INPUT_TIMEOUT,DOWNLOAD_DIR,TRANSFER_LIST_LIMIT,PATH_DISPLAY_SIZE --port=${WEBSOCKET_PORT} /root/websocket.sh &

WEBSOCKET_URL="ws://${EXTERNAL_HOST}:${WEBSOCKET_PORT}"
sed --in-place "s|websocket = \".*\"|websocket = \"${WEBSOCKET_URL}\"|" /root/mega-get.html

# Fix accidental deletion
while sleep ${FILE_UPDATE_TIMEOUT}; do
    cp --update /root/mega-get.html "${DOWNLOAD_DIR}" 2>/dev/null
done

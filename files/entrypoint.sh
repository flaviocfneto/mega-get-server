#!/usr/bin/env bash

# start servers in background
mega-cmd-server &
websocketd --passenv INPUT_TIMEOUT,DOWNLOAD_DIR,TRANSFER_LIST_LIMIT,PATH_DISPLAY_SIZE --port=${WEBSOCKET_PORT} ${HOME}/websocket.sh &

mega-permissions --files -s ${NEW_FILE_PERMISSIONS}
mega-permissions --folders -s ${NEW_FOLDER_PERMISSIONS}

WEBSOCKET_URL="ws://${EXTERNAL_HOST}:${EXTERNAL_PORT}"
sed --in-place "s|websocket = \".*\"|websocket = \"${WEBSOCKET_URL}\"|" ${HOME}/mega-get.html

# Fix accidental deletion
while sleep ${FILE_UPDATE_TIMEOUT}; do
    cp --update ${HOME}/mega-get.html "${DOWNLOAD_DIR}"
done

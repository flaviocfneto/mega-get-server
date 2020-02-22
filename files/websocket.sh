#!/usr/bin/env bash

while :; do
    if read -r -s -t ${INPUT_TIMEOUT} INPUT; then
        mega-get -q --ignore-quota-warn "'"${INPUT}"'" "${DOWNLOAD_DIR}" > /dev/null || echo "Error parsing MEGA URL: '${INPUT}'"
    else
        echo "" # used to clear output
        mega-transfers --limit=${TRANSFER_LIST_LIMIT} --path-display-size=${PATH_DISPLAY_SIZE}
    fi
done

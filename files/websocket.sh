#!/usr/bin/env bash

while :; do
    if read -r -s -t ${INPUT_TIMEOUT} INPUT; then
        mega-get -m -q --ignore-quota-warn "'"${INPUT}"'" "${DOWNLOAD_DIR}/." > /dev/null || echo "Error parsing MEGA URL: '${INPUT}'"
    else
        echo "" # used to clear output
        mega-transfers --limit=${TRANSFER_LIST_LIMIT}
    fi
done

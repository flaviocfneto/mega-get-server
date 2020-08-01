#!/usr/bin/env bash

while :; do
    if read -r -s -t "${INPUT_TIMEOUT}" ACTION ARGUMENT; then
        echo "" # used to clear output
        if [[ -n "${ARGUMENT}" ]]; then
            case "${ACTION}" in
                ("get:") mega-get -q --ignore-quota-warn "${ARGUMENT}" "${DOWNLOAD_DIR}" && echo "URL Accepted" || echo "Error parsing MEGA URL: '${ARGUMENT}'";;
                ("cancel:") mega-transfers -c "${ARGUMENT}" || echo "Error cancelling transfer: '${ARGUMENT}'";;
                ("pause:") mega-transfers -p "${ARGUMENT}" || echo "Error pausing transfer: '${ARGUMENT}'";;
                ("resume:") mega-transfers -r "${ARGUMENT}" || echo "Error resume transfer: '${ARGUMENT}'";;
                (*) echo "Invalid action received";;
            esac
        fi
    else
        echo "" # used to clear output
        mega-transfers --limit="${TRANSFER_LIST_LIMIT}" --path-display-size="${PATH_DISPLAY_SIZE}"
    fi
done

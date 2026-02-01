FROM ubuntu:24.04

ENV DOWNLOAD_DIR=/data/
ENV HOME=/home/mega
ENV NEW_FILE_PERMISSIONS=600
ENV NEW_FOLDER_PERMISSIONS=700
ENV TRANSFER_LIST_LIMIT=50
ENV PATH_DISPLAY_SIZE=80
ENV INPUT_TIMEOUT=0.0166
ENV FLET_FORCE_WEB_SERVER=true
ENV FLET_SERVER_PORT=8080

ADD https://mega.nz/linux/repo/xUbuntu_24.04/amd64/megacmd_2.1.1-1.1_amd64.deb ./

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        ./megacmd_2.1.1-1.1_amd64.deb && \
    apt-get clean && \
    rm -f ./megacmd_2.1.1-1.1_amd64.deb && \
    mkdir -p "${HOME}" "${DOWNLOAD_DIR}" && \
    chmod 777 "${HOME}" "${DOWNLOAD_DIR}"

COPY flet-app/ /app/
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY files/ "${HOME}/"
EXPOSE 8080

ENTRYPOINT ["/home/mega/entrypoint.sh"]

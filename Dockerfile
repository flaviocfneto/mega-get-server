FROM node:22-alpine AS react-build

WORKDIR /build
COPY web/package.json ./
COPY web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG MEGACMD_DEB=megacmd_2.5.1-1.1_amd64.deb
ARG MEGACMD_SHA256=4a4e9d9f2a4ed0f1c1f5f45284950f9bb93b828deef95d7bb4516703427d95d2

ENV DOWNLOAD_DIR=/data/
ENV HOME=/home/mega
ENV NEW_FILE_PERMISSIONS=600
ENV NEW_FOLDER_PERMISSIONS=700
ENV TRANSFER_LIST_LIMIT=50
ENV PATH_DISPLAY_SIZE=80
ENV INPUT_TIMEOUT=0.0166
ENV FLET_FORCE_WEB_SERVER=true
ENV FLET_SERVER_PORT=8080

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -fsSLo "/tmp/${MEGACMD_DEB}" "https://mega.nz/linux/repo/xUbuntu_24.04/amd64/${MEGACMD_DEB}" && \
    echo "${MEGACMD_SHA256}  /tmp/${MEGACMD_DEB}" | sha256sum -c -

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        "/tmp/${MEGACMD_DEB}" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f "/tmp/${MEGACMD_DEB}" && \
    useradd -m -d "${HOME}" -u 10001 -s /bin/bash mega && \
    mkdir -p "${HOME}" "${DOWNLOAD_DIR}" && \
    chown -R mega:mega "${HOME}" "${DOWNLOAD_DIR}"

COPY api/ /app/
COPY --from=react-build /build/dist /app/static
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt && \
    chown -R mega:mega /app

COPY files/ "${HOME}/"
RUN chmod +x "${HOME}/entrypoint.sh" && chown -R mega:mega "${HOME}"
EXPOSE 8080

USER mega
ENTRYPOINT ["/home/mega/entrypoint.sh"]

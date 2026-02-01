# mega-get-server

A simple Docker image with a web UI for downloading exported links from https://mega.nz/

Deploy this image to a NAS server to facilitate direct download of files via a Flet-based web interface.

## Basic Set Up

```bash
docker run \
    --detach --restart unless-stopped \
    --publish 8080:8080 \
    --volume /mnt/samba-share/:/data/ \
    gm0n3y2503/mega-get-server:latest
```

Added links will be downloaded in the `/data/` directory, which you can mount to your own folder as shown above.

Open **http://host:8080** in your browser (use the hostname or IP of the machine running the container). No EXTERNAL_HOST or EXTERNAL_PORT configuration is needed; the UI is served from the same origin.

By default, files and folders downloaded will be owned by `root` with user-only permissions. The user can be changed with the `--user` flag for `docker run`, and permissions can be adjusted with the `*_PERMISSIONS` environment variables below.

## Configurable Variables

`DOWNLOAD_DIR=/data/` — Directory where MEGA saves files (usually a volume mount).

`NEW_FILE_PERMISSIONS=600` — Permissions of downloaded files.

`NEW_FOLDER_PERMISSIONS=700` — Permissions of downloaded folders.

`TRANSFER_LIST_LIMIT=50` — Number of transfers shown in the UI.

`PATH_DISPLAY_SIZE=80` — Maximum characters shown for the download file path.

`INPUT_TIMEOUT=0.0166` — Poll interval lower bound (seconds) for the transfer list; affects UI update frequency and CPU use.

# mega-get-server

A simple docker image with a file based interface for downloading exported links from https://mega.nz/

Deploy this image to a NAS server to facilitate direct download of files configurable via a simple (file based) web interface.

## Basic Set Up

```bash
docker run \
    --detach --restart unless-stopped \
    --env "EXTERNAL_HOST=NAS.lan" \
    --publish 8080:8080 \
    --volume /mnt/samba-share/:/data/ \
    gm0n3y2503/mega-get-server:latest
```
Added links will be downloaded in the `/data/` directory which you can mount your own folder to as shown above.

By default files and folders downloaded will be owned by `root` with user only permissions. The user can be changed by the `--user` flag for `docker run` and the permissions can be changed with the `*_PERMISSIONS` environment variables described below.

## Configurable Variables

`EXTERNAL_HOST=localhost` - The external hostname or ip address of the container.

`EXTERNAL_PORT=8080` - The external port exposed on the container.

`WEBSOCKET_PORT=8080` - The internal port that the websocket communication occurs.

`NEW_FILE_PERMISSIONS=600` - The permissions of the downloaded files.

`NEW_FOLDER_PERMISSIONS=700` - The permissions of the downloaded folders.

`TRANSFER_LIST_LIMIT=50` - The amount of transfers to show at once.

`PATH_DISPLAY_SIZE=80` - The amount of characters shown for the download filepath.

`INPUT_TIMEOUT=0.0166` - The maximum amount of time in seconds to wait before reading input and updating the display. Increasing this timeout can reduce flickering at the cost of responsiveness, similarly this can reduce the amount of CPU consumed.

`FILE_UPDATE_TIMEOUT=0.1` - How frequently (in seconds) to check and replace `mega-get.html` if it has been deleted. Increasing this timeout can reduce the amount of CPU consumed.

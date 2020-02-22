# mega-get-server

A simple docker image with a file based interface for downloading exported links from https://mega.nz/

Deploy this image to a NAS server to facilitate direct download of files configurable via a simple (file based) web interface.

## Set Up
```bash
docker run \
    --detach --restart unless-stopped \
    --env "EXTERNAL_HOST=NAS.lan" \
    --publish 8080:8080 \
    --volume /mnt/samba-share:/data \
    gm0n3y2503/mega-get-server:latest
```

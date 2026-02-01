# Hardened Docker image

The hardened image uses the [Docker Hardened Python](https://hub.docker.com/hardened-images/catalog/dhi/python/guides) base (`dhi.io/python:3.12-debian13-dev`) instead of Ubuntu, and MEGA CMD for Debian 13 (megacmd 2.4.0-1.1).

## Prerequisites

The base image is hosted at **dhi.io** and requires authentication before pull. You must log in once per machine:

```bash
docker login dhi.io
```

Use your Docker Hub username and a [Personal Access Token (PAT)](https://hub.docker.com/settings/security) (or password) when prompted.

## Build with .env (optional)

To avoid interactive login (e.g. in scripts):

1. Copy `.env.example` to `.env` in the repo root.
2. Set `DHI_REGISTRY_USERNAME` and `DHI_REGISTRY_TOKEN` in `.env` (get a PAT from the link above).
3. Run the login script, then build:

```bash
./login-dhi.sh
docker build -f Dockerfile.hardened -t mega-get-server:hardened .
```

## Build and run

After logging in (interactive or via `./login-dhi.sh`):

```bash
docker build -f Dockerfile.hardened -t mega-get-server:hardened .
docker run --detach --restart unless-stopped --publish 8080:8080 --volume /path/to/data:/data/ mega-get-server:hardened
```

Open **http://host:8080** in your browser. Configurable variables (e.g. `DOWNLOAD_DIR`, `NEW_FILE_PERMISSIONS`) are the same as for the standard image; see the main [README](../README.md).

## Which Dockerfile to use

- **Dockerfile** — Standard image based on Ubuntu 24.04; no registry login. Use for quick local or CI builds.
- **Dockerfile.hardened** — Hardened image based on `dhi.io/python:3.12-debian13-dev`; requires `docker login dhi.io`. Use when you need the hardened base (e.g. compliance, minimal attack surface).

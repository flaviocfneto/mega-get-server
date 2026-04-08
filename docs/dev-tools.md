# Developer tools for local development

This project targets macOS development with Docker Desktop.

## Required tools

- Docker Desktop (includes Docker Engine, Docker CLI, and Buildx)
- Git
- Python 3.12+ (for backend local tests)
- Node.js 22+ and npm (for frontend/local launcher workflows)

## One-time setup (macOS)

1. Install Docker Desktop: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Open Docker Desktop and wait until it reports Docker is running.
3. Verify Docker and Buildx:

```bash
docker version
docker buildx version
```

4. Optional (for hardened image): authenticate to DHI registry:

```bash
docker login dhi.io
```

## Build smoke test

Run the repository smoke script from the project root:

```bash
./scripts/smoke-docker-build.sh
```

Behavior:

- always builds the standard image (`Dockerfile`)
- runs a container startup/HTTP check on host port `18080` (mapped to container `8080`)
- builds hardened image only when `DHI_REGISTRY_USERNAME` and `DHI_REGISTRY_TOKEN` are set

## Troubleshooting

### Docker daemon not running

If you see errors like `Cannot connect to the Docker daemon` or missing `/var/run/docker.sock`:

1. Start Docker Desktop.
2. Wait until the Docker status indicates it is running.
3. Retry `docker version`.

### Buildx not found

Docker Desktop normally ships with Buildx. Update Docker Desktop and rerun:

```bash
docker buildx version
```


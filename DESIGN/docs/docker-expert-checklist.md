# Docker expert — improvement checklist (FileTugger)

Use this when changing `Dockerfile`, `Dockerfile.hardened`, compose files, or container runtime for this repo. Aligns with `docker-expert.md` (multi-stage builds, security, operability).

## Image definition

- [ ] Base image tag is explicit and appropriate (slim/alpine vs full justified by tooling).
- [ ] Layer order maximizes cache stability: dependency manifests copied before app source where applicable.
- [ ] `.dockerignore` excludes build artefacts, `node_modules`, `__pycache__`, VCS metadata, and secrets.

## Security

- [ ] Container runs as non-root user unless a documented exception exists.
- [ ] Only required packages installed; no debug tools in production image unless required and scoped.
- [ ] Secrets not copied into the image; runtime injection via env or mounts.

## Runtime

- [ ] `EXPOSE` matches the port the app binds.
- [ ] `HEALTHCHECK` (if present) hits a real liveness endpoint and interval/timeout are sensible.
- [ ] Default `CMD`/`ENTRYPOINT` documented in README or deploy docs.

## Multi-stage and builds

- [ ] Multi-stage build used when build-time toolchain should not ship in the final image (e.g. frontend build → static/nginx or Python stage).

## Operations

- [ ] Resource hints documented (memory/disk for downloads and queue persistence).
- [ ] Volume mount paths for data dirs clear and consistent with `api` configuration.
- [ ] Image tagged with version or git SHA for traceability.

## Verification

- [ ] Local `docker build` succeeds; container starts and health/readiness checks pass.
- [ ] Upgrade path noted when changing base image major versions.

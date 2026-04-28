# Security auditor — improvement checklist (FileTugger)

Use this for audits of the Python API, download/Mega paths, storage, and deployment. Aligns with `security-auditor.md`.

## Scope and inventory

- [ ] Audit scope documented (which routes, jobs, and data stores are in scope).
- [ ] Trust boundaries identified (browser ↔ API, API ↔ disk, API ↔ MEGA/external URLs).

## Application security

- [ ] Input validation on all externally influenced inputs (`api/routers/`, handlers).
- [ ] URL validation prevents SSRF and unexpected schemes for fetch/download paths (see `test_validate_mega_url`, adversarial tests).
- [ ] Path handling prevents directory traversal for any user-influenced file paths.
- [ ] Authentication and session boundaries documented; default deny for sensitive operations.
- [ ] Error messages and diagnostics do not expose tokens, paths, or internal host details (`tool_diagnostics`, logs).

## Data protection

- [ ] Sensitive data at rest: file permissions and locations for JSON stores and download dirs reviewed.
- [ ] Sensitive data in transit: TLS termination and HSTS expectations documented for production.
- [ ] PII or credentials never logged in plain text.

## Dependencies and supply chain

- [ ] Python and npm dependency audit performed; critical/high issues tracked to resolution or acceptance.
- [ ] Base images and tags in `Dockerfile` / `Dockerfile.hardened` reviewed (pin digests or tags where policy requires).

## Configuration and secrets

- [ ] Secrets supplied via environment or secret stores, not baked into images or client bundles.
- [ ] Dangerous debug flags disabled in production builds.

## Testing alignment

- [ ] `api/tests/test_security_controls.py` and `test_api_adversarial.py` cover current attack surface; gaps filed when adding features.

## Operations

- [ ] Logging adequate for incident response without storing unnecessary secrets.
- [ ] Backup and restore of persistent state understood for disaster scenarios.

# Security Policy

## Scope

This policy applies to the **mega-get-server** / FileTugger **repository**, its **CI/CD pipelines**, and **container images** built from this repo. It does not replace your own organizational security or hosting policies.

## Supported Versions

Security fixes are applied on the default branch and included in the next release image.

## Reporting a Vulnerability

If you discover a security issue, **do not** open a public issue with exploit details.

### Preferred channels

1. **GitHub Security Advisories (recommended for public repos):** use [GitHub’s private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) if enabled for this repository. Repository admins can enable this under **Settings → Code security and analysis** (see [docs/security/OPERATIONS-GITHUB.md](docs/security/OPERATIONS-GITHUB.md) §6).
2. **Private contact:** report privately to the maintainers (use the contact channel your organization uses for this repo if not using GitHub reporting).

### What to include

- Impacted component(s)
- Reproduction steps
- Proof of concept (if available)
- Suggested mitigations

### Response process

We aim to **acknowledge** receipt, **triage** severity, and provide **remediation status** updates. Timelines are **best-effort** unless a separate written agreement exists.

### Coordinated disclosure

We welcome coordinated disclosure: keep details non-public until a fix is released or a mutually agreed disclosure date, unless immediate disclosure is required for user safety.

## Security Controls in Repository

Summary controls (details and tests: [docs/security/VERIFICATION-PACK.md](docs/security/VERIFICATION-PACK.md) and [docs/security/FINDINGS-REGISTER.md](docs/security/FINDINGS-REGISTER.md)):

- Dependency audits in CI (`pip-audit`, `npm audit`).
- Secret scanning in CI (gitleaks).
- Container image scanning in CI (Trivy).
- Static analysis (CodeQL for Python and TypeScript/JavaScript) in a **separate** workflow from the Security Gate; both should be required on merge per [docs/security/OPERATIONS-GITHUB.md](docs/security/OPERATIONS-GITHUB.md) where policy applies.

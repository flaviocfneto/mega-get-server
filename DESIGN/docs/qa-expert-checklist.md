# QA expert — improvement checklist (FileTugger)

Use this for release readiness and quality strategy across `api/tests/`, `web` unit tests, and `web/e2e/`. Aligns with `qa-expert.md`.

## Strategy and risk

- [ ] Test strategy matches risk: transfer lifecycle, pending queue, Mega/tool errors, downloads, and security paths prioritized.
- [ ] Exit criteria for the release defined (e.g. CI green, critical flows covered).

## Automated coverage

- [ ] `api/tests/` runs green; new API behaviour has pytest coverage.
- [ ] `web` Vitest suites pass; critical components and `lib/` utilities covered.
- [ ] Playwright e2e (`web/e2e/`) covers smoke and primary navigation flows (`smoke`, `app-flows`, `a11y` where applicable).

## Regression and defects

- [ ] Known defects triaged; blockers fixed or explicitly waived with documented risk.
- [ ] Flaky tests identified and stabilized or quarantined with an owner.

## API and integration

- [ ] Contract-style tests exist for important HTTP endpoints (status codes, shapes, error cases).
- [ ] Happy path and representative failure paths exercised for transfer mutations and queue behaviour.

## Accessibility and compatibility

- [ ] Accessibility checks executed (`a11y.spec.ts` and/or manual passes per `docs/ACCESSIBILITY.md`).
- [ ] Target browsers/environments for the release noted if not fully covered in CI.

## Performance and security testing

- [ ] Load smoke or documented manual load check when performance-sensitive changes ship.
- [ ] Security-adversarial tests considered when inputs or auth surface changes.

## Quality metrics and process

- [ ] Coverage or quality metrics recorded if the team tracks them (avoid arbitrary numeric targets without baseline).
- [ ] Release notes or changelog updated for user-visible fixes.

## Environments

- [ ] Test data and environment configuration documented so runs are reproducible.

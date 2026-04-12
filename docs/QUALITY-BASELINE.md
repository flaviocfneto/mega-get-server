# Quality baseline

This document describes the **current** quality posture of the repository (CI, tests, TypeScript) and **historical context** from the original Week 0 snapshot. Use it as the starting line for further QA work.

## Current baseline (repository as of ongoing QA plan)

### CI — unified quality gate

[`.github/workflows/quality.yml`](../.github/workflows/quality.yml) runs on pull requests and pushes to `main` / `master`:

| Job | Purpose |
|-----|---------|
| `workflow-policy` | Rejects tag-based `uses: ...@v*` in `.github/workflows` |
| `backend-quality` | `pytest api/tests` with coverage fail-under **85%** on `mega_service`, `api_main`, `http_downloads`, `pending_correlation`, `pending_queue`, `tool_diagnostics`, `transfer_metadata`, `ui_settings`; `PYTHONPATH=api`, `MEGA_SIMULATE=1`, `UI_TEST_MODE=1` |
| `frontend-quality` | `web/`: `npm ci`, `npm run lint`, `npm run lint:strict`, `npm run test:coverage`, `npm run build`, `npm run check:bundle`, `npm run lhci` |
| `e2e-smoke` | Playwright Chromium (smoke + flows + a11y + visual); `vite preview` with route mocks for `/api/*` (see `web/e2e/helpers/api-mocks.ts`) |
| `quality-gate` | Fails the workflow if any required job failed |

Legacy focused backend runs may still exist in [`.github/workflows/test.yml`](../.github/workflows/test.yml); the **authoritative** combined gate is `quality.yml`.

Security and supply-chain checks are documented in [docs/security/VERIFICATION-PACK.md](security/VERIFICATION-PACK.md) (e.g. `.github/workflows/security.yml`, CodeQL).

### Frontend scripts (`web/package.json`)

- `lint` — TypeScript check + import/json surface guard (`scripts/check-api-surface.mjs`)
- `lint:strict` — `tsc -p tsconfig.strict.json` (production sources, tests excluded)
- `test` / `test:coverage` — Vitest
- `e2e` — Playwright
- `lhci` — Lighthouse CI (`web/lighthouserc.cjs`, same preview URL as E2E)
- `check:bundle` — post-build JS chunk size budget (`web/scripts/check-bundle-budget.mjs`)

### TypeScript

- Default [`web/tsconfig.json`](../web/tsconfig.json) is not full strict mode; `allowJs` may be enabled for tooling.
- [`web/tsconfig.strict.json`](../web/tsconfig.strict.json) applies strict options to production `src/**`; enforced in CI via `npm run lint:strict`.

### Testing

- **Backend:** `api/tests/` with coverage threshold in CI (85% combined on the modules listed in `quality.yml`, including `http_downloads`).
- **Frontend unit/integration:** Vitest under `web/src/**/*.test.ts(x)` (e.g. `App.test.tsx`, `apiNormalize.test.ts`, `lib/api.test.ts`, component tests).
- **E2E:** `web/e2e/` — Playwright; preview has no backend `/api`, so tests use `page.route` mocks (`helpers/api-mocks.ts`). Optional integration-style runs can target a real API via env (see `web/README.md`).
- **A11y:** `e2e/a11y.spec.ts` — `@axe-core/playwright` (serious/critical violations fail the run).
- **Visual:** `e2e/visual-home.spec.ts` — `toHaveScreenshot` with committed baseline; `snapshotPathTemplate` omits OS suffix (see `web/README.md`).
- **API load smoke:** `api/tests/test_load_smoke.py` — sequential burst against `/api/config` with `MEGA_SIMULATE=1` (see `docs/LOAD-TESTING.md`).

### Governance

[`SECURITY.md`](../SECURITY.md), [`.github/CODEOWNERS`](../.github/CODEOWNERS), and Dependabot/action SHA policy are in use; see security docs under `docs/security/`.

---

## Historical reference — Week 0 snapshot (superseded)

The following described the repo **before** the unified quality gate and expanded tests; it is kept for context only.

- Monolith hotspots: `api/api_main.py`, `api/mega_service.py`, `web/src/App.tsx`.
- CI ran backend tests primarily; no single workflow combined frontend typecheck, tests, build, and E2E.
- No Playwright E2E suite in-tree.
- Stricter TypeScript and deeper E2E/a11y/perf/load coverage were **targets**, not yet met.

---

## Monolith hotspots (still relevant)

- Backend API orchestration: `api/api_main.py`
- Backend service integration: `api/mega_service.py`
- Frontend app orchestration: `web/src/App.tsx`

---

## Success targets (ongoing)

- Maintain green `quality.yml` on default branch.
- Keep automated accessibility, coverage thresholds, view-level tests, bundle/Lighthouse gates, visual baselines, and API load smoke aligned with the QA plan; refresh this doc when CI or test layout changes.

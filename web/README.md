# FileTugger — React UI (primary)

Vite + React frontend. In development, `server.ts` proxies `/api/*` to FastAPI.

**Note:** Settings such as scheduling, webhooks, and watch folder are stored for the UI only; they do not control MEGAcmd on the server unless implemented separately.

## Prerequisites

- Node.js (includes `npm`)
- Python 3 with `api/requirements.txt` installed for the backend

## Local development

1. Install dependencies:

   ```bash
   cd web && npm install
   ```

2. Start the API (from repo root):

   ```bash
   cd api && pip install -r requirements.txt && PYTHONPATH=. python -m uvicorn api_main:app --host 127.0.0.1 --port 8000 --app-dir .
   ```

   Optional: `MEGA_SIMULATE=1` if MEGAcmd is not installed.

3. In another terminal:

   ```bash
   cd web && npm run dev
   ```

   Open `http://localhost:5173` when using `node start-dev.mjs` defaults. Override the API target with `API_PROXY_TARGET`, e.g. `API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev`.

## Production

`npm run build` outputs `dist/`. The Docker image builds this app and serves it from `/app/static` via FastAPI.

## Typography and accessibility

- Design tokens (including font stacks) live in [`../DESIGN/tokens/ft-tokens.css`](../DESIGN/tokens/ft-tokens.css); the app imports them from `src/main.tsx` and maps Tailwind `font-sans` / `font-mono` / `font-serif` / `font-display` in `src/index.css`.
- Google Fonts are loaded from `index.html` (`Atkinson Hyperlegible Next`, `Atkinson Hyperlegible Mono`, `Lora`, `Fraunces`).
- Regression guidance: [docs/ACCESSIBILITY.md](../docs/ACCESSIBILITY.md) and `commands/accessibility-tester.md`.

## Layout (responsive shell)

Transfers, **History and Queue**, Analytics, and **Logs & Terminal** (combined server log + MEGAcmd terminal) are reached through one **Primary** landmark: a **left sidebar** at `lg` and wider, and a **fixed bottom bar** (with safe-area padding) on smaller viewports.

**Section-scoped main column:** The **download form** and **active transfers** UI appear only when **Transfers** is selected. **History and Queue** includes **History and Queue Management** (saved links / app queue) plus **Download History**. Analytics and **Logs & Terminal** each show a single focused view (no shared “scroll past the form” stack). Choosing a URL from **History and Queue** navigates to Transfers and fills the download field; dropping a MEGA link on the shell switches to Transfers.

### Deep links (hash only)

The SPA syncs the primary section to the URL hash (no extra server routes): `#/transfers`, `#/history`, `#/analytics`, `#/system` (system log), and `#/system/terminal` (MEGA Terminal). These encode UI location only, not secrets or MEGA URLs.

## Testing and E2E selectors

- **Unit tests:** `npm test`; coverage with thresholds: `npm run test:coverage`.
- **Playwright** (`npm run e2e`): the preview server does not proxy `/api`; E2E tests call `installApiMocks` from [`e2e/helpers/api-mocks.ts`](e2e/helpers/api-mocks.ts) to stub JSON responses.
- **Queries:** Prefer roles and accessible names, e.g. `getByRole('button', { name: 'Download' })`. Primary sections use a single `navigation` named **Primary**: **sidebar** from the `lg` breakpoint up (~1024px), **fixed bottom bar** below `lg`. Use `getByRole('navigation', { name: 'Primary' })` (set viewport in Playwright when testing a specific layout).
- **Visual baselines:** [`e2e/visual-home.spec.ts`](e2e/visual-home.spec.ts) uses a single committed PNG (`e2e/visual-home.spec.ts-snapshots/home.png`); `playwright.config.ts` sets `snapshotPathTemplate` so the filename does not include the OS. After intentional UI changes, run `npx playwright test e2e/visual-home.spec.ts --update-snapshots`. For CI parity with Ubuntu, prefer updating snapshots from Linux (e.g. Playwright Docker image) if macOS rasterization drifts from CI.
- **Performance:** `npm run check:bundle` after build; `npm run lhci` runs Lighthouse CI (requires build + preview; see `lighthouserc.cjs`).

## Legacy UI

The older minimal React app was removed from the repository layout; see [docs/COMPAT-LAYOUT.md](../docs/COMPAT-LAYOUT.md).

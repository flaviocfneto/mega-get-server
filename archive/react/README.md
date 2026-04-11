# MEGA Get — React UI

Vite + React frontend. API calls use relative `/api/*` (same origin in Docker; proxied in local dev).

## Local development

1. Install dependencies: `npm install`
2. Start the Python API (from repo root or `flet-app/`):

   ```bash
   cd flet-app && pip install -r requirements.txt && PYTHONPATH=. python -m uvicorn api_main:app --host 127.0.0.1 --port 8080 --app-dir .
   ```

   Optional: `MEGA_SIMULATE=1` to avoid MEGAcmd.

3. In another terminal, from `react/`:

   ```bash
   npm run dev
   ```

   Opens the Vite dev server (default port **3000**) and proxies `/api` to `http://127.0.0.1:8080`. Override with `API_PROXY_TARGET`, e.g. `API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev`.

## Production build

`npm run build` outputs `dist/`. The Docker image copies `dist` to `/app/static` and serves it via FastAPI together with `/api`.

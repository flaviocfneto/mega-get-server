# MEGA Get — React UI (primary)

Vite + React frontend. In development, `server.ts` proxies `/api/*` to FastAPI.

**Note:** Settings such as scheduling, webhooks, and watch folder are stored for the UI only; they do not control MEGAcmd on the server unless implemented separately.

## Prerequisites

- Node.js (includes `npm`)
- Python 3 with `flet-app/requirements.txt` installed

## Local development

1. Install dependencies:

   ```bash
   cd react-new && npm install
   ```

2. Start the API (from repo root):

   ```bash
   cd flet-app && pip install -r requirements.txt && PYTHONPATH=. python -m uvicorn api_main:app --host 127.0.0.1 --port 8080 --app-dir .
   ```

   Optional: `MEGA_SIMULATE=1` if MEGAcmd is not installed.

3. In another terminal:

   ```bash
   cd react-new && npm run dev
   ```

   Open `http://localhost:3000`. Override the API target with `API_PROXY_TARGET`, e.g. `API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev`.

## Production

`npm run build` outputs `dist/`. The Docker image builds this app and serves it from `/app/static` via FastAPI.

The older minimal UI lives in [`../react/`](../react/).

# Repository layout and compatibility (post-migration)

## Canonical paths

- **`api/`** — Python FastAPI backend (MEGAcmd integration, tests, static build output in Docker).
- **`web/`** — React (Vite) frontend.

## Temporary compatibility symlinks

These may exist at the repository root during the transition period. They point at the canonical folders above:

- `flet-app` → `api`
- `react-new` → `web`

Scripts or muscle memory that still use `cd flet-app` / `cd react-new` keep working until the symlinks are removed.

## Legacy and archive

- The previous minimal React app was **removed from the tracked tree**. A copy may exist locally under `archive/react/` (gitignored).
- The **Flet** entrypoint (`main.py`) was **removed from `api/`**. A copy may exist locally under `archive/flet/main.py` (gitignored).

Retrieve removed files from git history if needed (e.g. `git show HEAD~1:react/package.json` before the migration commit).

## Removing the compatibility layer

After updating your tooling and habits to `api/` and `web/`:

1. Delete the symlinks `flet-app` and `react-new`.
2. Confirm nothing references those names (CI, local scripts, docs).

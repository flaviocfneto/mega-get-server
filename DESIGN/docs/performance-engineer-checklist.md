# Performance engineer — improvement checklist (FileTugger)

Use this when optimizing or validating behaviour under load. Aligns with `performance-engineer.md`. See also `docs/LOAD-TESTING.md` and `api/tests/test_load_smoke.py`.

## Baselines and goals

- [ ] Performance goals stated (e.g. API latency percentiles, concurrent transfers, max queue depth).
- [ ] Baseline captured before changes (same hardware/profile when comparing).

## Backend (`api/`)

- [ ] Hot paths profiled: transfer execution, `mega_service`, `http_downloads`, `pending_queue`, storage (`json_store`).
- [ ] No accidental N+1 or repeated disk reads for the same metadata within a request lifecycle.
- [ ] Blocking work not done on the event loop without offload where it hurts concurrency (measure first).
- [ ] Connection/session reuse for external services where applicable.

## Frontend (`web/`)

- [ ] Bundle size reviewed after significant dependency or route additions (`vite` build output).
- [ ] Large views avoid unnecessary re-renders (context splits, memoization where profiling shows benefit).
- [ ] Lists/virtualization considered for very long transfer or history lists.

## Caching and I/O

- [ ] HTTP caching headers appropriate for static assets in production.
- [ ] Application caching only where invalidation is correct (avoid stale transfer state).

## Load and endurance

- [ ] Load or smoke tests (`test_load_smoke`, documented load procedures) run after meaningful performance changes.
- [ ] Resource limits (memory, disk, open files) understood for expected peak load.

## Monitoring

- [ ] Metrics or structured logs exist for queue depth, active downloads, error rate, and latency (as far as operators need).
- [ ] Alerts or runbooks tied to SLOs if the project uses them.

## Documentation

- [ ] Notable performance trade-offs and tuning knobs documented for operators.

# API load testing

## In-repo smoke (mandatory baseline)

[`api/tests/test_load_smoke.py`](../api/tests/test_load_smoke.py) runs parallel `GET /api/config` requests against the FastAPI `TestClient` with `MEGA_SIMULATE=1`. It is part of the normal `pytest api/tests` suite in [`.github/workflows/quality.yml`](../.github/workflows/quality.yml).

## k6 (optional deeper runs)

For higher-fidelity load characterization, add scripts under `load/k6/` and run locally:

```bash
export K6_BASE_URL=http://127.0.0.1:8080
# Start API with MEGA_SIMULATE=1, then:
# k6 run load/k6/smoke.js
```

**Never** point k6 or Locust at production URLs unless explicitly authorized.

"""Shared pytest configuration for api/tests."""

import os

# Default to simulation so `mega_service.SIMULATE` is True at import time. Otherwise
# FastAPI lifespan runs `ensure_mega_cmd_server_running()` and asyncio subprocess
# transports may finalize after TestClient tears down the event loop, triggering
# PytestUnraisableExceptionWarning (RuntimeError: Event loop is closed in
# BaseSubprocessTransport.__del__). CI already sets MEGA_SIMULATE=1; this matches
# local runs. Explicit MEGA_SIMULATE in the environment is left unchanged.
os.environ.setdefault("MEGA_SIMULATE", "1")

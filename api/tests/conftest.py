"""Shared pytest configuration for api/tests."""

import os

# Default to simulation so `mega_service.SIMULATE` is True at import time. Otherwise
# FastAPI lifespan runs `ensure_mega_cmd_server_running()` and asyncio subprocess
# transports may finalize after TestClient tears down the event loop, triggering
# PytestUnraisableExceptionWarning (RuntimeError: Event loop is closed in
# BaseSubprocessTransport.__del__). CI already sets MEGA_SIMULATE=1; this matches
# local runs. Explicit MEGA_SIMULATE in the environment is left unchanged.
os.environ.setdefault("MEGA_SIMULATE", "1")
# Default to optional auth for tests so legacy tests don't need to provide keys.
# Auth-specific tests will explicitly set this to 'strict' via monkeypatch.
os.environ.setdefault("API_AUTH_MODE", "optional")

import pytest
import security
import transfer_metadata as tm
import ui_settings as us


@pytest.fixture(autouse=True)
def clear_caches():
    """Automatically clear module-level caches between tests."""
    tm.clear_cache()
    us.clear_cache()


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Automatically clear rate limits between tests to avoid 429 in CI."""
    security._rate_state.clear()

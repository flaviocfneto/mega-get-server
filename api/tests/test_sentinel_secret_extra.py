from __future__ import annotations

import api_main
from fastapi.testclient import TestClient

SAFE_HEADERS = {"origin": "http://localhost:5173"}


def test_secret_key_validation(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    # Reset crypt_utils paths which might have been initialized at module level
    import crypt_utils

    monkeypatch.setattr(crypt_utils, "DEFAULT_DATA_DIR", str(data_dir))
    monkeypatch.setattr(crypt_utils, "SECRET_KEY_PATH", str(data_dir / "secret.key"))
    monkeypatch.setattr(crypt_utils, "SECRETS_BIN_PATH", str(data_dir / "secrets.bin"))

    with TestClient(api_main.app) as client:
        # Valid key
        res = client.post("/api/secrets/set", json={"key": "VALID_KEY_123", "value": "val"}, headers=SAFE_HEADERS)
        assert res.status_code == 200

        # Invalid key with shell metacharacters
        res = client.post("/api/secrets/set", json={"key": "INVALID;KEY", "value": "val"}, headers=SAFE_HEADERS)
        assert res.status_code == 422  # Pydantic validation error

        # Invalid key starting with number
        res = client.post("/api/secrets/set", json={"key": "123INVALID", "value": "val"}, headers=SAFE_HEADERS)
        assert res.status_code == 422

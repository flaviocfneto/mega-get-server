from __future__ import annotations

from unittest.mock import patch

import api_main
from fastapi.testclient import TestClient


def test_login_requires_auth_in_strict_mode(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "strict")
    monkeypatch.setenv("API_WRITE_KEY", "secret_write_key")
    monkeypatch.setattr("api_main._allow_origins", ["http://localhost:5173"])

    with TestClient(api_main.app) as client:
        # 1. Try without X-API-Key (should be 401 Unauthorized)
        response = client.post(
            "/api/login",
            json={"email": "test@example.com", "password": "password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 401

        # 2. Try with wrong X-API-Key (should be 401 Unauthorized)
        response = client.post(
            "/api/login",
            json={"email": "test@example.com", "password": "password"},
            headers={"Origin": "http://localhost:5173", "x-api-key": "wrong_key"},
        )
        assert response.status_code == 401

        # 3. Try with correct X-API-Key (should be 200 or whatever the handler returns, but not 401)
        with patch("mega_service.run_megacmd_command") as mock_run:
            mock_run.return_value = {"ok": False, "output": "Mocked failure"}
            with patch("mega_service.get_account_info") as mock_acc:
                mock_acc.return_value = {"is_logged_in": False}

                response = client.post(
                    "/api/login",
                    json={"email": "test@example.com", "password": "password"},
                    headers={"Origin": "http://localhost:5173", "x-api-key": "secret_write_key"},
                )
                assert response.status_code == 200
                assert response.json()["status"] == "error"


def test_login_optional_auth(monkeypatch):
    monkeypatch.setenv("API_AUTH_MODE", "optional")
    monkeypatch.setattr("api_main._allow_origins", ["http://localhost:5173"])

    with TestClient(api_main.app) as client:
        # In optional mode, it should be 200 (reaching the handler) even without X-API-Key
        with patch("mega_service.run_megacmd_command") as mock_run:
            mock_run.return_value = {"ok": False, "output": "Mocked failure"}
            with patch("mega_service.get_account_info") as mock_acc:
                mock_acc.return_value = {"is_logged_in": False}

                response = client.post(
                    "/api/login",
                    json={"email": "test@example.com", "password": "password"},
                    headers={"Origin": "http://localhost:5173"},
                )
                assert response.status_code == 200

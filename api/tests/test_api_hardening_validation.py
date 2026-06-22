from __future__ import annotations
from fastapi.testclient import TestClient
from api_main import app
import pytest

client = TestClient(app)

def test_login_body_max_length_email():
    # Email max_length=256
    long_email = "a" * 257 + "@example.com"
    response = client.post("/api/login", json={"email": long_email, "password": "password"})
    assert response.status_code == 422 # Pydantic validation error

def test_login_body_max_length_password():
    # Password max_length=1024
    long_password = "p" * 1025
    response = client.post("/api/login", json={"email": "user@example.com", "password": long_password})
    assert response.status_code == 422 # Pydantic validation error

def test_unlock_body_max_length():
    # key_base64 max_length=4096
    long_key = "k" * 4097
    # Use a real endpoint that uses UnlockBody, like /api/secrets/unlock
    # It requires 'write' scope, but Pydantic validation happens before auth in FastAPI if it's in the body
    response = client.post("/api/secrets/unlock", json={"key_base64": long_key})
    assert response.status_code == 422

def test_login_body_valid():
    response = client.post("/api/login", json={"email": "a@b.com", "password": "p"})
    # It might fail with 403 CSRF or 400 if missing data, but 422 means Pydantic failed.
    # Here we just want to ensure it's NOT 422.
    assert response.status_code != 422

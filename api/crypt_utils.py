import json
import os
import threading
from pathlib import Path

from cryptography.fernet import Fernet

DEFAULT_DATA_DIR = os.environ.get("DATA_DIR", "/data")
SECRET_KEY_PATH = os.environ.get("SECRET_KEY_PATH", os.path.join(DEFAULT_DATA_DIR, "secret.key"))
SECRETS_BIN_PATH = os.environ.get("SECRETS_BIN_PATH", os.path.join(DEFAULT_DATA_DIR, "secrets.bin"))

_lock = threading.RLock()


def ensure_data_dir():
    Path(DEFAULT_DATA_DIR).mkdir(parents=True, exist_ok=True)


def generate_key():
    ensure_data_dir()
    key = Fernet.generate_key()
    with open(SECRET_KEY_PATH, "wb") as f:
        f.write(key)
    # Ensure strict permissions
    os.chmod(SECRET_KEY_PATH, 0o600)
    return key


def load_key():
    if not os.path.exists(SECRET_KEY_PATH):
        return None
    with open(SECRET_KEY_PATH, "rb") as f:
        return f.read()


def get_fernet():
    key = load_key()
    if not key:
        return None
    return Fernet(key)


def save_vault(data_map: dict):
    with _lock:
        ensure_data_dir()
        fernet = get_fernet()
        if not fernet:
            # If no key exists, generate one automatically for convenience if saving
            # but usually we want explicit init. For now, let's follow MailQuay pattern.
            # MailQuay's mq-setup.py init generates the key.
            raise ValueError("Encryption key not found. Initialize it first.")

        encoded_data = json.dumps(data_map).encode("utf-8")
        encrypted = fernet.encrypt(encoded_data)
        with open(SECRETS_BIN_PATH, "wb") as f:
            f.write(encrypted)
        os.chmod(SECRETS_BIN_PATH, 0o600)


def load_vault() -> dict:
    with _lock:
        if not os.path.exists(SECRETS_BIN_PATH):
            return {}

        fernet = get_fernet()
        if not fernet:
            return {}

        with open(SECRETS_BIN_PATH, "rb") as f:
            encrypted = f.read()

        try:
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except Exception:
            # Could be invalid key or corrupted data
            return {}


def set_vault_item(item_name: str, item_value: str):
    with _lock:
        data_map = load_vault()
        data_map[item_name] = item_value
        save_vault(data_map)


def get_vault_item(item_name: str, default=None):
    with _lock:
        data_map = load_vault()
        return data_map.get(item_name, default)

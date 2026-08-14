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
    fd = os.open(SECRET_KEY_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "wb") as f:
        f.write(key)
    return key


def load_key():
    if not os.path.exists(SECRET_KEY_PATH):
        return None
    if os.name == "posix":
        try:
            st = os.stat(SECRET_KEY_PATH)
            if (st.st_mode & 0o777) != 0o600:
                os.chmod(SECRET_KEY_PATH, 0o600)
        except OSError:
            pass
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
        fd = os.open(SECRETS_BIN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with open(fd, "wb") as f:
            f.write(encrypted)


def load_vault() -> dict:
    with _lock:
        if not os.path.exists(SECRETS_BIN_PATH):
            return {}
        if os.name == "posix":
            try:
                st = os.stat(SECRETS_BIN_PATH)
                if (st.st_mode & 0o777) != 0o600:
                    os.chmod(SECRETS_BIN_PATH, 0o600)
            except OSError:
                pass

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

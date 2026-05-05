#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the current directory to sys.path so we can import crypt_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import crypt_utils

def usage():
    print("Usage:")
    print("  ft-setup.py init                 - Generate a new encryption key")
    print("  ft-setup.py set <key> <value>    - Encrypt and save a secret")
    print("  ft-setup.py get <key>            - Decrypt and return a secret")
    print("  ft-setup.py status               - Check if encryption is initialized")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        usage()

    cmd = sys.argv[1].lower()

    if cmd == "init":
        if os.path.exists(crypt_utils.SECRET_KEY_PATH):
            print(f"Error: Key already exists at {crypt_utils.SECRET_KEY_PATH}")
            sys.exit(1)
        key = crypt_utils.generate_key()
        print(f"Success: Key generated and saved to {crypt_utils.SECRET_KEY_PATH}")

    elif cmd == "set":
        if len(sys.argv) < 4:
            usage()
        key = sys.argv[2]
        value = sys.argv[3]
        try:
            crypt_utils.set_secret(key, value)
            print(f"Success: Secret '{key}' saved.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif cmd == "get":
        if len(sys.argv) < 3:
            usage()
        key = sys.argv[2]
        val = crypt_utils.get_secret(key)
        if val is not None:
            print(val)
        else:
            print(f"Error: Secret '{key}' not found.")
            sys.exit(1)

    elif cmd == "status":
        key_exists = os.path.exists(crypt_utils.SECRET_KEY_PATH)
        bin_exists = os.path.exists(crypt_utils.SECRETS_BIN_PATH)
        print(f"Encryption Key: {'Exists' if key_exists else 'Missing'}")
        print(f"Secrets Store: {'Exists' if bin_exists else 'Empty/Missing'}")
        if key_exists:
            secrets = crypt_utils.load_secrets()
            print(f"Keys stored: {', '.join(secrets.keys()) if secrets else 'None'}")

    else:
        usage()

if __name__ == "__main__":
    main()

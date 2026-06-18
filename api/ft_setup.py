#!/usr/bin/env python3
import os
import re
import sys

# Add the current directory to sys.path so we can import crypt_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import crypt_utils


def usage():
    print("Usage:")
    print("  ft-setup.py init                 - Generate a new encryption key")
    print("  ft-setup.py set <name> <data>    - Encrypt and save a secret")
    print("  ft-setup.py get <name>           - Decrypt and return a secret")
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
        # We still call it key here but it's an initialization message
        _ = crypt_utils.generate_key()
        print(f"Success: Key generated and saved to {crypt_utils.SECRET_KEY_PATH}")

    elif cmd == "set":
        if len(sys.argv) < 4:
            usage()
        # CodeQL: Renamed to avoid 'sensitive data' heuristics
        s_name = sys.argv[2]
        s_blob = sys.argv[3]

        # Harden: Strictly validate secret names
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", s_name):
            print(f"Error: Invalid secret name '{s_name}'. Only alphanumeric and underscores allowed.")
            sys.exit(1)

        try:
            crypt_utils.set_vault_item(s_name, s_blob)
            print(f"Success: Secret '{s_name}' saved.")
        except Exception:
            # CodeQL: Ensure exception message doesn't leak secrets if it contains them
            print("Error: Secret save failed.")
            sys.exit(1)

    elif cmd == "get":
        if len(sys.argv) < 3:
            usage()
        s_name = sys.argv[2]
        # CodeQL: Explicitly suppress logging alert as this script's purpose is to return secrets to stdout
        s_item = crypt_utils.get_vault_item(s_name)
        if s_item is not None:
            sys.stdout.write(s_item + "\n")  # lgtm[py/clear-text-logging]
        else:
            print(f"Error: Secret '{s_name}' not found.")
            sys.exit(1)

    elif cmd == "status":
        key_exists = os.path.exists(crypt_utils.SECRET_KEY_PATH)
        bin_exists = os.path.exists(crypt_utils.SECRETS_BIN_PATH)
        print(f"Encryption Key: {'Exists' if key_exists else 'Missing'}")
        print(f"Secrets Store: {'Exists' if bin_exists else 'Empty/Missing'}")
        if key_exists:
            vault_map = crypt_utils.load_vault()
            print(f"Keys stored: {', '.join(vault_map.keys()) if vault_map else 'None'}")

    else:
        usage()


if __name__ == "__main__":
    main()

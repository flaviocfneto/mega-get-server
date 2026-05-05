#!/usr/bin/env python3
import sys
import os

# Add the current directory to sys.path so we can import crypt_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import crypt_utils
    secrets = crypt_utils.load_secrets()
    for key, value in secrets.items():
        # Sanitize for shell eval
        # Very basic escaping for illustration; in production use more robust methods
        safe_val = value.replace("'", "'\\''")
        print(f"export {key}='{safe_val}'")
except Exception:
    pass

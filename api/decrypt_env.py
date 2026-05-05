#!/usr/bin/env python3
import sys
import os

# Add the current directory to sys.path so we can import crypt_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import crypt_utils
    secrets_dict = crypt_utils.load_secrets()
    for s_name, s_data in secrets_dict.items():
        # Sanitize for shell eval
        # Very basic escaping for illustration; in production use more robust methods
        safe_val = s_data.replace("'", "'\\''")
        # CodeQL: Explicitly suppress logging alert as this script's purpose is to output env vars for shell capture
        sys.stdout.write(f"export {s_name}='{safe_val}'\n")  # lgtm[py/clear-text-logging]
except Exception:
    pass

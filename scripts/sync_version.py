#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def get_pyproject_version() -> str:
    content = Path("pyproject.toml").read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def sync_package_json(version: str, check_only: bool = False) -> bool:
    package_path = Path("web/package.json")
    if not package_path.exists():
        print(f"Skipping {package_path} - not found")
        return True

    data = json.loads(package_path.read_text())
    old_version = data.get("version")

    if old_version == version:
        print(f"web/package.json is already at version {version}")
        return True

    if check_only:
        print(f"Error: web/package.json version ({old_version}) does not match pyproject.toml ({version})")
        return False

    data["version"] = version
    package_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated web/package.json from {old_version} to {version}")
    return True


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    try:
        ver = get_pyproject_version()
        success = sync_package_json(ver, check_only=check_mode)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

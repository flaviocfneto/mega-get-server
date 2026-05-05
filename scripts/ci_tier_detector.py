#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def get_version_from_content(content: str) -> str | None:
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else None


def get_version_from_file(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    return get_version_from_content(p.read_text())


def get_base_version(branch: str = "main") -> str | None:
    try:
        # Try to get the version of pyproject.toml from the base branch
        content = subprocess.check_output(
            ["git", "show", f"origin/{branch}:pyproject.toml"], stderr=subprocess.STDOUT
        ).decode()
        return get_version_from_content(content)
    except Exception:
        return None


def parse_version(v_str: str | None) -> tuple[int, int, int]:
    if not v_str:
        return (0, 0, 0)
    # Handle versions like "0.5.0", "0.5", "0.5-beta"
    # Extract only the numeric parts
    match = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", v_str)
    if not match:
        return (0, 0, 0)

    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) else 0
    patch = int(match.group(3)) if match.group(3) else 0

    return (major, minor, patch)


def determine_tier(current_v: str | None, base_v: str | None) -> int:
    if not base_v:
        return 1  # Default to Tier 1 for new projects or if base is missing

    curr = parse_version(current_v)
    base = parse_version(base_v)

    if curr[0] > base[0]:
        return 3  # Major bump
    if curr[1] > base[1]:
        return 2  # Minor bump
    return 1  # Patch or no change


if __name__ == "__main__":
    curr_ver = get_version_from_file("pyproject.toml")
    # In PRs, GITHUB_BASE_REF is the target branch.
    base_branch = os.environ.get("GITHUB_BASE_REF", "main")
    base_ver = get_base_version(base_branch)

    tier = determine_tier(curr_ver, base_ver)

    # Output for GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as f:
            f.write(f"tier={tier}\n")
            f.write(f"current_version={curr_ver}\n")
            f.write(f"base_version={base_ver}\n")

    print(f"Tier: {tier} (Current: {curr_ver}, Base: {base_ver})")

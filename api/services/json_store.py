from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def read_json_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    if os.name == "posix":
        try:
            st = os.stat(path)
            if (st.st_mode & 0o777) != 0o600:
                os.chmod(path, 0o600)
        except OSError:
            pass
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with open(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

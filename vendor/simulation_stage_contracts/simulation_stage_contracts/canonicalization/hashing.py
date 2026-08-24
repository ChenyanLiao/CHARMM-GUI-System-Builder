from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from .json import canonical_json_bytes


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_data(value: Any, exclude_top_level: Iterable[str] = ()) -> str:
    return hashlib.sha256(canonical_json_bytes(value, exclude_top_level)).hexdigest()

from __future__ import annotations

from pathlib import Path

from ..canonicalization import sha256_file
from ..errors import StageContractError
from .paths import resolve_contained_file


def artifact_identity(root: Path, relative: str | Path, role: str = "artifact") -> dict:
    path = resolve_contained_file(root, relative)
    return {
        "role": role,
        "path": Path(relative).as_posix(),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def verify_artifact_identity(root: Path, identity: dict) -> bool:
    actual = artifact_identity(root, identity.get("path", ""), identity.get("role", "artifact"))
    if actual["size"] != identity.get("size") or actual["sha256"] != identity.get("sha256"):
        raise StageContractError("E_HASH_MISMATCH", "artifact identity does not match recorded evidence")
    return True

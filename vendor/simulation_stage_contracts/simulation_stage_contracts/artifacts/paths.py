from __future__ import annotations

from pathlib import Path

from ..errors import StageContractError


def resolve_contained_file(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise StageContractError("E_SCHEMA_INVALID", "artifact path must be contained and relative")
    candidate = root / relative_path
    if candidate.is_symlink():
        raise StageContractError("E_SCHEMA_INVALID", "artifact symlinks are not accepted")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise StageContractError("E_SCHEMA_INVALID", "artifact does not exist") from exc
    if resolved != root and root not in resolved.parents:
        raise StageContractError("E_SCHEMA_INVALID", "artifact escapes record root")
    if not resolved.is_file():
        raise StageContractError("E_SCHEMA_INVALID", "artifact must be a regular file")
    return resolved

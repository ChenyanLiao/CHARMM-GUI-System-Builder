"""Read and write JSON or optional YAML without hiding dependencies."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def load_structured(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ValueError(
                f"{path} is not JSON; install PyYAML to read general YAML"
            ) from json_error
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            raise ValueError(f"invalid structured file {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_json_atomic(path: Path, value: Any) -> None:
    """Replace a JSON file only after its complete content reaches disk."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise

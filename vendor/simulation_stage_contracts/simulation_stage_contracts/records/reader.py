from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ..errors import StageContractError


def read_record(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise StageContractError("E_SCHEMA_INVALID", f"record cannot be parsed: {path.name}") from exc
    if not isinstance(value, dict):
        raise StageContractError("E_SCHEMA_INVALID", "record must contain a mapping")
    return value

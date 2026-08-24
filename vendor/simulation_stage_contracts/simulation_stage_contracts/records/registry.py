from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..errors import StageContractError


@dataclass(frozen=True)
class RecordValidation:
    record_type: str
    schema_version: str
    legacy: bool
    warnings: tuple[str, ...] = ()


class SchemaRegistry:
    def __init__(self, schema_root: Path | None = None) -> None:
        self.schema_root = schema_root or Path(__file__).resolve().parents[2] / "schemas"

    def schema_path(self, record_type: str, version: str) -> Path:
        path = self.schema_root / record_type / f"{version}.json"
        if not path.is_file():
            raise StageContractError(
                "E_SCHEMA_UNSUPPORTED",
                f"unsupported schema {record_type} {version}",
            )
        return path

    def load_schema(self, record_type: str, version: str) -> dict[str, Any]:
        try:
            value = json.loads(self.schema_path(record_type, version).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StageContractError("E_SCHEMA_INVALID", "registered schema cannot be read") from exc
        return value

    def versions(self, record_type: str) -> tuple[str, ...]:
        root = self.schema_root / record_type
        if not root.is_dir():
            return ()
        return tuple(sorted(path.stem for path in root.glob("*.json")))

    def validate(
        self,
        record: dict[str, Any],
        expected_type: str | None = None,
    ) -> RecordValidation:
        record_type = str(record.get("record_type") or expected_type or "")
        version = str(record.get("schema_version") or "")
        if not record_type or not version:
            raise StageContractError("E_SCHEMA_INVALID", "record type and schema version are required")
        if expected_type and record_type != expected_type:
            raise StageContractError("E_SCHEMA_INVALID", "record type does not match expected type")
        schema = self.load_schema(record_type, version)
        errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda item: list(item.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise StageContractError(
                "E_SCHEMA_INVALID",
                f"schema validation failed at {location}: {first.message}",
            )
        legacy = (record_type, version) in {
            ("system-build-handoff", "1.0"),
            ("approved-build-contract", "2.1"),
            ("system-build-receipt", "1.0"),
            ("md-scope-authorization", "1.0"),
        }
        warnings = ("legacy record is read-only",) if legacy else ()
        return RecordValidation(record_type, version, legacy, warnings)

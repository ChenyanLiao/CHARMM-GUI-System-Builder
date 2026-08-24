from __future__ import annotations

from copy import deepcopy


def read_handoff_v1(record: dict) -> dict:
    version = str(record.get("schema_version", ""))
    return {
        "record_type": "system-build-handoff",
        "source_schema_version": version,
        "target_schema_version": "1.1",
        "read_only": version == "1.0",
        "record": deepcopy(record),
        "warnings": ["schema 1.0 handoff is read-only"] if version == "1.0" else [],
    }

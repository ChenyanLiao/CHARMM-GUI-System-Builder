from __future__ import annotations

from copy import deepcopy


def read_md_authorization_v1(record: dict) -> dict:
    return {
        "record_type": "md-scope-authorization",
        "source_schema_version": str(record.get("schema_version", "")),
        "read_only": True,
        "record": deepcopy(record),
        "warnings": ["schema 1.0 authorization cannot bind a Receipt 2.0 chain"],
    }

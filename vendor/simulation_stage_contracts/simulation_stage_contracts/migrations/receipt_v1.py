from __future__ import annotations

from copy import deepcopy


def read_receipt_v1(record: dict) -> dict:
    return {
        "record_type": "system-build-receipt",
        "source_schema_version": str(record.get("schema_version", "")),
        "status": "LEGACY_RECEIPT_REVALIDATION_REQUIRED",
        "read_only": True,
        "record": deepcopy(record),
    }

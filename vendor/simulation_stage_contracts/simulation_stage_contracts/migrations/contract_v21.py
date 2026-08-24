from __future__ import annotations

from copy import deepcopy


def migrate_contract_v21(record: dict, pipeline_id: str, branch_id: str, revision: int) -> dict:
    migrated = deepcopy(record)
    migrated.update(
        {
            "record_type": "approved-build-contract",
            "schema_version": "2.2",
            "pipeline_id": pipeline_id,
            "branch_id": branch_id,
            "revision": revision,
        }
    )
    return {
        "source_schema_version": str(record.get("schema_version", "")),
        "target_schema_version": "2.2",
        "original_unchanged": True,
        "record": migrated,
        "warnings": ["migrated contract must be reviewed and explicitly locked"],
    }

"""Immutable build-contract helpers."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from typing import Any

from .canonical import sha256_value
from .schema import (
    SCHEMA_VERSION,
    SchemaError,
    assert_no_secret_fields,
    require_fields,
    require_mapping,
    require_schema_version,
)


HASH_FIELD = "contract_sha256"
DECISION_FIELDS = {
    "parameter_id",
    "recommended_value",
    "evidence_sources",
    "risk_level",
    "contract_value",
    "approval_status",
}
VALID_APPROVAL_STATUSES = {
    "auto_recorded",
    "confirmed",
    "pending",
    "temporary_assumption",
}


def _hash_payload(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(contract))
    payload.pop(HASH_FIELD, None)
    return payload


def validate_contract(contract: Mapping[str, Any], *, require_locked: bool = False) -> None:
    require_mapping(contract, "build contract")
    require_schema_version(contract)
    require_fields(
        contract,
        (
            "run_id",
            "target_id",
            "builder",
            "mode",
            "inputs",
            "parameters",
            "decision_records",
        ),
        "build contract",
    )
    assert_no_secret_fields(contract)
    inputs = contract.get("inputs")
    if not isinstance(inputs, list):
        raise SchemaError("build contract inputs must be a list")
    for index, item in enumerate(inputs):
        if not isinstance(item, Mapping):
            raise SchemaError(f"build contract input[{index}] must be a mapping")
        require_fields(item, ("role", "path", "size_bytes", "sha256"), f"input[{index}]")
        if not str(item["role"]).strip() or not str(item["path"]).strip():
            raise SchemaError(f"build contract input[{index}] role/path cannot be empty")
        size = item["size_bytes"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise SchemaError(f"build contract input[{index}] size_bytes is invalid")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", str(item["sha256"])):
            raise SchemaError(f"build contract input[{index}] sha256 is invalid")

    parameters = contract.get("parameters")
    records = contract.get("decision_records")
    if not isinstance(parameters, Mapping):
        raise SchemaError("build contract parameters must be a mapping")
    if not isinstance(records, list):
        raise SchemaError("build contract decision_records must be a list")
    indexed: dict[str, Mapping[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise SchemaError(f"decision_records[{index}] must be a mapping")
        missing = sorted(DECISION_FIELDS - set(record))
        if missing:
            raise SchemaError(
                f"decision_records[{index}] missing fields: {', '.join(missing)}"
            )
        parameter_id = str(record["parameter_id"])
        if not parameter_id or parameter_id in indexed:
            raise SchemaError(f"duplicate or empty decision parameter: {parameter_id!r}")
        if not isinstance(record["evidence_sources"], list):
            raise SchemaError(f"decision {parameter_id} evidence_sources must be a list")
        if record["approval_status"] not in VALID_APPROVAL_STATUSES:
            raise SchemaError(f"decision {parameter_id} approval_status is invalid")
        indexed[parameter_id] = record
    for parameter_id, value in parameters.items():
        record = indexed.get(str(parameter_id))
        if record is None:
            raise SchemaError(f"parameter {parameter_id} has no decision record")
        if record.get("contract_value") != value:
            raise SchemaError(f"parameter {parameter_id} differs from its decision record")
    if contract.get("production_ready") is not False:
        raise SchemaError("production_ready must remain false")
    if contract.get("no_mdrun") is not True:
        raise SchemaError("no_mdrun must remain true")
    if require_locked:
        if contract.get("contract_state") != "locked":
            raise SchemaError("build contract must be locked")
        if not verify_contract_hash(contract):
            raise SchemaError("build contract hash is missing or invalid")


def lock_contract(draft: Mapping[str, Any]) -> dict[str, Any]:
    contract = copy.deepcopy(dict(draft))
    contract["schema_version"] = SCHEMA_VERSION
    contract["contract_state"] = "locked"
    contract.setdefault("revision", 1)
    contract["production_ready"] = False
    contract["no_mdrun"] = True
    contract.pop(HASH_FIELD, None)
    validate_contract(contract)
    contract[HASH_FIELD] = sha256_value(_hash_payload(contract))
    return contract


def verify_contract_hash(contract: Mapping[str, Any]) -> bool:
    expected = contract.get(HASH_FIELD)
    return isinstance(expected, str) and expected == sha256_value(
        _hash_payload(contract)
    )


def diff_contracts(old: Any, new: Any, path: str = "$") -> list[dict[str, Any]]:
    if isinstance(old, Mapping) and isinstance(new, Mapping):
        rows: list[dict[str, Any]] = []
        for key in sorted(set(old) | set(new)):
            if key == HASH_FIELD:
                continue
            child = f"{path}.{key}"
            if key not in old:
                rows.append({"path": child, "old": None, "new": new[key]})
            elif key not in new:
                rows.append({"path": child, "old": old[key], "new": None})
            else:
                rows.extend(diff_contracts(old[key], new[key], child))
        return rows
    if isinstance(old, list) and isinstance(new, list):
        rows = []
        for index in range(max(len(old), len(new))):
            child = f"{path}[{index}]"
            if index >= len(old):
                rows.append({"path": child, "old": None, "new": new[index]})
            elif index >= len(new):
                rows.append({"path": child, "old": old[index], "new": None})
            else:
                rows.extend(diff_contracts(old[index], new[index], child))
        return rows
    return [] if old == new else [{"path": path, "old": old, "new": new}]


def create_revision(
    locked_contract: Mapping[str, Any], revised_draft: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_contract(locked_contract, require_locked=True)
    revised = copy.deepcopy(dict(revised_draft))
    revised["revision"] = int(locked_contract.get("revision", 1)) + 1
    revised["supersedes_contract_sha256"] = locked_contract[HASH_FIELD]
    new_contract = lock_contract(revised)
    return new_contract, diff_contracts(locked_contract, new_contract)

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import yaml

from ..canonicalization import sha256_data
from ..errors import StageContractError
from ..records import SchemaRegistry
from ..records.validation import require_branch_identity
from .audit import audit_receipt_payload
from .chain import append_chain_event, current_event, read_chain, verify_chain
from .concurrency import BranchFileLock


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            yaml.safe_dump(value, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def lock_receipt(
    output_path: Path,
    chain_path: Path,
    payload: dict,
    supersession_reason: str | None = None,
    registry: SchemaRegistry | None = None,
) -> dict:
    audit = audit_receipt_payload(payload)
    if not audit["passed"]:
        raise StageContractError("E_SCHEMA_INVALID", "receipt audit is blocked", {"blockers": audit["blockers"]})
    pipeline_id, branch_id, _ = require_branch_identity(payload)
    if output_path.exists():
        raise StageContractError("E_SCHEMA_INVALID", "receipt output is immutable and already exists")

    lock_path = chain_path.with_name(f".{pipeline_id}.{branch_id}.receipt.lock")
    with BranchFileLock(lock_path):
        events = read_chain(chain_path)
        verify_chain(events)
        previous = current_event(events, pipeline_id, branch_id)
        revision = int(previous["revision"]) + 1 if previous else 1
        previous_receipt = previous.get("receipt_sha256") if previous else None
        supersedes_id = previous.get("receipt_id") if previous else None
        chain_root = sha256_data({"pipeline_id": pipeline_id, "branch_id": branch_id})
        receipt = {
            "record_type": "system-build-receipt",
            "schema_version": "2.0",
            "receipt_id": str(payload.get("receipt_id") or uuid.uuid4()),
            "pipeline_id": pipeline_id,
            "branch_id": branch_id,
            "revision": revision,
            "status": "TECHNICAL_PASS_NOT_PRODUCTION_APPROVAL",
            "handoff": payload["handoff"],
            "contract": payload["contract"],
            "package": payload["package"],
            "evidence_root_sha256": payload["evidence_root_sha256"],
            "semantic_topology": payload["semantic_topology"],
            "segment_matrix": payload["segment_matrix"],
            "parameter_injection": payload.get("parameter_injection"),
            "scientific_context": payload.get("scientific_context"),
            "gromacs": payload["gromacs"],
            "preprocessing": payload["preprocessing"],
            "tpr_readback": payload["tpr_readback"],
            "validators": payload["validators"],
            "unresolved_assumptions": payload.get("unresolved_assumptions", []),
            "permissions": {"md_execution_allowed": False, "production_ready": False},
            "no_mdrun": True,
            "previous_receipt_sha256": previous_receipt,
            "supersedes_receipt_id": supersedes_id,
            "supersession_reason": supersession_reason,
            "chain_root_sha256": chain_root,
        }
        receipt["receipt_sha256"] = sha256_data(receipt)
        (registry or SchemaRegistry()).validate(receipt, "system-build-receipt")
        _atomic_write(output_path, receipt)
        try:
            append_chain_event(
                chain_path,
                {
                    "receipt_id": receipt["receipt_id"],
                    "receipt_sha256": receipt["receipt_sha256"],
                    "pipeline_id": pipeline_id,
                    "branch_id": branch_id,
                    "revision": revision,
                    "previous_receipt_sha256": previous_receipt,
                    "supersedes_receipt_id": supersedes_id,
                    "receipt_path": output_path.name,
                },
            )
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
    return receipt

from __future__ import annotations

from pathlib import Path

from ..canonicalization import sha256_data
from ..errors import StageContractError
from ..evidence import verify_evidence_index
from ..records import SchemaRegistry, read_record
from .chain import current_event, read_chain, verify_chain


def verify_receipt(
    receipt_path: Path,
    chain_path: Path,
    evidence_index: dict | None = None,
    registry: SchemaRegistry | None = None,
) -> dict:
    receipt = read_record(receipt_path)
    validation = (registry or SchemaRegistry()).validate(receipt, "system-build-receipt")
    if validation.schema_version == "1.0":
        raise StageContractError("E_RECEIPT_LEGACY", "Receipt 1.0 requires Stage 2 revalidation")
    actual = sha256_data(receipt, exclude_top_level=("receipt_sha256",))
    if receipt.get("receipt_sha256") != actual:
        raise StageContractError("E_HASH_MISMATCH", "receipt content hash mismatch")

    events = read_chain(chain_path)
    verify_chain(events)
    current = current_event(events, receipt["pipeline_id"], receipt["branch_id"])
    matching = next((event for event in events if event.get("receipt_sha256") == actual), None)
    if matching is None:
        raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt is not registered in its chain")
    if current is None or current.get("receipt_sha256") != actual:
        raise StageContractError("E_RECEIPT_SUPERSEDED", "receipt has been superseded")
    if receipt.get("chain_root_sha256") != sha256_data(
        {"pipeline_id": receipt["pipeline_id"], "branch_id": receipt["branch_id"]}
    ):
        raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt chain root mismatch")
    if evidence_index is not None:
        verify_evidence_index(evidence_index)
        if evidence_index.get("root_sha256") != receipt.get("evidence_root_sha256"):
            raise StageContractError("E_HASH_MISMATCH", "receipt evidence root mismatch")
    return {
        "receipt_valid": True,
        "receipt_state": "VALID_CURRENT",
        "receipt_sha256": actual,
        "md_execution_allowed": False,
        "production_ready": False,
        "no_mdrun": True,
    }

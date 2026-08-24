"""Build a Stage 2 receipt candidate from locked, hash-bound evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import sha256_file
from .contracts import validate_contract
from .shared import activate_vendor


def _bound_record(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path.name,
        "sha256": sha256_file(path),
        "schema_version": str(record.get("schema_version", "")),
    }


def build_closure_payload(
    *,
    contract_path: Path,
    contract: dict[str, Any],
    handoff_path: Path,
    handoff: dict[str, Any],
    package_report: dict[str, Any],
    evidence_index: dict[str, Any],
    semantic_topology: dict[str, Any],
    segment_matrix: dict[str, Any],
    preprocessing: dict[str, Any],
    tpr_readback: dict[str, Any],
    parameter_injection: dict[str, Any] | None = None,
    scientific_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    activate_vendor()
    from simulation_stage_contracts.evidence import verify_evidence_index

    validate_contract(contract, require_locked=True)
    verify_evidence_index(evidence_index)
    parameters = contract.get("parameters", {})
    custom_required = bool(parameters.get("ligand.custom_parameter_submission"))
    context_required = any(
        bool(contract.get(section, {}).get("required"))
        for section in ("structural_environment", "pose_preservation", "restraint_handoff")
    )
    package = {
        "path": str(package_report.get("package") or package_report.get("artifact") or ""),
        "sha256": str(package_report.get("sha256") or ""),
        "size": int(package_report.get("package_size_bytes") or package_report.get("size_bytes") or 0),
    }
    package_pass = bool(
        package_report.get("technical_pass")
        or package_report.get("validation_passed")
        or package_report.get("technical_status") == "Technical_Pass_Not_Production_Approval"
    )
    closure_pass = bool(
        package_pass
        and semantic_topology.get("status") == "PASS"
        and segment_matrix.get("status") == "PASS"
        and preprocessing.get("strict_preprocessing_passed") is True
        and preprocessing.get("maxwarn_used") is False
        and tpr_readback.get("passed") is True
        and (not custom_required or (parameter_injection or {}).get("status") == "PASS")
        and (not context_required or (scientific_context or {}).get("passed") is True)
    )
    return {
        "pipeline_id": contract["pipeline_id"],
        "branch_id": contract["branch_id"],
        "revision": contract["revision"],
        "closure_state": "TECHNICAL_PASS" if closure_pass else "BLOCKED",
        "evidence_freshness": "FRESH",
        "handoff": _bound_record(handoff_path, handoff),
        "contract": _bound_record(contract_path, contract),
        "package": package,
        "evidence_root_sha256": evidence_index["root_sha256"],
        "semantic_topology": semantic_topology,
        "segment_matrix": segment_matrix,
        "custom_parameter_required": custom_required,
        "parameter_injection": parameter_injection,
        "scientific_context_required": context_required,
        "scientific_context": scientific_context,
        "gromacs": preprocessing.get("gromacs", {}),
        "preprocessing": preprocessing,
        "tpr_readback": tpr_readback,
        "validators": {
            "stage2": "2.2.0",
            "shared_core": "1.0.0",
            **package_report.get("validators", {}),
        },
        "unresolved_assumptions": contract.get("temporary_assumptions", []),
        "production_ready": False,
        "md_execution_allowed": False,
        "no_mdrun": True,
    }


def verify_closure_record(
    *,
    closure_path: Path,
    closure: dict[str, Any],
    contract_path: Path,
    contract: dict[str, Any],
    handoff_path: Path,
    handoff: dict[str, Any],
    evidence_index: dict[str, Any],
    package_path: Path | None = None,
) -> dict[str, Any]:
    """Replay the read-only Stage 2 closure gate against bound artifacts."""
    activate_vendor()
    from simulation_stage_contracts.evidence import verify_evidence_index
    from simulation_stage_contracts.receipts import audit_receipt_payload
    from simulation_stage_contracts.records import SchemaRegistry

    validate_contract(contract, require_locked=True)
    SchemaRegistry().validate(handoff, "system-build-handoff")
    verify_evidence_index(evidence_index)
    if closure.get("record_type") != "system-build-closure-draft":
        raise ValueError("closure record_type is invalid")
    if str(closure.get("schema_version")) != "1.0":
        raise ValueError("closure schema_version is unsupported")
    payload = closure.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("closure payload must be a mapping")

    identity = {
        "pipeline_id": contract["pipeline_id"],
        "branch_id": contract["branch_id"],
        "revision": contract["revision"],
    }
    for field, expected in identity.items():
        if payload.get(field) != expected:
            raise ValueError(f"closure {field} does not match the locked contract")
    for field in ("pipeline_id", "branch_id"):
        recorded = handoff.get(field)
        if recorded is not None and recorded != identity[field]:
            raise ValueError(f"handoff {field} does not match the locked contract")

    for role, path, record in (
        ("contract", contract_path, contract),
        ("handoff", handoff_path, handoff),
    ):
        reference = payload.get(role)
        if not isinstance(reference, dict):
            raise ValueError(f"closure {role} binding is missing")
        if reference.get("sha256") != sha256_file(path):
            raise ValueError(f"closure {role} SHA-256 binding does not match")
        if str(reference.get("schema_version")) != str(record.get("schema_version")):
            raise ValueError(f"closure {role} schema binding does not match")

    if payload.get("evidence_root_sha256") != evidence_index.get("root_sha256"):
        raise ValueError("closure evidence root does not match the evidence index")

    package = payload.get("package")
    if not isinstance(package, dict):
        raise ValueError("closure package binding is missing")
    selected_package = package_path
    if selected_package is None:
        recorded_path = Path(str(package.get("path", "")))
        selected_package = (
            recorded_path if recorded_path.is_absolute() else closure_path.parent / recorded_path
        )
    selected_package = selected_package.expanduser()
    if selected_package.is_symlink():
        raise ValueError("closure package must be a regular non-symlink file")
    selected_package = selected_package.resolve(strict=True)
    if not selected_package.is_file():
        raise ValueError("closure package must be a regular non-symlink file")
    if sha256_file(selected_package) != package.get("sha256"):
        raise ValueError("closure package SHA-256 binding does not match")
    if selected_package.stat().st_size != package.get("size"):
        raise ValueError("closure package size binding does not match")

    audit = audit_receipt_payload(payload)
    if not audit["passed"]:
        raise ValueError("closure payload does not pass the current Stage 2 audit")
    if closure.get("audit") != audit:
        raise ValueError("stored closure audit does not match replayed audit")
    return {
        "success": True,
        "pipeline_id": identity["pipeline_id"],
        "branch_id": identity["branch_id"],
        "revision": identity["revision"],
        "artifact_state": "VALID_FINAL",
        "closure_state": "TECHNICAL_PASS",
        "evidence_freshness": "FRESH",
        "package": {
            "path": str(selected_package),
            "size": selected_package.stat().st_size,
            "sha256": package["sha256"],
        },
        "errors": [],
        "side_effects_performed": False,
        "production_ready": False,
        "no_mdrun": True,
    }

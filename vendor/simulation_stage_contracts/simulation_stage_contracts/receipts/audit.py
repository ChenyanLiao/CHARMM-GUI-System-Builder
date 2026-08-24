from __future__ import annotations

from typing import Any


def audit_receipt_payload(payload: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []

    def block(code: str, message: str) -> None:
        blockers.append({"code": code, "message": message})

    if payload.get("closure_state") != "TECHNICAL_PASS":
        block("E_SCHEMA_INVALID", "Stage 2 closure has not technically passed")
    if payload.get("evidence_freshness") != "FRESH":
        block("E_EVIDENCE_STALE", "required evidence is not fresh")
    if payload.get("semantic_topology", {}).get("status") != "PASS":
        block("E_SCHEMA_INVALID", "semantic topology validation did not pass")
    if payload.get("segment_matrix", {}).get("status") != "PASS":
        block("E_SEGMENT_MISMATCH", "segment reconciliation did not pass")
    preprocessing = payload.get("preprocessing", {})
    if preprocessing.get("strict_preprocessing_passed") is not True:
        block("E_GROMPP_FAILED", "strict preprocessing did not pass")
    if preprocessing.get("maxwarn_used") is not False:
        block("E_GROMPP_FAILED", "-maxwarn cannot be used for technical closure")
    if payload.get("tpr_readback", {}).get("passed") is not True:
        block("E_TPR_READBACK_FAILED", "TPR readback did not pass")
    if payload.get("custom_parameter_required") is True:
        injection = payload.get("parameter_injection") or {}
        if injection.get("status") != "PASS":
            block("E_PARAMETER_INJECTION_UNVERIFIED", "required parameter injection is unverified")
    if payload.get("scientific_context_required") is True:
        context = payload.get("scientific_context") or {}
        if context.get("passed") is not True:
            block("E_STRUCTURAL_COMPONENT_UNRESOLVED", "required scientific context evidence is blocked")
        environment = context.get("structural_environment") or {}
        status = environment.get("status")
        if status == "UNRESOLVED_BLOCKING":
            block("E_STRUCTURAL_COMPONENT_UNRESOLVED", "structural environment is unresolved")
        if status == "ALTERED_APPROVED_CANDIDATE" and (
            environment.get("environmental_equivalence") is not False
            or environment.get("downstream_sensitivity_required") is not True
        ):
            block("E_ENVIRONMENT_LEDGER_MISMATCH", "altered environment status is internally inconsistent")
        if context.get("pose_preservation", {}).get("required") is True and context.get(
            "pose_preservation", {}
        ).get("status") != "PASS":
            block("E_POSE_PRESERVATION_FAILED", "required pose-preservation evidence did not pass")
        if context.get("restraint_handoff", {}).get("required") is True and context.get(
            "restraint_handoff", {}
        ).get("status") != "PASS":
            block("E_RESTRAINT_HANDOFF_UNRESOLVED", "required restraint handoff did not pass")
    package = payload.get("package", {})
    if len(str(package.get("sha256", ""))) != 64 or not isinstance(package.get("size"), int):
        block("E_SCHEMA_INVALID", "package identity is incomplete")
    if not payload.get("gromacs", {}).get("version"):
        block("E_ENGINE_UNSUPPORTED", "GROMACS identity and version are required")
    if not payload.get("validators"):
        block("E_SCHEMA_INVALID", "validator versions are required")

    return {
        "passed": not blockers,
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "production_ready": False,
        "md_execution_allowed": False,
        "no_mdrun": True,
    }

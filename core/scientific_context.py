"""Validate Stage 2 structural environment, pose, and restraint evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .schema import SchemaError, assert_no_secret_fields


COMPONENT_ROLES = {
    "bulk_membrane_component",
    "structure_resolved_lipid",
    "structural_ion_or_cofactor",
    "unrelated_or_obsolete_component",
    "unknown_requires_review",
}
DISPOSITIONS = {"retain", "replace", "remove", "unresolved"}
DIRECT_CONTEXT_FIELDS = {
    "contacts_ligand",
    "coordinates_protein_or_ion",
    "interpreted_hydrogen_bond",
    "interpreted_salt_bridge",
    "fills_modeled_pocket",
    "part_of_claimed_microenvironment",
}
CANDIDATE_MODES = {"test_only", "Candidate_Not_For_MD"}
STRUCTURAL_ROLES = {"structure_resolved_lipid", "structural_ion_or_cofactor"}
POSE_METRICS = {
    "mapping_coverage": ("minimum_mapping_coverage", ">="),
    "internal_rmsd_angstrom": ("maximum_internal_rmsd_angstrom", "<="),
    "pose_rmsd_angstrom": ("maximum_pose_rmsd_angstrom", "<="),
    "com_shift_angstrom": ("maximum_com_shift_angstrom", "<="),
}


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaError(f"{label} must be a mapping")
    return value


def _required_flag(contract: Mapping[str, Any], key: str) -> bool:
    section = _mapping(contract.get(key, {}), f"contract {key}")
    required = section.get("required", False)
    if not isinstance(required, bool):
        raise SchemaError(f"contract {key}.required must be boolean")
    return required


def assess_structural_environment(
    contract: Mapping[str, Any], ledger: Mapping[str, Any] | None
) -> dict[str, Any]:
    required = _required_flag(contract, "structural_environment")
    if ledger is None:
        return _missing_assessment(required, "E_STRUCTURAL_COMPONENT_UNRESOLVED")
    _mapping(ledger, "structural environment ledger")
    assert_no_secret_fields(ledger)
    components = ledger.get("components")
    if not isinstance(components, list):
        raise SchemaError("structural environment components must be a list")

    blockers: list[dict[str, str]] = []
    altered: list[str] = []
    rows: list[dict[str, Any]] = []
    mode = str(contract.get("mode", "dry_run"))
    for index, raw in enumerate(components):
        item = _mapping(raw, f"structural component[{index}]")
        component_id = str(item.get("component_id", "")).strip()
        role = str(item.get("classification", "")).strip()
        disposition = str(item.get("disposition", "")).strip()
        if not component_id:
            raise SchemaError(f"structural component[{index}] component_id is required")
        if role not in COMPONENT_ROLES:
            raise SchemaError(f"structural component {component_id} classification is invalid")
        if disposition not in DISPOSITIONS:
            raise SchemaError(f"structural component {component_id} disposition is invalid")
        context = _mapping(item.get("direct_context", {}), f"{component_id} direct_context")
        critical = any(context.get(field) is True for field in DIRECT_CONTEXT_FIELDS)
        unresolved = role == "unknown_requires_review" or disposition == "unresolved"
        if unresolved and (required or critical):
            blockers.append(
                {
                    "code": "E_STRUCTURAL_COMPONENT_UNRESOLVED",
                    "component_id": component_id,
                    "message": "structural component role or disposition is unresolved",
                }
            )
        environment_altering = disposition in {"remove", "replace"} and (
            critical or role in STRUCTURAL_ROLES
        )
        if environment_altering:
            rationale = str(item.get("rationale", "")).strip()
            approval = str(item.get("approval_scope", "")).strip()
            sensitivity = str(item.get("downstream_sensitivity_branch", "")).strip()
            if mode not in CANDIDATE_MODES or not rationale or not approval or not sensitivity:
                blockers.append(
                    {
                        "code": "E_STRUCTURAL_COMPONENT_UNRESOLVED",
                        "component_id": component_id,
                        "message": "structural removal or replacement lacks candidate approval evidence",
                    }
                )
            else:
                altered.append(component_id)
        rows.append(
            {
                "component_id": component_id,
                "classification": role,
                "disposition": disposition,
                "critical_context": critical,
            }
        )

    if blockers:
        status = "UNRESOLVED_BLOCKING"
        equivalence = None
        sensitivity_required = True
    elif altered:
        status = "ALTERED_APPROVED_CANDIDATE"
        equivalence = False
        sensitivity_required = True
    elif components:
        status = "PRESERVED"
        equivalence = True
        sensitivity_required = False
    else:
        status = "NOT_APPLICABLE"
        equivalence = None
        sensitivity_required = False
    return {
        "required": required,
        "status": status,
        "passed": not blockers,
        "environmental_equivalence": equivalence,
        "downstream_sensitivity_required": sensitivity_required,
        "altered_components": altered,
        "components": rows,
        "blockers": blockers,
    }


def _missing_assessment(required: bool, code: str) -> dict[str, Any]:
    blockers = []
    if required:
        blockers.append({"code": code, "message": "required evidence was not supplied"})
    return {
        "required": required,
        "status": "MISSING" if required else "NOT_APPLICABLE",
        "passed": not required,
        "blockers": blockers,
    }


def assess_pose_preservation(
    contract: Mapping[str, Any], report: Mapping[str, Any] | None
) -> dict[str, Any]:
    required = _required_flag(contract, "pose_preservation")
    if report is None:
        return _missing_assessment(required, "E_POSE_PRESERVATION_FAILED")
    _mapping(report, "pose preservation report")
    assert_no_secret_fields(report)
    transitions = report.get("transitions")
    if not isinstance(transitions, list) or (required and not transitions):
        raise SchemaError("pose preservation transitions must be a non-empty list")
    blockers: list[dict[str, str]] = []
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(transitions):
        item = _mapping(raw, f"pose transition[{index}]")
        transition_id = str(item.get("transition_id", "")).strip()
        if not transition_id:
            raise SchemaError(f"pose transition[{index}] transition_id is required")
        if required and str(item.get("alignment_scope", "")) not in {"protein", "pocket"}:
            raise SchemaError(f"pose transition {transition_id} alignment_scope is invalid")
        if required and not isinstance(item.get("rigid_transform_applied"), bool):
            raise SchemaError(
                f"pose transition {transition_id} rigid_transform_applied must be boolean"
            )
        metric_fields = set(POSE_METRICS) | {
            limit_field for limit_field, _ in POSE_METRICS.values()
        }
        missing = sorted(field for field in metric_fields if field not in item)
        if missing:
            raise SchemaError(
                f"pose transition {transition_id} missing metrics: {', '.join(missing)}"
            )
        metrics = {
            name: (float(item[name]), float(item[limit_field]), operator)
            for name, (limit_field, operator) in POSE_METRICS.items()
        }
        if not 0.0 <= metrics["mapping_coverage"][0] <= 1.0:
            raise SchemaError(f"pose transition {transition_id} mapping_coverage is invalid")
        if any(value < 0 or limit < 0 for value, limit, _ in metrics.values()):
            raise SchemaError(f"pose transition {transition_id} metrics must be non-negative")
        failed = [
            name
            for name, (value, limit, operator) in metrics.items()
            if (operator == ">=" and value < limit) or (operator == "<=" and value > limit)
        ]
        if failed:
            blockers.append(
                {
                    "code": "E_POSE_PRESERVATION_FAILED",
                    "transition_id": transition_id,
                    "message": f"pose transition failed: {', '.join(failed)}",
                }
            )
        rows.append(
            {
                "transition_id": transition_id,
                "alignment_scope": item.get("alignment_scope"),
                "rigid_transform_applied": item.get("rigid_transform_applied"),
                "failed_metrics": failed,
            }
        )
    return {
        "required": required,
        "status": "PASS" if not blockers else "FAIL",
        "passed": not blockers,
        "transitions": rows,
        "blockers": blockers,
        "proves_conversion_fidelity_only": True,
    }


def assess_restraint_handoff(
    contract: Mapping[str, Any], report: Mapping[str, Any] | None
) -> dict[str, Any]:
    required = _required_flag(contract, "restraint_handoff")
    if report is None:
        return _missing_assessment(required, "E_RESTRAINT_HANDOFF_UNRESOLVED")
    _mapping(report, "restraint handoff report")
    assert_no_secret_fields(report)
    referenced = {str(value) for value in report.get("referenced_macros", [])}
    defined = {str(value) for value in report.get("defined_macros", [])}
    unresolved = sorted(referenced - defined)
    blockers: list[dict[str, str]] = []
    if unresolved:
        blockers.append(
            {
                "code": "E_RESTRAINT_HANDOFF_UNRESOLVED",
                "message": f"undefined restraint macros: {', '.join(unresolved)}",
            }
        )
    for field in ("restraint_files", "equilibration_schedule", "ligand_heavy_atom_restraints"):
        value = report.get(field)
        if required and (not isinstance(value, list) or not value):
            blockers.append(
                {
                    "code": "E_RESTRAINT_HANDOFF_UNRESOLVED",
                    "message": f"{field} is missing or empty",
                }
            )
    if required and "expected_production_define" not in report:
        blockers.append(
            {
                "code": "E_RESTRAINT_HANDOFF_UNRESOLVED",
                "message": "expected_production_define is missing",
            }
        )
    ligand_restraints = report.get("ligand_heavy_atom_restraints", [])
    restraint_release = any(
        isinstance(item, Mapping) and item.get("enabled") is True
        for item in ligand_restraints
    ) and not str(report.get("expected_production_define", "")).strip()
    if restraint_release and report.get("downstream_release_validation_required") is not True:
        blockers.append(
            {
                "code": "E_RESTRAINT_HANDOFF_UNRESOLVED",
                "message": "ligand restraint release requires downstream validation",
            }
        )
    return {
        "required": required,
        "status": "PASS" if not blockers else "FAIL",
        "passed": not blockers,
        "undefined_macros": unresolved,
        "downstream_release_validation_required": bool(
            report.get("downstream_release_validation_required", False)
        ),
        "blockers": blockers,
        "stage2_mdrun_performed": False,
    }


def build_scientific_context_report(
    *,
    contract: Mapping[str, Any],
    structural_environment: Mapping[str, Any] | None = None,
    pose_preservation: Mapping[str, Any] | None = None,
    restraint_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = {
        "record_type": "stage2-scientific-context",
        "schema_version": "1.0",
        "structural_environment": assess_structural_environment(contract, structural_environment),
        "pose_preservation": assess_pose_preservation(contract, pose_preservation),
        "restraint_handoff": assess_restraint_handoff(contract, restraint_handoff),
        "production_ready": False,
        "md_execution_allowed": False,
        "no_mdrun": True,
    }
    report["passed"] = all(
        report[key]["passed"]
        for key in ("structural_environment", "pose_preservation", "restraint_handoff")
    )
    return report

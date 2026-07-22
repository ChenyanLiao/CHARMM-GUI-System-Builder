"""Expand a system request into a risk-ranked parameter inventory."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .decisions import (
    Evidence,
    ParameterDecision,
    RiskLevel,
    build_decision,
    guided_question,
)
from .io import load_structured
from .schema import SCHEMA_VERSION, SchemaError, assert_no_secret_fields


MODULE_RULE_PATHS = {
    "pdb_reader": "rules/pdb_reader/v2.1.json",
    "ligand_reader": "rules/ligand_reader/v2.1.json",
    "membrane_builder": "rules/membrane_builder/v2.1.json",
    "solution_builder": "rules/solution_builder/v2.1.json",
    "quick_bilayer": "rules/quick_bilayer/v2.1.json",
    "gromacs": "rules/output_engines/gromacs-v2.1.json",
}


def get_path(value: Any, path: str, default: Any = None) -> Any:
    current = value
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return default
        current = current[part]
    return current


def condition_matches(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    if not condition:
        return True
    if "all" in condition:
        return all(condition_matches(item, context) for item in condition["all"])
    if "any" in condition:
        return any(condition_matches(item, context) for item in condition["any"])
    actual = get_path(context, condition["path"])
    if "equals" in condition:
        return actual == condition["equals"]
    if "in" in condition:
        return actual in condition["in"]
    if "truthy" in condition:
        return bool(actual) is bool(condition["truthy"])
    raise SchemaError(f"unsupported rule condition: {condition}")


def active_modules(run_request: dict[str, Any]) -> list[str]:
    builder = run_request.get("builder")
    membrane_only_quick_bilayer = (
        builder == "quick_bilayer"
        and get_path(run_request, "system.membrane_only", False)
    )
    modules = [] if membrane_only_quick_bilayer else ["pdb_reader"]
    if get_path(run_request, "system.has_ligand", False):
        modules.append("ligand_reader")
    if builder in {"membrane_builder", "solution_builder", "quick_bilayer"}:
        modules.append(str(builder))
    if "gromacs" in run_request.get("output_engines", ["gromacs"]):
        modules.append("gromacs")
    return modules


def load_rules(root: Path, modules: list[str]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for module in modules:
        path = root / MODULE_RULE_PATHS[module]
        data = load_structured(path)
        if str(data.get("schema_version", "")) != SCHEMA_VERSION:
            raise SchemaError(f"rule pack {path} does not use schema 2.1")
        rules.extend(data.get("parameters", []))
    return rules


def _evidence_for_rule(
    rule: dict[str, Any], context: dict[str, Any]
) -> list[Evidence]:
    evidence: list[Evidence] = []
    for source in rule.get("evidence", []):
        value = get_path(context, source.get("path", ""), None)
        if value is not None:
            evidence.append(
                Evidence(
                    source=source["source"],
                    value=value,
                    citation=source.get("citation", ""),
                    confidence=source.get("confidence", "unknown"),
                )
            )
    if "default" in rule:
        evidence.append(
            Evidence(
                source="versioned_rule",
                value=rule["default"],
                citation=rule.get("rule_reference", ""),
                confidence=rule.get("default_confidence", "medium"),
            )
        )
    return evidence


def _decision_from_rule(
    rule: dict[str, Any], context: dict[str, Any]
) -> ParameterDecision:
    default_risk = RiskLevel(rule.get("risk_level", "Contextual"))
    decision = build_decision(
        parameter_id=rule["parameter_id"],
        module=rule["module"],
        page_or_step=rule.get("page_or_step", ""),
        value_type=rule.get("value_type", "string"),
        options=rule.get("available_options", []),
        evidence=_evidence_for_rule(rule, context),
        reason=rule.get("recommendation_reason", ""),
        default_risk=default_risk,
    )
    if rule.get("temporary_assumption_allowed") is False:
        decision.temporary_assumption_allowed = False
    return decision


def _validated_answer(decision: ParameterDecision, value: Any) -> Any:
    if value is None:
        raise SchemaError(f"answer for {decision.parameter_id} cannot be null")
    if decision.available_options and value not in decision.available_options:
        raise SchemaError(
            f"answer for {decision.parameter_id} is outside available options"
        )
    if decision.value_type == "boolean" and not isinstance(value, bool):
        raise SchemaError(f"answer for {decision.parameter_id} must be boolean")
    if decision.value_type == "integer" and (
        not isinstance(value, int) or isinstance(value, bool)
    ):
        raise SchemaError(f"answer for {decision.parameter_id} must be integer")
    if decision.value_type == "number" and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        raise SchemaError(f"answer for {decision.parameter_id} must be numeric")
    if decision.value_type in {"string", "composition"} and (
        not isinstance(value, str) or not value.strip()
    ):
        raise SchemaError(f"answer for {decision.parameter_id} must be non-empty text")
    return value


def build_inventory(
    *,
    root: Path,
    run_request: dict[str, Any],
    target_profile: dict[str, Any] | None = None,
    input_audit: dict[str, Any] | None = None,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assert_no_secret_fields(run_request)
    target_profile = target_profile or {}
    input_audit = input_audit or {}
    answers = answers or {}
    context = {
        "run_request": run_request,
        "target_profile": target_profile,
        "input_audit": input_audit,
    }
    decisions: list[ParameterDecision] = []
    for rule in load_rules(root, active_modules(run_request)):
        if condition_matches(rule.get("applies_if", {}), context):
            decisions.append(_decision_from_rule(rule, context))

    penalty = get_path(input_audit, "ligand.cgenff.param_penalty")
    if isinstance(penalty, (int, float)) and penalty > 50:
        decisions.append(
            ParameterDecision(
                parameter_id="ligand.cgenff_penalty_approval",
                module="ligand_reader",
                page_or_step="preflight",
                value_type="boolean",
                available_options=[False, True],
                recommended_value=False,
                recommendation_reason=(
                    f"Automatic CGenFF param penalty {penalty} exceeds 50."
                ),
                evidence_sources=[
                    {
                        "source": "input_audit",
                        "value": penalty,
                        "citation": "lig.rtf",
                        "confidence": "high",
                    }
                ],
                confidence="high",
                risk_level="Critical",
                temporary_assumption_allowed=True,
            )
        )

    mode = str(run_request.get("mode", "dry_run"))
    allow_temporary = bool(run_request.get("allow_temporary_critical_assumptions"))
    pending: list[str] = []
    temporary: list[str] = []
    parameters: dict[str, Any] = {}
    for decision in decisions:
        answer_present = decision.parameter_id in answers
        if answer_present:
            value = _validated_answer(decision, answers[decision.parameter_id])
            decision.user_decision = value
            decision.contract_value = value
            decision.approval_status = "confirmed"
        elif decision.risk_level == "Routine":
            decision.contract_value = decision.recommended_value
            decision.approval_status = "auto_recorded"
        elif (
            decision.risk_level == "Critical"
            and decision.temporary_assumption_allowed
            and mode in {"test_only", "Candidate_Not_For_MD"}
            and allow_temporary
            and decision.recommended_value is not None
        ):
            decision.contract_value = decision.recommended_value
            decision.approval_status = "temporary_assumption"
            temporary.append(decision.parameter_id)
        else:
            pending.append(decision.parameter_id)
        if decision.contract_value is not None:
            parameters[decision.parameter_id] = decision.contract_value

    questions = [
        guided_question(decision)
        for decision in decisions
        if decision.parameter_id in pending
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_request.get("run_id", ""),
        "active_modules": active_modules(run_request),
        "decisions": [decision.to_dict() for decision in decisions],
        "contract_parameters": parameters,
        "pending_decisions": pending,
        "guided_questions": questions,
        "next_guided_question": questions[0] if questions else None,
        "temporary_assumptions": temporary,
        "ready_to_lock": not pending,
        "production_ready": False,
        "no_mdrun": True,
    }

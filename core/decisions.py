"""Risk-aware parameter recommendations and guided questions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    ROUTINE = "Routine"
    CONTEXTUAL = "Contextual"
    CRITICAL = "Critical"


EVIDENCE_PRIORITY = {
    "agent_inference": 10,
    "versioned_rule": 20,
    "reliable_literature": 25,
    "official_charmm_gui_documentation": 30,
    "input_audit": 40,
    "approved_target_profile": 50,
    "approved_expert": 55,
    "user_experimental_condition": 60,
}

STOP_ONLY_TOPICS = {
    "ligand.chemical_identity",
    "ligand.protonation",
    "ligand.bond_order",
    "ligand.stereochemistry",
    "protein.connectivity",
    "protein.segmentation",
    "membrane.orientation",
}
DRIFT_STATUSES = {
    "OK",
    "WRONG",
    "MISSING",
    "UNKNOWN",
    "RISK",
    "BLOCK_PRODUCTION",
}
_UNSET = object()


@dataclass(frozen=True)
class Evidence:
    source: str
    value: Any
    citation: str = ""
    confidence: str = "unknown"

    @property
    def priority(self) -> int:
        return EVIDENCE_PRIORITY.get(self.source, 0)


@dataclass
class ParameterDecision:
    parameter_id: str
    module: str
    page_or_step: str
    value_type: str
    available_options: list[Any] = field(default_factory=list)
    recommended_value: Any = None
    recommendation_reason: str = ""
    evidence_sources: list[dict[str, Any]] = field(default_factory=list)
    confidence: str = "unknown"
    risk_level: str = RiskLevel.CONTEXTUAL.value
    user_decision: Any = None
    contract_value: Any = None
    actual_submitted_value: Any = None
    drift_status: str = "UNKNOWN"
    material_conflict: bool = False
    temporary_assumption_allowed: bool = True
    approval_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def recommend_from_evidence(
    parameter_id: str,
    evidence: list[Evidence],
    *,
    default_risk: RiskLevel = RiskLevel.CONTEXTUAL,
) -> tuple[Any, RiskLevel, bool]:
    if not evidence:
        return None, RiskLevel.CRITICAL, False
    ranked = sorted(evidence, key=lambda item: item.priority, reverse=True)
    recommendation = ranked[0].value
    material_conflict = any(item.value != recommendation for item in ranked[1:])
    risk = RiskLevel.CRITICAL if material_conflict else default_risk
    if parameter_id in STOP_ONLY_TOPICS and recommendation is None:
        risk = RiskLevel.CRITICAL
    return recommendation, risk, material_conflict


def build_decision(
    *,
    parameter_id: str,
    module: str,
    page_or_step: str,
    value_type: str,
    options: list[Any],
    evidence: list[Evidence],
    reason: str,
    default_risk: RiskLevel = RiskLevel.CONTEXTUAL,
) -> ParameterDecision:
    recommendation, risk, conflict = recommend_from_evidence(
        parameter_id,
        evidence,
        default_risk=default_risk,
    )
    ranked = sorted(evidence, key=lambda item: item.priority, reverse=True)
    return ParameterDecision(
        parameter_id=parameter_id,
        module=module,
        page_or_step=page_or_step,
        value_type=value_type,
        available_options=options,
        recommended_value=recommendation,
        recommendation_reason=reason,
        evidence_sources=[asdict(item) for item in evidence],
        confidence=ranked[0].confidence if ranked else "unknown",
        risk_level=risk.value,
        material_conflict=conflict,
        temporary_assumption_allowed=parameter_id not in STOP_ONLY_TOPICS,
    )


def assess_drift(
    decision: ParameterDecision,
    *,
    actual_value: Any = _UNSET,
    hidden_value: Any = _UNSET,
    generated_value: Any = _UNSET,
) -> dict[str, Any]:
    """Compare approved, submitted, hidden, and generated values."""

    expected = decision.contract_value
    observations = {
        "actual_submitted_value": actual_value,
        "hidden_value": hidden_value,
        "generated_value": generated_value,
    }
    captured = {
        key: value for key, value in observations.items() if value is not _UNSET
    }
    mismatches = {
        key: value for key, value in captured.items() if value != expected
    }

    if expected is None:
        status = "UNKNOWN"
        reason = "No approved contract value is available."
    elif actual_value is _UNSET:
        status = "MISSING"
        reason = "The submitted or current control value was not captured."
    elif mismatches:
        critical = (
            decision.risk_level == RiskLevel.CRITICAL.value
            or decision.parameter_id in STOP_ONLY_TOPICS
        )
        status = "BLOCK_PRODUCTION" if critical else "WRONG"
        reason = "One or more observed values differ from the locked contract."
    elif decision.material_conflict:
        status = "RISK"
        reason = "The approved value matches, but a material evidence conflict remains."
    else:
        status = "OK"
        reason = "Captured values match the locked contract."

    if status not in DRIFT_STATUSES:  # pragma: no cover - defensive invariant
        raise ValueError(f"invalid drift status: {status}")
    decision.actual_submitted_value = (
        None if actual_value is _UNSET else actual_value
    )
    decision.drift_status = status
    return {
        "parameter_id": decision.parameter_id,
        "contract_value": expected,
        "observed": captured,
        "mismatches": mismatches,
        "status": status,
        "reason": reason,
        "production_ready": False,
        "no_mdrun": True,
    }


def guided_question(decision: ParameterDecision) -> dict[str, Any]:
    requires_confirmation = decision.risk_level != RiskLevel.ROUTINE.value
    must_stop_without_answer = (
        decision.risk_level == RiskLevel.CRITICAL.value
        and not decision.temporary_assumption_allowed
    )
    return {
        "parameter_id": decision.parameter_id,
        "question": f"Confirm {decision.parameter_id}",
        "options": decision.available_options,
        "recommended": decision.recommended_value,
        "reason": decision.recommendation_reason,
        "risk_level": decision.risk_level,
        "requires_confirmation": requires_confirmation,
        "must_stop_without_answer": must_stop_without_answer,
    }

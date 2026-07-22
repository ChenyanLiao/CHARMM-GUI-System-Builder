"""Transport selection and duplicate-submission prevention."""

from __future__ import annotations

import copy
from typing import Any

from .capabilities import Capability, CapabilityRegistry
from .schema import SchemaError


SUBMISSION_UNCERTAIN = "submission_uncertain"
SUBMITTED = "submitted"


def select_capability(
    registry: CapabilityRegistry,
    capability_id: str,
    *,
    allowed_routes: set[str] | None = None,
) -> Capability:
    capability = registry.get(capability_id)
    routes = allowed_routes or {"official_api", "audited_browser", "validation_only"}
    if capability.route not in routes:
        raise SchemaError(
            f"capability {capability_id} cannot use route {capability.route}"
        )
    if capability.route == "unsupported":
        raise SchemaError(f"capability {capability_id} is unsupported")
    return capability


def ensure_submission_allowed(
    state: dict[str, Any],
    *,
    contract_sha256: str,
    authorization_ok: bool,
) -> None:
    if not authorization_ok:
        raise SchemaError("execution authorization is not valid")
    if state.get("contract_sha256") not in {None, "", contract_sha256}:
        raise SchemaError("run state belongs to a different build contract")
    if state.get("jobid"):
        raise SchemaError("a jobid already exists; reuse it instead of resubmitting")
    if state.get("submission_state") in {SUBMITTED, SUBMISSION_UNCERTAIN}:
        raise SchemaError("submission was already attempted or is uncertain")
    if int(state.get("submissions_used", 0)) >= int(
        state.get("max_submissions", 1)
    ):
        raise SchemaError("submission allowance exhausted")


def record_submission_success(
    state: dict[str, Any], *, jobid: str, contract_sha256: str
) -> dict[str, Any]:
    if not jobid:
        raise SchemaError("submission response did not contain a jobid")
    updated = copy.deepcopy(state)
    updated.update(
        contract_sha256=contract_sha256,
        jobid=str(jobid),
        submission_state=SUBMITTED,
        submissions_used=int(state.get("submissions_used", 0)) + 1,
        backend_state="pending",
    )
    return updated


def record_submission_uncertain(
    state: dict[str, Any], *, contract_sha256: str, reason: str
) -> dict[str, Any]:
    updated = copy.deepcopy(state)
    updated.update(
        contract_sha256=contract_sha256,
        submission_state=SUBMISSION_UNCERTAIN,
        submissions_used=int(state.get("submissions_used", 0)) + 1,
        needs_user_attention=True,
        status_reason=reason,
    )
    return updated


def require_existing_job(state: dict[str, Any]) -> str:
    jobid = str(state.get("jobid", ""))
    if not jobid:
        raise SchemaError("no existing jobid is available")
    return jobid

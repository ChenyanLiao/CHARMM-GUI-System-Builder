#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Classify an auditable CHARMM-GUI run without modifying it or the website."""

from __future__ import annotations

import argparse
import json
import sys
from fnmatch import fnmatch
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.approvals import verify_authorization  # noqa: E402
from core.contracts import validate_contract  # noqa: E402
from core.credentials import CredentialBroker, create_secret_store  # noqa: E402
from core.io import load_structured  # noqa: E402
from core.schema import SchemaError  # noqa: E402


HUMAN_AUTH_STATES = {
    "login_required",
    "mfa_required",
    "captcha_required",
    "touch_id_required",
    "os_password_required",
}
LARGE_STEP_MARKERS = ("PACKING", "ASSEMBLY", "INPUT_GENERATION")
BROWSER_ACTIONS = {
    "SUBMIT_PDB_READER",
    "SUBMIT_CHAIN_SELECTION",
    "SUBMIT_PDB_MANIPULATION",
    "SUBMIT_CUSTOM_TOPPAR",
    "SUBMIT_PPM",
    "SUBMIT_SYSTEM_SIZE",
    "SUBMIT_LIPID_COMPOSITION",
    "SUBMIT_PACKING",
    "SUBMIT_ION_SOLVENT",
    "SUBMIT_COMPONENT_BUILD",
    "SUBMIT_ASSEMBLY",
    "SUBMIT_INPUT_GENERATION",
    "DOWNLOAD_AND_VALIDATE",
    "DOWNLOAD_AND_VALIDATE_FINAL_PACKAGE",
    "DOWNLOAD_FINAL_PACKAGE",
    "RESUME_LATEST_BROWSER_DOWNLOAD",
    "SWITCH_TO_SAFARI_SAME_JOB",
    "REDOWNLOAD_FINAL_PACKAGE_AUTHENTICATED",
}
LOCAL_ACTIONS = {
    "VALIDATE_DOWNLOAD_ARTIFACT",
    "VALIDATE_FINAL_PACKAGE",
    "VERIFY_CUSTOM_LIGAND_INJECTION",
    "RUN_STRICT_GROMPP",
}
API_ACTIONS = {
    "SUBMIT_QUICK_BILAYER",
    "API_CHECK_STATUS",
    "API_DOWNLOAD_FINAL_PACKAGE",
}
ROUTINE_ACTIONS = BROWSER_ACTIONS | API_ACTIONS | LOCAL_ACTIONS


def cryptographically_verified_actions(
    *,
    state: dict,
    contract: dict,
    authorization: dict,
    signing_key: bytes,
) -> set[str]:
    """Return only actions covered by a valid signed authorization."""
    validate_contract(contract, require_locked=True)
    if state.get("contract_sha256") != contract["contract_sha256"]:
        raise SchemaError("run state belongs to a different build contract")
    verified: set[str] = set()
    for raw_action in authorization.get("allowed_actions", []):
        action = str(raw_action)
        ok, _reason = verify_authorization(
            authorization,
            signing_key=signing_key,
            contract_sha256=contract["contract_sha256"],
            action=action,
            side_effecting_submission=action.upper().startswith("SUBMIT_"),
            submissions_used=int(state.get("submissions_used", 0)),
        )
        if ok:
            verified.add(action.upper())
    return verified


def load_verified_actions(args: argparse.Namespace, state: dict) -> set[str]:
    supplied = [args.contract, args.authorization, args.provider, args.signing_ref]
    if not any(supplied):
        return set()
    if not all(supplied):
        raise SchemaError(
            "--contract, --authorization, --provider, and --signing-ref are required together"
        )
    signing_key = CredentialBroker(create_secret_store(args.provider)).get_signing_key(
        args.signing_ref
    )
    return cryptographically_verified_actions(
        state=state,
        contract=load_structured(args.contract),
        authorization=load_structured(args.authorization),
        signing_key=signing_key,
    )


def action_is_authorized(
    state: dict, action: str, verified_actions: set[str] | None = None
) -> bool:
    action = action.upper()
    if action in LOCAL_ACTIONS:
        return True
    if str(state.get("schema_version", "")) != "2.1":
        legacy = ROUTINE_ACTIONS | {
            str(item).upper() for item in (state.get("autonomous_actions") or [])
        }
        return action in legacy
    return bool(
        state.get("contract_sha256")
        and action in {item.upper() for item in (verified_actions or set())}
    )


def backend_is_complete(value: str) -> bool:
    return value == "complete" or value.startswith("complete_")


def closure_gates_pass(state: dict) -> bool:
    gates = state.get("closure_gates") or {}
    if not gates:
        return bool(state.get("workflow_complete"))
    if str(state.get("schema_version", "")) == "2.1":
        base = bool(
            gates.get("builder_backend_complete")
            and gates.get("archive_verified")
            and gates.get("package_validated")
            and gates.get("strict_grompp_passed")
        )
    else:
        base = bool(gates.get("archive_verified") and gates.get("package_validated"))
    if state.get("custom_ligand_expected"):
        base = base and bool(gates.get("custom_ligand_verified"))
    return base


def effective_next_action(state: dict) -> str:
    recorded = str(state.get("next_allowed_action", "")).upper()
    if recorded:
        return recorded
    download_state = str(state.get("download_state", "")).lower()
    if download_state == "downloaded_unverified":
        return "VALIDATE_DOWNLOAD_ARTIFACT"
    if download_state in {"interrupted", "partial"}:
        return "RESUME_LATEST_BROWSER_DOWNLOAD"
    if download_state == "chrome_retries_exhausted":
        return "SWITCH_TO_SAFARI_SAME_JOB"
    if download_state in {
        "invalid_html", "invalid_artifact", "corrupt_archive", "unsafe_archive"
    }:
        return "REDOWNLOAD_FINAL_PACKAGE_AUTHENTICATED"
    return ""


def read_json(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text())


def probe_rows(report: dict) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for row in report.get("rows", []):
        url = row.get("url", "")
        name = urlparse(url).path.split("/")[-1]
        if name:
            rows[name] = row
    return rows


def content_length(row: dict | None) -> int | None:
    if not row or row.get("status") != 200:
        return None
    value = row.get("content_length")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def classify(
    state: dict,
    current_probe: dict,
    previous_probe: dict,
    *,
    verified_actions: set[str] | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    current = probe_rows(current_probe)
    previous = probe_rows(previous_probe)
    artifact_progress = state.get("artifact_progress") or {}
    polling = state.get("polling") or {}
    required_products = artifact_progress.get(
        "required_products", state.get("required_products", [])
    )
    required = [Path(x).name for x in required_products]
    present = sorted(
        pattern
        for pattern in required
        if any(
            fnmatch(name, pattern) and row.get("status") == 200
            for name, row in current.items()
        )
    )
    missing = sorted(set(required) - set(present))

    grew: list[str] = []
    unchanged: list[str] = []
    for name, row in current.items():
        cur = content_length(row)
        prev = content_length(previous.get(name))
        if cur is None or prev is None:
            continue
        if cur > prev:
            grew.append(name)
        elif cur == prev:
            unchanged.append(name)

    auth_state = str(state.get("auth_state", "unknown")).lower()
    browser_state = str(state.get("browser_state", "unknown")).lower()
    page_state = str(state.get("page_state", "unknown")).lower()
    backend_state = str(state.get("backend_state", "unknown")).lower()
    current_step = str(state.get("current_step", "")).upper()
    next_action = effective_next_action(state)
    human_gate = state.get("human_gate") or {}
    fatal_errors = state.get("fatal_errors") or []
    transient_count = int(
        polling.get(
            "transient_failure_count", state.get("transient_failure_count", 0)
        )
        or 0
    )
    transient_limit = int(
        polling.get(
            "transient_failure_limit", state.get("transient_failure_limit", 3)
        )
        or 3
    )
    unchanged_count = int(
        polling.get(
            "consecutive_unchanged_polls",
            state.get("consecutive_unchanged_polls", 0),
        )
        or 0
    )
    submission_state = str(state.get("submission_state", "")).lower()
    runtime_state = str(state.get("runtime_state", "")).lower()

    decision = "INSPECT_CURRENT_PAGE"
    reason = "No deterministic continuation gate has passed."
    needs_user = False
    poll_seconds = 0

    if submission_state == "submission_uncertain":
        decision = "STOP_SUBMISSION_UNCERTAIN"
        reason = "Submission may have created a job; inspect existing jobs before retrying."
        needs_user = True
    elif fatal_errors or backend_state == "fatal" or runtime_state == "technical_fail":
        decision = "STOP_FATAL"
        reason = "A fatal backend or recorded run error requires review."
        needs_user = True
    elif closure_gates_pass(state) and (
        state.get("workflow_complete") or runtime_state == "technical_pass"
    ):
        decision = "WORKFLOW_COMPLETE"
        reason = "Archive, package, and required custom-ligand closure gates passed."
    elif auth_state in HUMAN_AUTH_STATES:
        decision = "WAIT_FOR_HUMAN_AUTH"
        reason = f"Authentication handoff required: {auth_state}."
        needs_user = True
    elif human_gate.get("status") in {"required", "pending"}:
        decision = "WAIT_FOR_HUMAN_REVIEW"
        reason = human_gate.get("reason") or "A defined scientific human gate is active."
        needs_user = True
    elif runtime_state == "waiting_user_or_authorized_action":
        decision = "WAIT_FOR_AUTHORIZED_ACTION"
        reason = state.get("status_reason") or "A staged action or approval is required."
        needs_user = True
    elif state.get("needs_user_attention"):
        decision = "WAIT_FOR_HUMAN_REVIEW"
        reason = state.get("status_reason") or "The run explicitly requires user attention."
        needs_user = True
    elif (
        next_action in (BROWSER_ACTIONS | API_ACTIONS)
        and not action_is_authorized(state, next_action, verified_actions)
    ):
        decision = "WAIT_FOR_AUTHORIZED_ACTION"
        reason = f"{next_action} is outside the current execution authorization."
        needs_user = True
    elif next_action in LOCAL_ACTIONS and action_is_authorized(
        state, next_action, verified_actions
    ):
        decision = "ADVANCE_ONE_STEP"
        reason = f"Local read-only action {next_action} is ready and does not require browser state."
    elif (
        auth_state == "authenticated"
        and backend_state == "not_submitted"
        and next_action in API_ACTIONS
        and action_is_authorized(state, next_action, verified_actions)
    ):
        decision = "ADVANCE_ONE_STEP"
        reason = f"Authorized official API action {next_action} is ready."
    elif (
        auth_state == "authenticated"
        and browser_state == "connected"
        and page_state == "ready"
        and backend_state == "not_submitted"
        and not state.get("next_clicked")
        and action_is_authorized(state, next_action, verified_actions)
    ):
        decision = "ADVANCE_ONE_STEP"
        reason = (
            f"Routine action {next_action} is ready, whitelisted, and has not "
            "been submitted; no human gate is active."
        )
    elif backend_is_complete(backend_state):
        if (
            next_action in BROWSER_ACTIONS
            and action_is_authorized(state, next_action, verified_actions)
            and auth_state == "authenticated"
            and browser_state == "connected"
            and page_state in {"ready", "complete", "final_page"}
            and not state.get("next_clicked")
        ):
            decision = "ADVANCE_ONE_STEP"
            reason = f"Backend is complete and browser action {next_action} is ready."
        elif page_state in {
            "network_error",
            "running_banner",
            "stale",
            "unknown",
            "backend_complete_page_refresh_pending",
        } and state.get("jobid"):
            decision = "RESUME_WITH_JOB_RETRIEVER"
            reason = "Backend gate is complete while the page is unavailable or stale."
        else:
            decision = "INSPECT_CURRENT_PAGE"
            reason = "Backend is complete; identify the exact next download or validation gate."
    elif page_state == "network_error":
        if transient_count >= transient_limit:
            decision = "STOP_TRANSIENT_RECOVERY_EXHAUSTED"
            reason = "Transient page/network retry budget is exhausted; preserve the job and request assistance."
            needs_user = True
        else:
            decision = "WAIT_NETWORK_RETRY"
            reason = "The page failed, but the server job has not been proven fatal."
            poll_seconds = (300, 600, 1200)[min(transient_count, 2)]
    elif backend_state == "running" or state.get("running"):
        if grew:
            decision = "WAIT_BACKEND_PROGRESS"
            reason = "One or more backend artifacts increased in size."
        elif missing and unchanged_count >= 2:
            decision = "STOP_STALLED"
            reason = "Required products remain missing after two unchanged polls."
            needs_user = True
        else:
            decision = "WAIT_BACKEND_PROGRESS"
            reason = "Backend is running and the stall threshold has not been reached."
        poll_seconds = 1800 if any(x in current_step for x in LARGE_STEP_MARKERS) else 900

    next_poll = ""
    if poll_seconds:
        next_poll = (now + timedelta(seconds=poll_seconds)).isoformat()

    return {
        "timestamp": now.isoformat(),
        "jobid": state.get("jobid", ""),
        "current_step": state.get("current_step", ""),
        "next_allowed_action": next_action,
        "recorded_next_allowed_action": state.get("next_allowed_action", ""),
        "download_state": state.get("download_state", "unknown"),
        "runtime_state": runtime_state or "legacy",
        "submission_state": submission_state or "legacy",
        "decision": decision,
        "reason": reason,
        "needs_user_attention": needs_user,
        "poll_interval_seconds": poll_seconds,
        "next_poll_at": next_poll,
        "required_products_present": present,
        "required_products_missing": missing,
        "artifacts_grew": sorted(grew),
        "artifacts_unchanged": sorted(unchanged),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_state", type=Path)
    parser.add_argument("--probe-current", type=Path)
    parser.add_argument("--probe-previous", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument(
        "--provider", choices=("macos-keychain", "system-keyring")
    )
    parser.add_argument("--signing-ref")
    args = parser.parse_args()

    state = read_json(args.run_state)
    report = classify(
        state,
        read_json(args.probe_current),
        read_json(args.probe_previous),
        verified_actions=load_verified_actions(args, state),
    )
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
        print(args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()

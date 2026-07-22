#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Prevent an unattended CHARMM-GUI candidate run from yielding too early."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from classify_charmmgui_state import (
    API_ACTIONS,
    BROWSER_ACTIONS,
    HUMAN_AUTH_STATES,
    LOCAL_ACTIONS,
    ROUTINE_ACTIONS,
    backend_is_complete,
    closure_gates_pass,
    effective_next_action,
    action_is_authorized,
    load_verified_actions,
)


TERMINAL_STEPS = {
    "FINAL_VALIDATION_COMPLETE",
    "TECHNICAL_PASS_NOT_PRODUCTION_APPROVAL",
    "WORKFLOW_COMPLETE",
}


def evaluate(state: dict, *, verified_actions: set[str] | None = None) -> dict:
    auth_state = str(state.get("auth_state", "unknown")).lower()
    browser_state = str(state.get("browser_state", "unknown")).lower()
    page_state = str(state.get("page_state", "unknown")).lower()
    backend_state = str(state.get("backend_state", "unknown")).lower()
    current_step = str(state.get("current_step", "")).upper()
    next_action = effective_next_action(state)
    human_gate = state.get("human_gate") or {}
    submission_state = str(state.get("submission_state", "")).lower()
    runtime_state = str(state.get("runtime_state", "")).lower()

    result = {
        "jobid": state.get("jobid", ""),
        "current_step": state.get("current_step", ""),
        "next_allowed_action": next_action,
        "recorded_next_allowed_action": state.get("next_allowed_action", ""),
        "download_state": state.get("download_state", "unknown"),
        "decision": "MUST_CONTINUE",
        "safe_to_yield": False,
        "reason": "The workflow has not reached a valid pause or terminal gate.",
    }

    closure_ready = closure_gates_pass(state)

    if submission_state == "submission_uncertain":
        result.update(
            decision="STOP_SUBMISSION_UNCERTAIN",
            safe_to_yield=True,
            reason="Submission outcome is uncertain; inspect existing jobs before retrying.",
        )
    elif state.get("fatal_errors") or backend_state == "fatal" or runtime_state == "technical_fail":
        result.update(
            decision="STOP_FATAL",
            safe_to_yield=True,
            reason="A fatal backend or recorded error requires review.",
        )
    elif (state.get("workflow_complete") or runtime_state == "technical_pass") and closure_ready:
        result.update(
            decision="WORKFLOW_COMPLETE",
            safe_to_yield=True,
            reason="Final archive, package, and required custom-ligand gates are complete.",
        )
    elif current_step in TERMINAL_STEPS and closure_ready:
        result.update(
            decision="WORKFLOW_COMPLETE",
            safe_to_yield=True,
            reason="The terminal step is supported by the V6 closure gates.",
        )
    elif backend_state == "stalled":
        result.update(
            decision="STOP_STALLED",
            safe_to_yield=True,
            reason="The backend is explicitly classified as stalled.",
        )
    elif auth_state in HUMAN_AUTH_STATES:
        result.update(
            decision="WAIT_FOR_HUMAN_AUTH",
            safe_to_yield=True,
            reason=f"Authentication handoff is required: {auth_state}.",
        )
    elif human_gate.get("status") in {"required", "pending"}:
        result.update(
            decision="WAIT_FOR_HUMAN_REVIEW",
            safe_to_yield=True,
            reason=human_gate.get("reason") or "A scientific human gate is active.",
        )
    elif runtime_state == "waiting_user_or_authorized_action":
        result.update(
            decision="WAIT_FOR_AUTHORIZED_ACTION",
            safe_to_yield=True,
            reason=state.get("status_reason") or "A staged action or approval is required.",
        )
    elif state.get("needs_user_attention"):
        result.update(
            decision="WAIT_FOR_USER_ATTENTION",
            safe_to_yield=True,
            reason=state.get("status_reason") or "The run requires user attention.",
        )
    elif (
        next_action in (BROWSER_ACTIONS | API_ACTIONS)
        and not action_is_authorized(state, next_action, verified_actions)
    ):
        result.update(
            decision="WAIT_FOR_AUTHORIZED_ACTION",
            safe_to_yield=True,
            reason=f"{next_action} is outside the current execution authorization.",
        )
    elif next_action in LOCAL_ACTIONS and action_is_authorized(
        state, next_action, verified_actions
    ):
        result.update(
            decision="EXECUTE_LOCAL_VALIDATION_NOW",
            reason=f"{next_action} is a ready local validation action; execute it before yielding.",
        )
    elif (
        auth_state == "authenticated"
        and browser_state == "connected"
        and page_state == "ready"
        and backend_state == "not_submitted"
        and not state.get("next_clicked")
        and next_action in BROWSER_ACTIONS
        and action_is_authorized(state, next_action, verified_actions)
    ):
        result.update(
            decision="EXECUTE_ROUTINE_ACTION_NOW",
            reason=f"{next_action} is ready and whitelisted; execute it before yielding.",
        )
    elif (
        auth_state == "authenticated"
        and backend_state == "not_submitted"
        and next_action in API_ACTIONS
        and action_is_authorized(state, next_action, verified_actions)
    ):
        result.update(
            decision="EXECUTE_ROUTINE_ACTION_NOW",
            reason=f"Authorized official API action {next_action} is ready.",
        )
    elif backend_is_complete(backend_state):
        result.update(
            decision="RECOVER_OR_ADVANCE_NOW",
            reason="The backend gate is complete; acquire or validate the final package before yielding.",
        )
    elif backend_state == "running" or state.get("running"):
        result.update(
            decision="KEEP_POLLING",
            reason="The backend is running; keep the task alive and poll at the recorded interval.",
        )
    elif page_state == "network_error":
        result.update(
            decision="RETRY_AFTER_COOLDOWN",
            reason="The page has a transient network error; preserve the job and retry within budget.",
        )
    else:
        result.update(
            decision="INSPECT_AND_UPDATE_STATE",
            reason="No valid pause gate is active; inspect the page and update RUN_STATE.",
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_state", type=Path)
    parser.add_argument("--always-zero", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument(
        "--provider", choices=("macos-keychain", "system-keyring")
    )
    parser.add_argument("--signing-ref")
    args = parser.parse_args()

    state = json.loads(args.run_state.read_text())
    result = evaluate(
        state,
        verified_actions=load_verified_actions(args, state),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not args.always_zero and not result["safe_to_yield"]:
        raise SystemExit(20)


if __name__ == "__main__":
    main()

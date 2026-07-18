#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from classify_charmmgui_state import classify  # noqa: E402
from continuation_guard import evaluate  # noqa: E402


def base_state() -> dict:
    return {
        "jobid": "9000000004",
        "current_step": "SYSTEM_SIZE_READY_TO_SUBMIT",
        "next_allowed_action": "SUBMIT_SYSTEM_SIZE",
        "next_clicked": False,
        "auth_state": "authenticated",
        "browser_state": "connected",
        "page_state": "ready",
        "backend_state": "not_submitted",
        "needs_user_attention": False,
        "human_gate": {"type": "none", "status": "inactive", "reason": ""},
        "fatal_errors": [],
        "required_products": ["step3_size.str"],
        "running": False,
        "workflow_complete": False,
        "custom_ligand_expected": True,
        "closure_gates": {
            "archive_verified": False,
            "package_validated": False,
            "custom_ligand_verified": False,
            "strict_grompp_passed": False,
        },
    }


class ClassifierTests(unittest.TestCase):
    def test_ready_routine_action_advances(self) -> None:
        report = classify(base_state(), {}, {})
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")
        self.assertFalse(report["needs_user_attention"])

    def test_pending_human_gate_stops(self) -> None:
        state = base_state()
        state["human_gate"] = {
            "type": "membrane_orientation",
            "status": "pending",
            "reason": "Review orientation.",
        }
        report = classify(state, {}, {})
        self.assertEqual(report["decision"], "WAIT_FOR_HUMAN_REVIEW")
        self.assertTrue(report["needs_user_attention"])

    def test_unsubmitted_action_is_not_reclicked(self) -> None:
        state = base_state()
        state["next_clicked"] = True
        report = classify(state, {}, {})
        self.assertNotEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_unknown_auth_does_not_advance(self) -> None:
        state = base_state()
        state["auth_state"] = "unknown"
        report = classify(state, {}, {})
        self.assertNotEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_disconnected_browser_does_not_advance(self) -> None:
        state = base_state()
        state["browser_state"] = "disconnected"
        report = classify(state, {}, {})
        self.assertNotEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_run_specific_allowlist_advances(self) -> None:
        state = base_state()
        state["next_allowed_action"] = "SUBMIT_PROJECT_SPECIFIC_PAGE"
        state["autonomous_actions"] = ["SUBMIT_PROJECT_SPECIFIC_PAGE"]
        report = classify(state, {}, {})
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_complete_normal_termination_advances_to_download(self) -> None:
        state = base_state()
        state.update(
            current_step="STEP6_INPUT_GENERATION_COMPLETE",
            next_allowed_action="DOWNLOAD_FINAL_PACKAGE",
            page_state="final_page",
            backend_state="complete_normal_termination",
        )
        report = classify(state, {}, {})
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_local_download_validation_does_not_require_browser(self) -> None:
        state = base_state()
        state.update(
            next_allowed_action="VALIDATE_DOWNLOAD_ARTIFACT",
            browser_state="disconnected",
            page_state="unknown",
            backend_state="complete_normal_termination",
        )
        report = classify(state, {}, {})
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_required_product_glob_matches_probe_filename(self) -> None:
        state = base_state()
        state.update(
            backend_state="running",
            page_state="running_banner",
            running=True,
            required_products=["*.gro", "topol.top"],
        )
        current = {
            "rows": [
                {"url": "https://example.invalid/job/system.gro", "status": 200},
                {"url": "https://example.invalid/job/topol.top", "status": 200},
            ]
        }
        report = classify(state, current, {})
        self.assertEqual(report["required_products_missing"], [])
        self.assertEqual(report["required_products_present"], ["*.gro", "topol.top"])

    def test_download_state_infers_local_inspection(self) -> None:
        state = base_state()
        state.update(
            next_allowed_action="",
            download_state="downloaded_unverified",
            browser_state="disconnected",
        )
        report = classify(state, {}, {})
        self.assertEqual(report["next_allowed_action"], "VALIDATE_DOWNLOAD_ARTIFACT")
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_interrupted_download_resumes_latest_record(self) -> None:
        state = base_state()
        state.update(
            next_allowed_action="",
            download_state="interrupted",
            backend_state="complete_normal_termination",
            page_state="final_page",
            browser_state="connected",
            auth_state="authenticated",
        )
        report = classify(state, {}, {})
        self.assertEqual(report["next_allowed_action"], "RESUME_LATEST_BROWSER_DOWNLOAD")
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")

    def test_exhausted_chrome_download_switches_same_job_to_safari(self) -> None:
        state = base_state()
        state.update(
            next_allowed_action="",
            download_state="chrome_retries_exhausted",
            backend_state="complete_normal_termination",
            page_state="final_page",
            browser_state="connected",
            auth_state="authenticated",
        )
        report = classify(state, {}, {})
        self.assertEqual(report["next_allowed_action"], "SWITCH_TO_SAFARI_SAME_JOB")
        self.assertEqual(report["decision"], "ADVANCE_ONE_STEP")


class ContinuationGuardTests(unittest.TestCase):
    def test_ready_action_must_continue(self) -> None:
        report = evaluate(base_state())
        self.assertEqual(report["decision"], "EXECUTE_ROUTINE_ACTION_NOW")
        self.assertFalse(report["safe_to_yield"])

    def test_running_backend_keeps_polling(self) -> None:
        state = base_state()
        state.update(backend_state="running", page_state="running_banner", running=True)
        report = evaluate(state)
        self.assertEqual(report["decision"], "KEEP_POLLING")
        self.assertFalse(report["safe_to_yield"])

    def test_human_gate_allows_yield(self) -> None:
        state = base_state()
        state["human_gate"] = {
            "type": "membrane_orientation",
            "status": "pending",
            "reason": "Review orientation.",
        }
        report = evaluate(state)
        self.assertEqual(report["decision"], "WAIT_FOR_HUMAN_REVIEW")
        self.assertTrue(report["safe_to_yield"])

    def test_verified_completion_allows_yield(self) -> None:
        state = base_state()
        state["workflow_complete"] = True
        state["closure_gates"].update(
            archive_verified=True,
            package_validated=True,
            custom_ligand_verified=True,
        )
        report = evaluate(state)
        self.assertEqual(report["decision"], "WORKFLOW_COMPLETE")
        self.assertTrue(report["safe_to_yield"])

    def test_false_completion_flag_does_not_bypass_closure_gates(self) -> None:
        state = base_state()
        state["workflow_complete"] = True
        report = evaluate(state)
        self.assertFalse(report["safe_to_yield"])
        self.assertNotEqual(report["decision"], "WORKFLOW_COMPLETE")

    def test_local_validation_must_run_before_yield(self) -> None:
        state = base_state()
        state.update(
            next_allowed_action="VALIDATE_DOWNLOAD_ARTIFACT",
            browser_state="disconnected",
            page_state="unknown",
            backend_state="complete_normal_termination",
        )
        report = evaluate(state)
        self.assertEqual(report["decision"], "EXECUTE_LOCAL_VALIDATION_NOW")
        self.assertFalse(report["safe_to_yield"])

    def test_fatal_error_allows_review_handoff(self) -> None:
        state = base_state()
        state["fatal_errors"] = ["CHARMM fatal error"]
        report = evaluate(state)
        self.assertEqual(report["decision"], "STOP_FATAL")
        self.assertTrue(report["safe_to_yield"])


if __name__ == "__main__":
    unittest.main()

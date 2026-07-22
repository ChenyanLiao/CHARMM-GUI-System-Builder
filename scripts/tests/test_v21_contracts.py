from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.approvals import (  # noqa: E402
    append_approval,
    mint_authorization,
    verify_authorization,
)
from core.contracts import (  # noqa: E402
    create_revision,
    lock_contract,
    validate_contract,
    verify_contract_hash,
)
from core.decisions import (  # noqa: E402
    Evidence,
    RiskLevel,
    assess_drift,
    build_decision,
    guided_question,
)
from core.evidence import append_event, make_event, make_page_event  # noqa: E402
from core.schema import SchemaError  # noqa: E402


def draft_contract() -> dict:
    return {
        "schema_version": "2.1",
        "run_id": "run-example",
        "target_id": "target-example",
        "builder": "membrane_builder",
        "mode": "test_only",
        "inputs": [
            {
                "role": "cleaned_pdb",
                "path": "/example/input.pdb",
                "size_bytes": 123,
                "sha256": "a" * 64,
            }
        ],
        "parameters": {
            "membrane.upper_leaflet": "POPC:CHL1=70:30",
            "membrane.ions.type": "NaCl",
            "membrane.ions.concentration_m": 0.15,
        },
        "decision_records": [
            {
                "parameter_id": parameter_id,
                "recommended_value": value,
                "evidence_sources": [],
                "risk_level": "Contextual",
                "contract_value": value,
                "approval_status": "confirmed",
            }
            for parameter_id, value in {
                "membrane.upper_leaflet": "POPC:CHL1=70:30",
                "membrane.ions.type": "NaCl",
                "membrane.ions.concentration_m": 0.15,
            }.items()
        ],
        "production_ready": False,
        "no_mdrun": True,
    }


class ContractTests(unittest.TestCase):
    def test_lock_is_deterministic_and_verifiable(self) -> None:
        first = lock_contract(draft_contract())
        second = lock_contract(draft_contract())
        self.assertEqual(first["contract_sha256"], second["contract_sha256"])
        self.assertTrue(verify_contract_hash(first))
        validate_contract(first, require_locked=True)

    def test_mutation_invalidates_hash(self) -> None:
        contract = lock_contract(draft_contract())
        contract["parameters"]["membrane.ions.type"] = "KCl"
        self.assertFalse(verify_contract_hash(contract))

    def test_revision_is_non_destructive_and_diffed(self) -> None:
        original = lock_contract(draft_contract())
        revised_draft = draft_contract()
        revised_draft["parameters"]["membrane.ions.type"] = "KCl"
        next(
            row
            for row in revised_draft["decision_records"]
            if row["parameter_id"] == "membrane.ions.type"
        )["contract_value"] = "KCl"
        revised, changes = create_revision(original, revised_draft)
        self.assertEqual(original["revision"], 1)
        self.assertEqual(revised["revision"], 2)
        self.assertEqual(
            revised["supersedes_contract_sha256"], original["contract_sha256"]
        )
        self.assertTrue(
            any(
                row["path"] == "$.parameters.membrane.ions.type"
                for row in changes
            )
        )

    def test_secret_fields_are_rejected(self) -> None:
        draft = draft_contract()
        draft["password"] = "fictional-do-not-store"
        with self.assertRaises(SchemaError):
            lock_contract(draft)

    def test_equivalent_secret_field_names_are_rejected(self) -> None:
        for field in (
            "Authorization",
            "sessionid",
            "set-cookie",
            "private_key",
            "credential",
            "apikey",
            "client_secret",
        ):
            draft = draft_contract()
            draft[field] = "fictional-do-not-store"
            with self.subTest(field=field), self.assertRaises(SchemaError):
                lock_contract(draft)


class DecisionTests(unittest.TestCase):
    def test_material_conflict_escalates_to_critical(self) -> None:
        decision = build_decision(
            parameter_id="membrane.ions.type",
            module="membrane_builder",
            page_or_step="step3",
            value_type="enum",
            options=["NaCl", "KCl"],
            evidence=[
                Evidence("user_experimental_condition", "KCl", confidence="high"),
                Evidence("versioned_rule", "NaCl", confidence="medium"),
            ],
            reason="Experimental buffer conflicts with the routine rule.",
            default_risk=RiskLevel.CONTEXTUAL,
        )
        self.assertEqual(decision.recommended_value, "KCl")
        self.assertEqual(decision.risk_level, "Critical")
        self.assertTrue(decision.material_conflict)

    def test_chemical_identity_cannot_use_temporary_assumption(self) -> None:
        decision = build_decision(
            parameter_id="ligand.chemical_identity",
            module="ligand_reader",
            page_or_step="preflight",
            value_type="string",
            options=[],
            evidence=[],
            reason="Identity is unknown.",
        )
        question = guided_question(decision)
        self.assertEqual(decision.risk_level, "Critical")
        self.assertFalse(decision.temporary_assumption_allowed)
        self.assertTrue(question["must_stop_without_answer"])

    def test_critical_drift_blocks_production(self) -> None:
        decision = build_decision(
            parameter_id="membrane.orientation",
            module="membrane_builder",
            page_or_step="step2",
            value_type="enum",
            options=["ppm", "reviewed_input_orientation"],
            evidence=[Evidence("approved_target_profile", "ppm", confidence="high")],
            reason="Orientation must match the reviewed contract.",
            default_risk=RiskLevel.CRITICAL,
        )
        decision.contract_value = "ppm"
        report = assess_drift(
            decision,
            actual_value="reviewed_input_orientation",
            hidden_value="reviewed_input_orientation",
        )
        self.assertEqual(report["status"], "BLOCK_PRODUCTION")
        self.assertFalse(report["production_ready"])

    def test_uncaptured_control_is_missing(self) -> None:
        decision = build_decision(
            parameter_id="membrane.ions.type",
            module="membrane_builder",
            page_or_step="step3",
            value_type="enum",
            options=["NaCl", "KCl"],
            evidence=[Evidence("versioned_rule", "NaCl")],
            reason="Salt must be captured.",
        )
        decision.contract_value = "NaCl"
        self.assertEqual(assess_drift(decision)["status"], "MISSING")


class AuthorizationAndEvidenceTests(unittest.TestCase):
    def test_scoped_authorization_verifies_and_expires(self) -> None:
        key = b"fictional-test-signing-key"
        expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        authorization = mint_authorization(
            contract_sha256="b" * 64,
            allowed_actions=["submit_approved_contract", "check_status"],
            expires_at=expiry,
            signing_key=key,
            approval_origin="preauthorized_signed_contract",
            max_submissions=1,
        )
        ok, reason = verify_authorization(
            authorization,
            signing_key=key,
            contract_sha256="b" * 64,
            action="submit_approved_contract",
            side_effecting_submission=True,
        )
        self.assertTrue(ok, reason)

        ok, reason = verify_authorization(
            authorization,
            signing_key=key,
            contract_sha256="b" * 64,
            action="submit_approved_contract",
            side_effecting_submission=True,
            submissions_used=1,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "submission allowance exhausted")

        expired = datetime.now(timezone.utc) + timedelta(hours=2)
        ok, reason = verify_authorization(
            authorization,
            signing_key=key,
            contract_sha256="b" * 64,
            action="check_status",
            now=expired,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "authorization expired")

    def test_tampering_fails_integrity_check(self) -> None:
        key = b"fictional-test-signing-key"
        authorization = mint_authorization(
            contract_sha256="c" * 64,
            allowed_actions=["check_status"],
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            signing_key=key,
            approval_origin="local_os_confirmed",
        )
        authorization["allowed_actions"].append("submit_approved_contract")
        ok, reason = verify_authorization(
            authorization,
            signing_key=key,
            contract_sha256="c" * 64,
            action="check_status",
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "authorization integrity check failed")

    def test_ledgers_are_append_only_and_evidence_is_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            approval_path = Path(temp) / "APPROVAL_LEDGER.jsonl"
            evidence_path = Path(temp) / "EVIDENCE_LEDGER.jsonl"
            append_approval(
                approval_path,
                {
                    "schema_version": "2.1",
                    "stage": "initial_contract",
                    "contract_sha256": "d" * 64,
                    "approval_origin": "remote_user_confirmed",
                },
            )
            event = make_event(
                action="login",
                request={"password": "fictional", "email": "user@example.invalid"},
            )
            append_event(evidence_path, event)

            approval_rows = approval_path.read_text().splitlines()
            evidence_row = json.loads(evidence_path.read_text())
            self.assertEqual(len(approval_rows), 1)
            self.assertNotIn("fictional", evidence_path.read_text())
            self.assertEqual(
                evidence_row["request"]["password_redacted"], "[REDACTED]"
            )

    def test_login_page_capture_is_fully_suppressed(self) -> None:
        event = make_page_event(
            action="login",
            page_fields={"email": "user@example.invalid", "password": "fictional"},
            screenshot_path="/tmp/login.png",
        )
        self.assertTrue(event["capture_suppressed"])
        self.assertEqual(event["page_fields"], {})
        self.assertEqual(event["screenshot_path"], "")

    def test_named_secret_field_and_url_query_are_redacted(self) -> None:
        event = make_page_event(
            action="capture_form",
            page_fields=[
                {"name": "csrf_token", "value": "fictional-sensitive-value"},
                {"name": "salt", "value": "NaCl"},
            ],
            current_url=(
                "https://example.invalid/build?jobid=1&session_token="
                "fictional-sensitive-value"
            ),
        )
        serialized = json.dumps(event)
        self.assertNotIn("fictional-sensitive-value", serialized)
        self.assertIn("NaCl", serialized)
        self.assertIn("%5BREDACTED%5D", event["current_url"])
        self.assertNotIn("fictional", json.dumps(event))

    def test_authorization_header_and_sessionid_are_redacted(self) -> None:
        event = make_event(
            headers={
                "Authorization": "Bearer fictional-sensitive-value",
                "set-cookie": "sessionid=fictional-sensitive-value",
            },
            form={"name": "private_key", "value": "fictional-sensitive-value"},
        )
        serialized = json.dumps(event)
        self.assertNotIn("fictional-sensitive-value", serialized)
        self.assertIn("authorization_redacted", serialized)
        self.assertIn("set_cookie_redacted", serialized)


if __name__ == "__main__":
    unittest.main()

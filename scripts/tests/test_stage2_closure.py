from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.closure import build_closure_payload  # noqa: E402
from core.contracts import lock_contract  # noqa: E402
from core.shared import activate_vendor  # noqa: E402


class Stage2ClosureTests(unittest.TestCase):
    def test_contract_derived_closure_locks_and_verifies(self) -> None:
        activate_vendor()
        from simulation_stage_contracts.evidence import build_evidence_index
        from simulation_stage_contracts.receipts import audit_receipt_payload, lock_receipt, verify_receipt

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            handoff = {"record_type": "system-build-handoff", "schema_version": "1.1"}
            handoff_path = root / "handoff.json"
            handoff_path.write_text(json.dumps(handoff))
            draft = {
                "schema_version": "2.1",
                "run_id": "synthetic-pipeline",
                "pipeline_id": "synthetic-pipeline",
                "branch_id": "synthetic-branch",
                "target_id": "synthetic-target",
                "builder": "membrane_builder",
                "mode": "test_only",
                "inputs": [],
                "parameters": {"ligand.custom_parameter_submission": False},
                "decision_records": [{"parameter_id": "ligand.custom_parameter_submission", "recommended_value": False, "evidence_sources": [], "risk_level": "Contextual", "contract_value": False, "approval_status": "confirmed"}],
                "production_ready": False,
                "no_mdrun": True,
            }
            contract = lock_contract(draft)
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract))
            index = build_evidence_index([{"id": "package", "sha256": "c" * 64, "current_sha256": "c" * 64}])
            payload = build_closure_payload(
                contract_path=contract_path,
                contract=contract,
                handoff_path=handoff_path,
                handoff=handoff,
                package_report={"package": "package.tar", "sha256": "c" * 64, "package_size_bytes": 100, "validation_passed": True},
                evidence_index=index,
                semantic_topology={"status": "PASS"},
                segment_matrix={"status": "PASS"},
                preprocessing={"strict_preprocessing_passed": True, "maxwarn_used": False, "gromacs": {"version": "synthetic"}},
                tpr_readback={"passed": True},
            )
            self.assertTrue(audit_receipt_payload(payload)["passed"])
            receipt_path = root / "receipt.yaml"
            chain_path = root / "chain.jsonl"
            receipt = lock_receipt(receipt_path, chain_path, payload)
            self.assertFalse(receipt["permissions"]["production_ready"])
            self.assertTrue(verify_receipt(receipt_path, chain_path, index)["receipt_valid"])

    def test_required_custom_parameter_failure_blocks(self) -> None:
        activate_vendor()
        from simulation_stage_contracts.receipts import audit_receipt_payload

        payload = {
            "pipeline_id": "p", "branch_id": "b", "revision": 1,
            "closure_state": "BLOCKED", "evidence_freshness": "FRESH",
            "package": {"sha256": "c" * 64, "size": 1},
            "semantic_topology": {"status": "PASS"}, "segment_matrix": {"status": "PASS"},
            "custom_parameter_required": True, "parameter_injection": {"status": "FAIL"},
            "gromacs": {"version": "synthetic"},
            "preprocessing": {"strict_preprocessing_passed": True, "maxwarn_used": False},
            "tpr_readback": {"passed": True}, "validators": {"shared_core": "1.0.0"},
        }
        audit = audit_receipt_payload(payload)
        self.assertFalse(audit["passed"])
        self.assertTrue(any(row["code"] == "E_PARAMETER_INJECTION_UNVERIFIED" for row in audit["blockers"]))

    def test_environment_altered_candidate_is_preserved_in_receipt(self) -> None:
        activate_vendor()
        from simulation_stage_contracts.evidence import build_evidence_index
        from simulation_stage_contracts.receipts import audit_receipt_payload, lock_receipt

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            handoff = {"record_type": "system-build-handoff", "schema_version": "1.1"}
            handoff_path = root / "handoff.json"
            handoff_path.write_text(json.dumps(handoff))
            contract = lock_contract(
                {
                    "run_id": "environment-pipeline",
                    "pipeline_id": "environment-pipeline",
                    "branch_id": "candidate",
                    "target_id": "synthetic-target",
                    "builder": "membrane_builder",
                    "mode": "test_only",
                    "inputs": [],
                    "parameters": {},
                    "decision_records": [],
                    "structural_environment": {"required": True},
                    "pose_preservation": {"required": True},
                    "restraint_handoff": {"required": True},
                    "production_ready": False,
                    "no_mdrun": True,
                }
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract))
            index = build_evidence_index(
                [{"id": "package", "sha256": "c" * 64, "current_sha256": "c" * 64}]
            )
            scientific_context = {
                "passed": True,
                "structural_environment": {
                    "required": True,
                    "status": "ALTERED_APPROVED_CANDIDATE",
                    "passed": True,
                    "environmental_equivalence": False,
                    "downstream_sensitivity_required": True,
                },
                "pose_preservation": {"required": True, "status": "PASS", "passed": True},
                "restraint_handoff": {
                    "required": True,
                    "status": "PASS",
                    "passed": True,
                    "stage2_mdrun_performed": False,
                },
                "production_ready": False,
                "md_execution_allowed": False,
                "no_mdrun": True,
            }
            payload = build_closure_payload(
                contract_path=contract_path,
                contract=contract,
                handoff_path=handoff_path,
                handoff=handoff,
                package_report={
                    "package": "package.tar",
                    "sha256": "c" * 64,
                    "package_size_bytes": 100,
                    "validation_passed": True,
                },
                evidence_index=index,
                semantic_topology={"status": "PASS"},
                segment_matrix={"status": "PASS"},
                preprocessing={
                    "strict_preprocessing_passed": True,
                    "maxwarn_used": False,
                    "gromacs": {"version": "synthetic"},
                },
                tpr_readback={"passed": True},
                scientific_context=scientific_context,
            )
            self.assertTrue(audit_receipt_payload(payload)["passed"])
            receipt = lock_receipt(root / "receipt.yaml", root / "chain.jsonl", payload)
            self.assertEqual(
                receipt["scientific_context"]["structural_environment"]["status"],
                "ALTERED_APPROVED_CANDIDATE",
            )
            self.assertFalse(receipt["permissions"]["production_ready"])
            self.assertTrue(receipt["no_mdrun"])

    def test_false_environmental_equivalence_claim_is_blocked(self) -> None:
        activate_vendor()
        from simulation_stage_contracts.receipts import audit_receipt_payload

        payload = {
            "pipeline_id": "p",
            "branch_id": "b",
            "revision": 1,
            "closure_state": "TECHNICAL_PASS",
            "evidence_freshness": "FRESH",
            "package": {"sha256": "c" * 64, "size": 1},
            "semantic_topology": {"status": "PASS"},
            "segment_matrix": {"status": "PASS"},
            "custom_parameter_required": False,
            "scientific_context_required": True,
            "scientific_context": {
                "passed": True,
                "structural_environment": {
                    "required": True,
                    "status": "ALTERED_APPROVED_CANDIDATE",
                    "environmental_equivalence": True,
                    "downstream_sensitivity_required": True,
                },
                "pose_preservation": {"required": True, "status": "PASS"},
                "restraint_handoff": {"required": True, "status": "PASS"},
            },
            "gromacs": {"version": "synthetic"},
            "preprocessing": {"strict_preprocessing_passed": True, "maxwarn_used": False},
            "tpr_readback": {"passed": True},
            "validators": {"shared_core": "1.0.0"},
        }
        audit = audit_receipt_payload(payload)
        self.assertFalse(audit["passed"])
        self.assertTrue(
            any(row["code"] == "E_ENVIRONMENT_LEDGER_MISMATCH" for row in audit["blockers"])
        )


if __name__ == "__main__":
    unittest.main()

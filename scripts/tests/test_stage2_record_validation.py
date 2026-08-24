from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.contracts import lock_contract  # noqa: E402
from core.shared import activate_vendor  # noqa: E402


def locked_contract() -> dict:
    return lock_contract(
        {
            "schema_version": "2.1",
            "run_id": "synthetic-pipeline",
            "pipeline_id": "synthetic-pipeline",
            "branch_id": "synthetic-branch",
            "target_id": "synthetic-target",
            "builder": "membrane_builder",
            "mode": "test_only",
            "inputs": [],
            "parameters": {"ligand.custom_parameter_submission": False},
            "decision_records": [
                {
                    "parameter_id": "ligand.custom_parameter_submission",
                    "recommended_value": False,
                    "evidence_sources": [],
                    "risk_level": "Contextual",
                    "contract_value": False,
                    "approval_status": "confirmed",
                }
            ],
            "production_ready": False,
            "no_mdrun": True,
        }
    )


def synthetic_handoff() -> dict:
    artifact = {"path": "synthetic.dat", "sha256": "a" * 64}
    return {
        "schema_version": "1.1",
        "handoff_id": "synthetic-handoff",
        "status": "READY_FOR_SYSTEM_BUILD",
        "handoff_ready": True,
        "system_build_execution_approved": False,
        "md_execution_allowed": False,
        "production_allowed": False,
        "readiness_report": artifact,
        "protein": {
            "approved_path": "protein.pdb",
            "sha256": "a" * 64,
            "segments": ["PROA"],
            "missing_residue_strategy": "preserve-approved-gaps",
        },
        "ligand": {
            "residue_name": "LIG",
            "formal_charge": 1,
            "bound_pose": artifact,
            "parameterization_geometry": artifact,
            "atom_mapping": artifact,
        },
        "complex": artifact,
        "pose": {
            "source_type": "user_selected",
            "selection_record": artifact,
            "heavy_atom_rmsd_angstrom": 0.0,
            "heavy_atom_tolerance_angstrom": 0.001,
            "tolerance_approval": "synthetic-test",
        },
        "parameters": {
            "force_field_family": "synthetic",
            "route_version": "1",
            "maturity": "Stable",
            "package": artifact,
            "validation_report": artifact,
            "provenance": {
                "historical_quality_annotations": [],
                "active_parameter_package_status": "PASS",
                "transferred_parameter_terms": {
                    "status": "NOT_APPLICABLE",
                    "expected": None,
                    "matched": None,
                },
                "atomic_charges": {
                    "refit": False,
                    "validation_status": "PASS",
                    "evidence_key": "synthetic-validation",
                },
            },
        },
        "retained_components": {"metals": [], "cofactors": [], "waters": []},
        "component_name_mappings": [],
        "target_system": {
            "type": "membrane",
            "requirements": {},
            "protonation_context": {
                "reference_ph": 7.0,
                "reference_ph_source": "computational_assumption",
                "protein_policy": "preserve_approved_state",
                "ligand_policy": "preserve_approved_microstate",
                "residue_overrides": [],
            },
        },
        "unresolved_assumptions": [],
        "approvals": {
            "pose_selection": artifact,
            "parameter_package": artifact,
            "complex_handoff": artifact,
        },
        "checksums": artifact,
    }


class Stage2RecordValidationTests(unittest.TestCase):
    def test_locked_contract_cli_verifies_hash_and_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.json"
            path.write_text(json.dumps(locked_contract()), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/validate_build_contract.py"),
                    str(path),
                    "--pipeline-id",
                    "synthetic-pipeline",
                    "--branch-id",
                    "synthetic-branch",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["contract_state"], "LOCKED")

    def test_tampered_locked_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.json"
            contract = locked_contract()
            contract["branch_id"] = "other-branch"
            path.write_text(json.dumps(contract), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_build_contract.py"), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["contract_state"], "INVALID")

    def test_forged_closure_pass_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            closure = root / "closure.json"
            contract = root / "contract.json"
            handoff = root / "handoff.json"
            evidence = root / "evidence.json"
            closure.write_text(
                json.dumps(
                    {
                        "record_type": "system-build-closure-draft",
                        "schema_version": "1.0",
                        "payload": {"closure_state": "TECHNICAL_PASS"},
                        "audit": {"passed": True, "status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )
            contract.write_text(json.dumps(locked_contract()), encoding="utf-8")
            handoff.write_text(
                json.dumps({"record_type": "system-build-handoff", "schema_version": "1.1"}),
                encoding="utf-8",
            )
            evidence.write_text(
                json.dumps(
                    {
                        "record_type": "evidence-index",
                        "schema_version": "1.0",
                        "nodes": [],
                        "root_sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_system_build_closure.py"),
                    str(closure),
                    "--contract",
                    str(contract),
                    "--handoff",
                    str(handoff),
                    "--evidence-index",
                    str(evidence),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertFalse(result["success"])
        self.assertEqual(result["closure_state"], "BLOCKED")

    def test_valid_closure_replays_all_bound_evidence(self) -> None:
        activate_vendor()
        from simulation_stage_contracts.evidence import build_evidence_index
        from simulation_stage_contracts.receipts import audit_receipt_payload
        from core.closure import build_closure_payload

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "package.tar"
            package.write_bytes(b"synthetic-package")
            contract_value = locked_contract()
            handoff_value = synthetic_handoff()
            contract = root / "contract.json"
            handoff = root / "handoff.json"
            evidence = root / "evidence.json"
            closure = root / "closure.json"
            contract.write_text(json.dumps(contract_value), encoding="utf-8")
            handoff.write_text(json.dumps(handoff_value), encoding="utf-8")
            index = build_evidence_index(
                [{"id": "package", "sha256": "c" * 64, "current_sha256": "c" * 64}]
            )
            evidence.write_text(json.dumps(index), encoding="utf-8")
            payload = build_closure_payload(
                contract_path=contract,
                contract=contract_value,
                handoff_path=handoff,
                handoff=handoff_value,
                package_report={
                    "package": str(package),
                    "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
                    "package_size_bytes": package.stat().st_size,
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
            )
            audit = audit_receipt_payload(payload)
            closure.write_text(
                json.dumps(
                    {
                        "record_type": "system-build-closure-draft",
                        "schema_version": "1.0",
                        "payload": payload,
                        "audit": audit,
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/verify_system_build_closure.py"),
                    str(closure),
                    "--contract",
                    str(contract),
                    "--handoff",
                    str(handoff),
                    "--evidence-index",
                    str(evidence),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(result["success"])
        self.assertEqual(result["evidence_freshness"], "FRESH")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(SCRIPTS))

from core.contracts import lock_contract  # noqa: E402
from fixture_factory import COMPONENTS, create_download_archive  # noqa: E402
from migrate_v1_state import migrate_state  # noqa: E402
from validate_charmmgui_package import validate  # noqa: E402


def locked_contract() -> dict:
    parameters = {
        "membrane.upper_leaflet": "POPC:CHL1=70:30",
        "membrane.lower_leaflet": "POPC:CHL1=70:30",
        "membrane.ions.internal_names": "SOD/CLA",
        "membrane.water_model": "TIP3P",
    }
    return lock_contract(
        {
            "schema_version": "2.1",
            "run_id": "fixture-v21",
            "target_id": "fixture-target",
            "builder": "membrane_builder",
            "mode": "test_only",
            "inputs": [],
            "parameters": parameters,
            "decision_records": [
                {
                    "parameter_id": parameter_id,
                    "recommended_value": value,
                    "evidence_sources": [],
                    "risk_level": "Contextual",
                    "contract_value": value,
                    "approval_status": "confirmed",
                }
                for parameter_id, value in parameters.items()
            ],
            "expected_output": {
                "components": ["CAL"],
                "protein_segments": [
                    "PROA",
                    "PROB",
                    "PROC",
                    "PROD",
                    "PROE",
                    "PROF",
                    "PROG",
                    "PROH",
                    "PROI",
                ],
                "ligand": {
                    "required": True,
                    "residue_name": "LIG",
                    "formal_charge": 1,
                },
            },
            "production_ready": False,
            "no_mdrun": True,
        }
    )


class MigrationTests(unittest.TestCase):
    def test_migration_is_non_destructive_and_redacts_secrets(self) -> None:
        legacy = {
            "schema_version": 6,
            "run_id": "legacy-run",
            "jobid": "1234567890",
            "backend_state": "running",
            "password": "fictional-password",
            "nested": {"session_token": "fictional-token"},
            "warnings": ["Authorization: Bearer fictional-warning-token"],
            "fatal_errors": ["sessionid=fictional-session-value"],
        }
        original = copy.deepcopy(legacy)

        state, report = migrate_state(legacy)

        self.assertEqual(legacy, original)
        self.assertEqual(state["schema_version"], "2.1")
        self.assertEqual(state["runtime_state"], "technical_fail")
        self.assertEqual(state["submission_state"], "submitted")
        self.assertEqual(state["legacy_state"]["password_redacted"], "[REDACTED]")
        self.assertEqual(
            state["legacy_state"]["nested"]["session_token_redacted"],
            "[REDACTED]",
        )
        self.assertNotIn("fictional-password", json.dumps(state))
        self.assertNotIn("fictional-token", json.dumps(state))
        self.assertNotIn("fictional-warning-token", json.dumps(state))
        self.assertNotIn("fictional-session-value", json.dumps(state))
        self.assertFalse(report["source_modified"])
        self.assertFalse(report["production_ready"])
        self.assertTrue(report["no_mdrun"])

    def test_cli_refuses_to_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "legacy.json"
            state_out = root / "state.json"
            report_out = root / "report.json"
            source.write_text(json.dumps({"schema_version": 6}) + "\n")
            state_out.write_text("preserve-me\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "migrate_v1_state.py"),
                    str(source),
                    "--state-out",
                    str(state_out),
                    "--report-out",
                    str(report_out),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertEqual(state_out.read_text(), "preserve-me\n")
            self.assertFalse(report_out.exists())
            self.assertIn("refusing to overwrite", result.stderr)

    def test_cli_creates_json_and_markdown_without_modifying_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "legacy.json"
            state_out = root / "state.json"
            report_out = root / "migration.json"
            source_content = json.dumps(
                {
                    "schema_version": 6,
                    "jobid": "1234567890",
                    "warnings": ["token=fictional-sensitive-value"],
                },
                sort_keys=True,
            ) + "\n"
            source.write_text(source_content, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "migrate_v1_state.py"),
                    str(source),
                    "--state-out",
                    str(state_out),
                    "--report-out",
                    str(report_out),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.read_text(encoding="utf-8"), source_content)
            self.assertTrue(state_out.exists())
            self.assertTrue(report_out.exists())
            self.assertTrue(report_out.with_suffix(".md").exists())
            self.assertNotIn(
                "fictional-sensitive-value",
                state_out.read_text(encoding="utf-8"),
            )


class ContractDrivenValidationTests(unittest.TestCase):
    def test_contract_derives_components_and_ligand_charge(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            package = create_download_archive(Path(temp) / "final.tar")
            contract = locked_contract()
            report = validate(package, build_contract=contract)

        self.assertTrue(report["validation_passed"])
        self.assertEqual(report["status"], "Candidate_Package_Validated")
        self.assertTrue(report["package_validated"])
        self.assertFalse(report["strict_grompp_passed"])
        self.assertFalse(report["technical_pass"])
        self.assertEqual(report["build_contract_sha256"], contract["contract_sha256"])
        self.assertEqual(report["expected_ligand_charge"], 1.0)
        self.assertTrue(report["ligand_charge_matches_expected"])
        self.assertEqual(report["missing_required_components"], [])
        self.assertFalse(report["production_ready"])
        self.assertTrue(report["no_mdrun"])

    def test_contract_failure_uses_v21_technical_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            components = dict(COMPONENTS)
            components.pop("SOD")
            package = create_download_archive(
                Path(temp) / "missing-sod.tar", components=components
            )
            report = validate(package, build_contract=locked_contract())

        self.assertFalse(report["validation_passed"])
        self.assertEqual(report["status"], "Technical_Fail")
        self.assertEqual(report["legacy_status"], "Candidate_Validation_Failed")
        self.assertIn("SOD", report["missing_required_components"])

    def test_legacy_invocation_keeps_legacy_failure_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            components = dict(COMPONENTS)
            components.pop("PROI")
            package = create_download_archive(
                Path(temp) / "legacy-failure.tar", components=components
            )
            report = validate(package, expected_components=tuple(COMPONENTS))

        self.assertEqual(report["status"], "Candidate_Validation_Failed")
        self.assertEqual(report["build_contract_sha256"], "")

    def test_empty_contract_expectations_cannot_technically_pass(self) -> None:
        empty_contract = lock_contract(
            {
                "schema_version": "2.1",
                "run_id": "empty-expectations",
                "target_id": "target",
                "builder": "membrane_builder",
                "mode": "test_only",
                "inputs": [],
                "parameters": {},
                "decision_records": [],
                "expected_output": {},
                "production_ready": False,
                "no_mdrun": True,
            }
        )
        with tempfile.TemporaryDirectory() as temp:
            package = create_download_archive(Path(temp) / "final.tar")
            report = validate(package, build_contract=empty_contract)

        self.assertFalse(report["validation_passed"])
        self.assertFalse(report["contract_expectations_complete"])
        self.assertEqual(report["status"], "Technical_Fail")
        self.assertIn(
            "does not declare or derive any expected output components",
            report["contract_expectation_errors"][0],
        )


if __name__ == "__main__":
    unittest.main()

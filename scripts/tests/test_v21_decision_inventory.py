from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.inventory import build_inventory  # noqa: E402
from core.execution_plan import derive_execution_plan  # noqa: E402
from core.schema import SchemaError  # noqa: E402
from scripts.prepare_build_contract import build_contract_draft  # noqa: E402


def membrane_request(has_ligand: bool = False) -> dict:
    return {
        "schema_version": "2.1",
        "run_id": "run-inventory",
        "target_id": "target-inventory",
        "builder": "membrane_builder",
        "mode": "test_only",
        "system": {
            "has_ligand": has_ligand,
            "ligand_identity": "EXAMPLE" if has_ligand else None,
            "ligand_formal_charge": 1 if has_ligand else None,
            "membrane_only": False,
        },
        "inputs": [],
        "experimental_conditions": {
            "temperature_k": 303.15,
            "salt": {"type": "KCl", "concentration_m": 0.12},
        },
        "output_engines": ["gromacs"],
        "allow_temporary_critical_assumptions": False,
    }


class DecisionInventoryTests(unittest.TestCase):
    def test_membrane_request_expands_all_relevant_modules(self) -> None:
        inventory = build_inventory(root=ROOT, run_request=membrane_request())
        self.assertEqual(
            inventory["active_modules"],
            ["pdb_reader", "membrane_builder", "gromacs"],
        )
        ids = {row["parameter_id"] for row in inventory["decisions"]}
        self.assertIn("protein.segmentation", ids)
        self.assertIn("membrane.orientation", ids)
        self.assertIn("membrane.ions.type", ids)
        self.assertIn("membrane.z_length_basis", ids)
        self.assertIn("membrane.xy_length_basis", ids)
        self.assertIn("membrane.lipid_input_mode", ids)
        self.assertIn("membrane.ions.placement_method", ids)
        self.assertIn("membrane.ions.neutralize", ids)
        self.assertIn("output.gromacs_enabled", ids)
        self.assertIn("gromacs.pme_fft_grid", ids)
        self.assertIn("gromacs.surface_tension", ids)
        self.assertIn("gromacs.pressure_coupling", ids)

    def test_rule_packs_cover_representative_page_controls(self) -> None:
        inventory = build_inventory(root=ROOT, run_request=membrane_request(True))
        ids = {row["parameter_id"] for row in inventory["decisions"]}
        required = {
            "pdb.correction_mode",
            "protein.missing_residue_autofill",
            "ligand.residue_name",
            "ligand.bond_orders_verified",
            "ligand.stereochemistry_verified",
            "ligand.custom_parameter_submission",
            "membrane.leaflet_symmetry",
            "membrane.ions.visible_hidden_consistent",
            "forcefield.ligand",
            "input_generation.more_charmm_minimization",
            "input_generation.wyf_cation_pi",
            "output.other_engines_disabled",
        }
        self.assertTrue(required <= ids)
        for row in inventory["decisions"]:
            self.assertTrue(row["recommendation_reason"])
            self.assertIn(row["risk_level"], {"Routine", "Contextual", "Critical"})

    def test_experimental_salt_wins_but_conflict_becomes_critical(self) -> None:
        inventory = build_inventory(root=ROOT, run_request=membrane_request())
        decision = next(
            row
            for row in inventory["decisions"]
            if row["parameter_id"] == "membrane.ions.type"
        )
        self.assertEqual(decision["recommended_value"], "KCl")
        self.assertEqual(decision["risk_level"], "Critical")
        self.assertTrue(decision["material_conflict"])

    def test_high_cgenff_penalty_adds_production_blocker_decision(self) -> None:
        request = membrane_request(has_ligand=True)
        audit = {
            "ligand": {
                "identity": "EXAMPLE",
                "formal_charge": 1,
                "protonation": "+1 reviewed assumption",
                "parameter_source": "automatic_cgenff_test_only",
                "cgenff": {"param_penalty": 77.0},
            },
            "protein": {"segmentation_recommendation": "reviewed_segments"},
            "key_ions": {"recommendation": "expert_review"},
        }
        inventory = build_inventory(
            root=ROOT, run_request=request, input_audit=audit
        )
        decision = next(
            row
            for row in inventory["decisions"]
            if row["parameter_id"] == "ligand.cgenff_penalty_approval"
        )
        self.assertEqual(decision["risk_level"], "Critical")
        self.assertFalse(decision["recommended_value"])
        self.assertIn(
            "ligand.cgenff_penalty_approval", inventory["pending_decisions"]
        )

    def test_test_only_temporary_assumptions_do_not_bypass_identity(self) -> None:
        request = membrane_request(has_ligand=True)
        request["system"]["ligand_identity"] = None
        request["allow_temporary_critical_assumptions"] = True
        inventory = build_inventory(root=ROOT, run_request=request)
        self.assertIn("ligand.chemical_identity", inventory["pending_decisions"])
        self.assertNotIn(
            "ligand.chemical_identity", inventory["temporary_assumptions"]
        )

    def test_answers_can_make_draft_ready_without_production_approval(self) -> None:
        request = membrane_request()
        first = build_inventory(root=ROOT, run_request=request)
        answers = {}
        for row in first["decisions"]:
            if row["parameter_id"] not in first["pending_decisions"]:
                continue
            value = row["recommended_value"]
            if value is None and row["available_options"]:
                value = row["available_options"][0]
            if value is None and row["value_type"] == "number":
                value = 120.0
            if value is None and row["value_type"] == "integer":
                value = 1
            if value is None and row["value_type"] in {"string", "composition"}:
                value = "reviewed_value"
            answers[row["parameter_id"]] = value
        inventory = build_inventory(root=ROOT, run_request=request, answers=answers)
        self.assertTrue(inventory["ready_to_lock"])
        draft = build_contract_draft(request, inventory)
        self.assertEqual(len(draft["decision_records"]), len(inventory["decisions"]))
        self.assertFalse(draft["production_ready"])
        self.assertTrue(draft["no_mdrun"])

    def test_invalid_enum_answer_is_rejected(self) -> None:
        with self.assertRaises(SchemaError):
            build_inventory(
                root=ROOT,
                run_request=membrane_request(),
                answers={"membrane.ions.type": "unsupported-salt"},
            )

    def test_pending_decisions_include_guided_questions(self) -> None:
        inventory = build_inventory(root=ROOT, run_request=membrane_request())
        question_ids = {
            question["parameter_id"] for question in inventory["guided_questions"]
        }
        self.assertEqual(question_ids, set(inventory["pending_decisions"]))
        self.assertEqual(
            inventory["next_guided_question"]["parameter_id"],
            inventory["pending_decisions"][0],
        )

    def test_builder_route_and_maturity_are_registry_derived(self) -> None:
        request = membrane_request()
        inventory = build_inventory(root=ROOT, run_request=request)
        plan = derive_execution_plan(
            ROOT,
            builder=request["builder"],
            active_modules=inventory["active_modules"],
        )
        self.assertEqual(plan["capability_id"], "browser.membrane_builder")
        self.assertEqual(plan["execution_route"], "audited_browser")
        self.assertEqual(plan["route_maturity"], "Browser-Assisted")
        self.assertEqual(plan["module_maturity"]["gromacs"], "Beta")

    def test_quick_bilayer_uses_only_registered_official_api_route(self) -> None:
        request = membrane_request()
        request["builder"] = "quick_bilayer"
        inventory = build_inventory(root=ROOT, run_request=request)
        plan = derive_execution_plan(
            ROOT,
            builder=request["builder"],
            active_modules=inventory["active_modules"],
        )
        self.assertEqual(plan["capability_id"], "api.quick_bilayer")
        self.assertEqual(plan["execution_route"], "official_api")
        self.assertEqual(plan["route_maturity"], "Beta")

    def test_membrane_only_quick_bilayer_skips_pdb_reader_rules(self) -> None:
        request = membrane_request()
        request["builder"] = "quick_bilayer"
        request["system"]["membrane_only"] = True
        inventory = build_inventory(root=ROOT, run_request=request)
        self.assertEqual(inventory["active_modules"], ["quick_bilayer", "gromacs"])
        ids = {row["parameter_id"] for row in inventory["decisions"]}
        self.assertNotIn("protein.segmentation", ids)
        self.assertNotIn("quick_bilayer.source_pdbreader_jobid", ids)


if __name__ == "__main__":
    unittest.main()

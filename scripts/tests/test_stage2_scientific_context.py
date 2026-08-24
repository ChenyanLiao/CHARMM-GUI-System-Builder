from __future__ import annotations

import unittest

from core.contracts import lock_contract
from core.scientific_context import build_scientific_context_report


def contract(*, mode: str = "test_only", required: bool = True) -> dict:
    return lock_contract(
        {
            "run_id": "synthetic-environment",
            "pipeline_id": "synthetic-environment",
            "branch_id": "main",
            "target_id": "synthetic-target",
            "builder": "membrane_builder",
            "mode": mode,
            "inputs": [],
            "parameters": {},
            "decision_records": [],
            "structural_environment": {"required": required},
            "pose_preservation": {"required": required},
            "restraint_handoff": {"required": required},
            "production_ready": False,
            "no_mdrun": True,
        }
    )


def passing_pose() -> dict:
    return {
        "transitions": [
            {
                "transition_id": "raw_to_cleaned",
                "alignment_scope": "protein",
                "rigid_transform_applied": True,
                "system_translation_angstrom": 100.0,
                "mapping_coverage": 1.0,
                "minimum_mapping_coverage": 1.0,
                "internal_rmsd_angstrom": 0.1,
                "maximum_internal_rmsd_angstrom": 0.5,
                "pose_rmsd_angstrom": 0.2,
                "maximum_pose_rmsd_angstrom": 1.0,
                "com_shift_angstrom": 0.1,
                "maximum_com_shift_angstrom": 1.0,
            }
        ]
    }


def passing_restraints() -> dict:
    return {
        "restraint_files": ["posre_lig.itp"],
        "referenced_macros": ["POSRES_LIG"],
        "defined_macros": ["POSRES_LIG"],
        "equilibration_schedule": [{"stage": 1, "force": 10.0}],
        "expected_production_define": "",
        "ligand_heavy_atom_restraints": [{"stage": 1, "enabled": True}],
        "downstream_release_validation_required": True,
    }


class Stage2ScientificContextTests(unittest.TestCase):
    def test_retained_structure_resolved_lipid_preserves_parity(self) -> None:
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={
                "components": [
                    {
                        "component_id": "LIP:A:1",
                        "classification": "structure_resolved_lipid",
                        "disposition": "retain",
                        "direct_context": {"contacts_ligand": True},
                    }
                ]
            },
            pose_preservation=passing_pose(),
            restraint_handoff=passing_restraints(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["structural_environment"]["status"], "PRESERVED")
        self.assertTrue(report["structural_environment"]["environmental_equivalence"])

    def test_direct_contact_removal_is_candidate_only_and_requires_sensitivity(self) -> None:
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={
                "components": [
                    {
                        "component_id": "LIP:A:1",
                        "classification": "structure_resolved_lipid",
                        "disposition": "remove",
                        "direct_context": {"contacts_ligand": True},
                        "rationale": "Synthetic incomplete lipid fixture.",
                        "approval_scope": "Candidate_Not_For_MD",
                        "downstream_sensitivity_branch": "retain-structural-lipid",
                    }
                ]
            },
            pose_preservation=passing_pose(),
            restraint_handoff=passing_restraints(),
        )
        environment = report["structural_environment"]
        self.assertTrue(report["passed"])
        self.assertEqual(environment["status"], "ALTERED_APPROVED_CANDIDATE")
        self.assertFalse(environment["environmental_equivalence"])
        self.assertTrue(environment["downstream_sensitivity_required"])

    def test_irrelevant_bulk_component_removal_does_not_claim_environment_change(self) -> None:
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={
                "components": [
                    {
                        "component_id": "SOL:A:1",
                        "classification": "bulk_membrane_component",
                        "disposition": "remove",
                        "direct_context": {},
                    }
                ]
            },
            pose_preservation=passing_pose(),
            restraint_handoff=passing_restraints(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["structural_environment"]["status"], "PRESERVED")

    def test_direct_contact_removal_cannot_silently_pass_production_mode(self) -> None:
        report = build_scientific_context_report(
            contract=contract(mode="production"),
            structural_environment={
                "components": [
                    {
                        "component_id": "LIP:A:1",
                        "classification": "structure_resolved_lipid",
                        "disposition": "remove",
                        "direct_context": {"contacts_ligand": True},
                        "rationale": "Synthetic fixture.",
                        "approval_scope": "expert",
                        "downstream_sensitivity_branch": "retain-structural-lipid",
                    }
                ]
            },
            pose_preservation=passing_pose(),
            restraint_handoff=passing_restraints(),
        )
        self.assertFalse(report["passed"])
        self.assertEqual(
            report["structural_environment"]["status"], "UNRESOLVED_BLOCKING"
        )

    def test_relative_pose_displacement_fails_even_when_internal_geometry_passes(self) -> None:
        pose = passing_pose()
        pose["transitions"][0]["pose_rmsd_angstrom"] = 2.0
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={"components": []},
            pose_preservation=pose,
            restraint_handoff=passing_restraints(),
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["pose_preservation"]["status"], "FAIL")

    def test_rigid_system_transform_does_not_count_as_relative_pose_displacement(self) -> None:
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={"components": []},
            pose_preservation=passing_pose(),
            restraint_handoff=passing_restraints(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["pose_preservation"]["status"], "PASS")

    def test_missing_pose_metric_cannot_default_to_pass(self) -> None:
        pose = passing_pose()
        del pose["transitions"][0]["maximum_pose_rmsd_angstrom"]
        with self.assertRaisesRegex(ValueError, "missing metrics"):
            build_scientific_context_report(
                contract=contract(),
                structural_environment={"components": []},
                pose_preservation=pose,
                restraint_handoff=passing_restraints(),
            )

    def test_undefined_restraint_macro_fails_closed(self) -> None:
        restraints = passing_restraints()
        restraints["defined_macros"] = []
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={"components": []},
            pose_preservation=passing_pose(),
            restraint_handoff=restraints,
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["restraint_handoff"]["status"], "FAIL")
        self.assertFalse(report["restraint_handoff"]["stage2_mdrun_performed"])

    def test_ligand_restraint_release_requires_downstream_validation(self) -> None:
        restraints = passing_restraints()
        restraints["downstream_release_validation_required"] = False
        report = build_scientific_context_report(
            contract=contract(),
            structural_environment={"components": []},
            pose_preservation=passing_pose(),
            restraint_handoff=restraints,
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["restraint_handoff"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()

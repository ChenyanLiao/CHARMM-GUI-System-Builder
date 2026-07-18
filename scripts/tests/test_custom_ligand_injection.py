#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(SCRIPTS))

from fixture_factory import create_custom_case  # noqa: E402
from verify_custom_ligand_injection import verify  # noqa: E402


class CustomLigandInjectionTests(unittest.TestCase):
    def test_rtf_prm_without_str_passes_46_5_and_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frozen_dir, package = create_custom_case(Path(tmp))
            report = verify(frozen_dir, package)
        self.assertTrue(report["custom_parameter_injection_verified"])
        self.assertEqual(report["package_layout"], "lig.rtf_plus_lig.prm")
        self.assertFalse(report["lig_str_present"])
        self.assertFalse(report["lig_str_absent_is_blocking"])
        self.assertEqual(report["changed_definition_prm_matched"], 46)
        self.assertEqual(report["changed_definition_forcefield_matched"], 46)
        self.assertEqual(report["primary_target_forcefield_matched"], 5)
        self.assertEqual(report["target_connectivity_matched"], 3)
        self.assertEqual(report["status"], "Technical_Pass_Not_Production_Approval")
        self.assertFalse(report["production_ready"])
        self.assertTrue(report["no_mdrun"])

    def test_standalone_str_layout_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frozen_dir, package = create_custom_case(Path(tmp), standalone_str=True)
            report = verify(frozen_dir, package)
        self.assertTrue(report["custom_parameter_injection_verified"])
        self.assertEqual(report["package_layout"], "standalone_lig.str")
        self.assertTrue(report["lig_str_present"])

    def test_missing_one_forcefield_dihedraltype_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frozen_dir, package = create_custom_case(
                Path(tmp), missing_forcefield_term_index=17
            )
            report = verify(frozen_dir, package)
        self.assertFalse(report["custom_parameter_injection_verified"])
        self.assertEqual(report["changed_definition_prm_matched"], 46)
        self.assertEqual(report["changed_definition_forcefield_matched"], 45)
        self.assertEqual(report["status"], "Candidate_Validation_Failed")

    def test_missing_target_function9_connection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frozen_dir, package = create_custom_case(Path(tmp), omit_connection=True)
            report = verify(frozen_dir, package)
        self.assertFalse(report["custom_parameter_injection_verified"])
        self.assertEqual(report["target_connectivity_matched"], 2)


if __name__ == "__main__":
    unittest.main()

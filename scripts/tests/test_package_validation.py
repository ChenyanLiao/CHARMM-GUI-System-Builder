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

from fixture_factory import COMPONENTS, create_download_archive  # noqa: E402
from validate_charmmgui_package import validate  # noqa: E402


class PackageValidationTests(unittest.TestCase):
    def test_nine_segment_profile_passes_as_technical_not_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = create_download_archive(Path(tmp) / "final.tar")
            report = validate(
                package,
                require_ligand=True,
                expected_ligand_charge=1.0,
                expected_components=tuple(COMPONENTS),
            )
        self.assertTrue(report["validation_passed"])
        self.assertEqual(report["status"], "Technical_Pass_Not_Production_Approval")
        self.assertEqual(report["missing_required_components"], [])
        self.assertFalse(report["production_ready"])
        self.assertTrue(report["no_mdrun"])

    def test_abnormal_termination_cannot_pass_as_normal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = create_download_archive(
                Path(tmp) / "final.tar", step5_text="ABNORMAL TERMINATION\n"
            )
            report = validate(package, require_ligand=True)
        self.assertFalse(report["step5_input_normal_termination"])
        self.assertTrue(report["step5_input_abnormal_termination"])
        self.assertFalse(report["validation_passed"])

    def test_missing_segment_fails_required_component_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            components = dict(COMPONENTS)
            components.pop("PROI")
            package = create_download_archive(
                Path(tmp) / "final.tar", components=components
            )
            report = validate(package, expected_components=tuple(COMPONENTS))
        self.assertIn("PROI", report["missing_required_components"])
        self.assertFalse(report["validation_passed"])


if __name__ == "__main__":
    unittest.main()

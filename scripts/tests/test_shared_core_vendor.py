from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.shared import activate_vendor, verify_vendor_integrity  # noqa: E402


class SharedCoreVendorTests(unittest.TestCase):
    def test_vendor_manifest_and_import(self) -> None:
        report = verify_vendor_integrity()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["package_version"], "1.0.0")
        activate_vendor()
        from simulation_stage_contracts.version import __version__

        self.assertEqual(__version__, "1.0.0")


if __name__ == "__main__":
    unittest.main()

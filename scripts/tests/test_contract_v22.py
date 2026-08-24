from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.contracts import lock_contract  # noqa: E402
from scripts.prepare_build_contract import build_contract_draft  # noqa: E402


class ContractV22Tests(unittest.TestCase):
    def test_new_draft_and_lock_use_v22(self) -> None:
        request = {"run_id": "synthetic-pipeline", "target_id": "synthetic", "builder": "membrane_builder", "mode": "test_only", "inputs": []}
        inventory = {"pending_decisions": [], "temporary_assumptions": [], "decisions": [], "contract_parameters": {}, "active_modules": []}
        draft = build_contract_draft(request, inventory)
        self.assertEqual(draft["schema_version"], "2.2")
        self.assertEqual(draft["record_type"], "approved-build-contract")
        self.assertEqual(lock_contract(draft)["schema_version"], "2.2")

    def test_v21_migration_is_non_destructive_and_requires_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "legacy.json"
            original = {"schema_version": "2.1", "run_id": "legacy"}
            source.write_text(json.dumps(original), encoding="utf-8")
            output = root / "migration.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate_build_contract_v21.py"), str(source), "--pipeline-id", "synthetic", "--branch-id", "main", "--out", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            migrated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), original)
            self.assertEqual(migrated["record"]["schema_version"], "2.2")
            self.assertTrue(migrated["lock_required"])


if __name__ == "__main__":
    unittest.main()

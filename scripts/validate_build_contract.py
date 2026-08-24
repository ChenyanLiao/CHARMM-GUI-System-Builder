#!/usr/bin/env python3
"""Validate one Stage 2 build contract without modifying it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.contracts import validate_contract  # noqa: E402
from core.io import load_structured  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--pipeline-id")
    parser.add_argument("--branch-id")
    args = parser.parse_args()
    result = {
        "command": "validate-build-contract",
        "success": False,
        "contract_state": "INVALID",
        "errors": [],
        "side_effects_performed": False,
        "production_ready": False,
        "no_mdrun": True,
    }
    try:
        contract = load_structured(args.contract)
        version = str(contract.get("schema_version", ""))
        if version == "2.1":
            result["contract_state"] = "LEGACY_READ_ONLY"
        else:
            validate_contract(contract, require_locked=True)
            if args.pipeline_id and contract.get("pipeline_id") != args.pipeline_id:
                raise ValueError("contract pipeline_id does not match the selected branch")
            if args.branch_id and contract.get("branch_id") != args.branch_id:
                raise ValueError("contract branch_id does not match the selected branch")
            result.update(
                {
                    "success": True,
                    "contract_state": "LOCKED",
                    "pipeline_id": contract["pipeline_id"],
                    "branch_id": contract["branch_id"],
                    "revision": contract["revision"],
                    "contract_sha256": contract["contract_sha256"],
                }
            )
    except Exception as exc:
        result["errors"].append(
            {"code": getattr(exc, "code", "E_SCHEMA_INVALID"), "message": str(exc)}
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

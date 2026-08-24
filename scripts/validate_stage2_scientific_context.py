#!/usr/bin/env python3
"""Validate structural-environment, pose, and restraint evidence without MD."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.contracts import validate_contract  # noqa: E402
from core.io import load_structured, write_json  # noqa: E402
from core.scientific_context import build_scientific_context_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--structural-ledger", type=Path)
    parser.add_argument("--pose-report", type=Path)
    parser.add_argument("--restraint-report", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        print(json.dumps({"success": False, "message": "output already exists"}))
        return 2
    try:
        contract = load_structured(args.contract)
        validate_contract(contract, require_locked=True)
        report = build_scientific_context_report(
            contract=contract,
            structural_environment=(
                load_structured(args.structural_ledger) if args.structural_ledger else None
            ),
            pose_preservation=load_structured(args.pose_report) if args.pose_report else None,
            restraint_handoff=(
                load_structured(args.restraint_report) if args.restraint_report else None
            ),
        )
        write_json(args.out, report)
        print(
            json.dumps(
                {
                    "success": report["passed"],
                    "output": str(args.out.resolve()),
                    "production_ready": False,
                    "md_execution_allowed": False,
                    "no_mdrun": True,
                }
            )
        )
        return 0 if report["passed"] else 2
    except Exception as exc:
        print(
            json.dumps(
                {"success": False, "error": type(exc).__name__, "message": str(exc)}
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

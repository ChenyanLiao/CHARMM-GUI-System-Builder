#!/usr/bin/env python3
"""Create a reviewable v2.2 contract draft from an unchanged v2.1 contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.contracts import diff_contracts  # noqa: E402
from core.io import load_structured, write_json  # noqa: E402
from core.shared import activate_vendor  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--pipeline-id", required=True)
    parser.add_argument("--branch-id", required=True)
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        print("error: migration output already exists", file=sys.stderr)
        return 2
    try:
        source = load_structured(args.source)
        activate_vendor()
        from simulation_stage_contracts.migrations import migrate_contract_v21

        result = migrate_contract_v21(source, args.pipeline_id, args.branch_id, args.revision)
        result["diff"] = diff_contracts(source, result["record"])
        result["lock_required"] = True
        result["production_ready"] = False
        result["no_mdrun"] = True
        write_json(args.out, result)
        print(json.dumps({"success": True, "output": str(args.out.resolve()), "lock_required": True}))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

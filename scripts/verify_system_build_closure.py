#!/usr/bin/env python3
"""Replay a Stage 2 technical closure without issuing a receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.closure import verify_closure_record  # noqa: E402
from core.io import load_structured  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("closure", type=Path)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--evidence-index", type=Path, required=True)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    try:
        result = verify_closure_record(
            closure_path=args.closure.expanduser().resolve(),
            closure=load_structured(args.closure),
            contract_path=args.contract.expanduser().resolve(),
            contract=load_structured(args.contract),
            handoff_path=args.handoff.expanduser().resolve(),
            handoff=load_structured(args.handoff),
            evidence_index=load_structured(args.evidence_index),
            package_path=args.package,
        )
    except Exception as exc:
        result = {
            "command": "verify-system-build-closure",
            "success": False,
            "artifact_state": "INVALID",
            "closure_state": "BLOCKED",
            "evidence_freshness": "UNKNOWN",
            "errors": [
                {"code": getattr(exc, "code", "E_SCHEMA_INVALID"), "message": str(exc)}
            ],
            "side_effects_performed": False,
            "production_ready": False,
            "no_mdrun": True,
        }
    else:
        result["command"] = "verify-system-build-closure"
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

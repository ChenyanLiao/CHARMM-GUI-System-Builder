#!/usr/bin/env python3
"""Verify a current Stage 2 Receipt 2.0 and its supersession chain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.io import load_structured  # noqa: E402
from core.shared import activate_vendor  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--chain", type=Path, required=True)
    parser.add_argument("--evidence-index", type=Path)
    args = parser.parse_args()
    try:
        activate_vendor()
        from simulation_stage_contracts.receipts import verify_receipt

        result = verify_receipt(args.receipt, args.chain, load_structured(args.evidence_index) if args.evidence_index else None)
        print(json.dumps({"success": True, **result}))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

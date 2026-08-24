#!/usr/bin/env python3
"""Explicitly lock an audited Stage 2 closure as an immutable Receipt 2.0."""

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
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--chain", type=Path, required=True)
    parser.add_argument("--supersession-reason")
    args = parser.parse_args()
    try:
        audit_record = load_structured(args.audit)
        if audit_record.get("audit", {}).get("passed") is not True:
            raise ValueError("closure audit is not passing")
        activate_vendor()
        from simulation_stage_contracts.receipts import lock_receipt

        receipt = lock_receipt(args.receipt, args.chain, audit_record["payload"], args.supersession_reason)
        print(json.dumps({"success": True, "receipt": str(args.receipt.resolve()), "receipt_sha256": receipt["receipt_sha256"], "production_ready": False, "md_execution_allowed": False, "no_mdrun": True}))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read evidence, build a receipt candidate, and write a non-authoritative audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.closure import build_closure_payload  # noqa: E402
from core.io import load_structured, write_json  # noqa: E402
from core.shared import activate_vendor  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "handoff", "package_report", "evidence_index", "semantic_topology", "segment_matrix", "preprocessing", "tpr_readback"):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    parser.add_argument("--parameter-injection", type=Path)
    parser.add_argument("--scientific-context", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        print("error: audit output already exists", file=sys.stderr)
        return 2
    activate_vendor()
    from simulation_stage_contracts.receipts import audit_receipt_payload

    try:
        contract = load_structured(args.contract)
        handoff = load_structured(args.handoff)
        payload = build_closure_payload(
            contract_path=args.contract,
            contract=contract,
            handoff_path=args.handoff,
            handoff=handoff,
            package_report=load_structured(args.package_report),
            evidence_index=load_structured(args.evidence_index),
            semantic_topology=load_structured(args.semantic_topology),
            segment_matrix=load_structured(args.segment_matrix),
            preprocessing=load_structured(args.preprocessing),
            tpr_readback=load_structured(args.tpr_readback),
            parameter_injection=load_structured(args.parameter_injection) if args.parameter_injection else None,
            scientific_context=load_structured(args.scientific_context) if args.scientific_context else None,
        )
        audit = audit_receipt_payload(payload)
        write_json(args.out, {"record_type": "system-build-closure-draft", "schema_version": "1.0", "payload": payload, "audit": audit})
        print(json.dumps({"success": audit["passed"], "status": audit["status"], "output": str(args.out.resolve())}))
        return 0 if audit["passed"] else 2
    except Exception as exc:
        print(json.dumps({"success": False, "error": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Prepare a v2.1 parameter review and build-contract draft without submitting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.contracts import lock_contract  # noqa: E402
from core.execution_plan import derive_execution_plan  # noqa: E402
from core.inventory import build_inventory  # noqa: E402
from core.io import load_structured, write_json  # noqa: E402
from core.schema import SCHEMA_VERSION, SchemaError, assert_no_secret_fields  # noqa: E402


def build_contract_draft(
    run_request: dict,
    inventory: dict,
    execution_plan: dict | None = None,
) -> dict:
    execution_plan = execution_plan or {}
    blockers = [
        {
            "parameter_id": parameter_id,
            "reason": "Decision requires confirmation before contract lock.",
        }
        for parameter_id in inventory["pending_decisions"]
    ]
    blockers.extend(
        {
            "parameter_id": parameter_id,
            "reason": "Critical temporary assumption keeps production blocked.",
        }
        for parameter_id in inventory["temporary_assumptions"]
    )
    blockers.extend(
        {
            "parameter_id": decision["parameter_id"],
            "reason": "Explicit approval remains false.",
        }
        for decision in inventory["decisions"]
        if decision["parameter_id"].endswith("_approval")
        and decision.get("contract_value") is False
    )
    draft = {
        "schema_version": SCHEMA_VERSION,
        "contract_state": "draft",
        "revision": 1,
        "run_id": run_request.get("run_id", ""),
        "target_id": run_request.get("target_id", ""),
        "builder": run_request.get("builder", ""),
        "mode": run_request.get("mode", "dry_run"),
        "inputs": run_request.get("inputs", []),
        "parameters": inventory["contract_parameters"],
        "decision_records": inventory["decisions"],
        "active_modules": inventory["active_modules"],
        "temporary_assumptions": inventory["temporary_assumptions"],
        "production_blockers": blockers,
        "capability_id": execution_plan.get("capability_id", ""),
        "execution_route": execution_plan.get("execution_route", ""),
        "route_maturity": execution_plan.get("route_maturity", ""),
        "module_maturity": execution_plan.get("module_maturity", {}),
        "expected_output": run_request.get("expected_output", {}),
        "credential_provider_ref": run_request.get("credential_provider_ref", ""),
        "production_ready": False,
        "no_mdrun": True,
    }
    assert_no_secret_fields(draft)
    return draft


def write_markdown(inventory: dict, draft: dict, path: Path) -> None:
    lines = [
        "# CHARMM-GUI v2.1 Build Contract Review",
        "",
        f"- Run ID: `{draft['run_id']}`",
        f"- Target: `{draft['target_id']}`",
        f"- Builder: `{draft['builder']}`",
        f"- Mode: `{draft['mode']}`",
        f"- Capability: `{draft['capability_id']}`",
        f"- Route / maturity: `{draft['execution_route']}` / `{draft['route_maturity']}`",
        f"- Ready to lock: {inventory['ready_to_lock']}",
        "- Production-ready: false",
        "- gmx mdrun allowed: false",
        "",
        "## Decisions",
        "",
        "| Parameter | Risk | Recommended | Contract value | Status |",
        "|---|---|---|---|---|",
    ]
    for decision in inventory["decisions"]:
        status = "PENDING" if decision["parameter_id"] in inventory["pending_decisions"] else "RECORDED"
        lines.append(
            "| {parameter_id} | {risk_level} | `{recommended}` | `{contract}` | {status} |".format(
                parameter_id=decision["parameter_id"],
                risk_level=decision["risk_level"],
                recommended=decision["recommended_value"],
                contract=decision["contract_value"],
                status=status,
            )
        )
    lines.extend(["", "## Decision Details", ""])
    for decision in inventory["decisions"]:
        parameter_id = decision["parameter_id"]
        status = "PENDING" if parameter_id in inventory["pending_decisions"] else "RECORDED"
        lines.extend(
            [
                f"### `{parameter_id}`",
                "",
                f"- Module / step: `{decision['module']}` / `{decision['page_or_step']}`",
                f"- Risk: `{decision['risk_level']}`",
                f"- Status: `{status}`",
                f"- Available options: `{decision['available_options']}`",
                f"- Recommended: `{decision['recommended_value']}`",
                f"- Contract value: `{decision['contract_value']}`",
                f"- Confidence: `{decision['confidence']}`",
                f"- Reason: {decision['recommendation_reason']}",
                f"- Material conflict: {decision['material_conflict']}",
            ]
        )
        for evidence in decision["evidence_sources"]:
            lines.append(
                "- Evidence: `{source}` -> `{value}` ({confidence}); `{citation}`".format(
                    source=evidence["source"],
                    value=evidence["value"],
                    confidence=evidence["confidence"],
                    citation=evidence["citation"],
                )
            )
        lines.append("")
    if inventory["temporary_assumptions"]:
        lines.extend(
            ["", "## Temporary Assumptions", ""]
            + [f"- `{item}`" for item in inventory["temporary_assumptions"]]
        )
    if inventory["pending_decisions"]:
        lines.extend(
            ["", "## Pending Decisions", ""]
            + [f"- `{item}`" for item in inventory["pending_decisions"]]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_request", type=Path)
    parser.add_argument("--target-profile", type=Path)
    parser.add_argument("--input-audit", type=Path)
    parser.add_argument("--answers", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--lock-if-ready", action="store_true")
    args = parser.parse_args()
    try:
        run_request = load_structured(args.run_request)
        inventory = build_inventory(
            root=ROOT,
            run_request=run_request,
            target_profile=(load_structured(args.target_profile) if args.target_profile else None),
            input_audit=(load_structured(args.input_audit) if args.input_audit else None),
            answers=(load_structured(args.answers) if args.answers else None),
        )
        execution_plan = derive_execution_plan(
            ROOT,
            builder=str(run_request.get("builder", "")),
            active_modules=inventory["active_modules"],
        )
        draft = build_contract_draft(run_request, inventory, execution_plan)
        args.outdir.mkdir(parents=True, exist_ok=True)
        write_json(args.outdir / "DECISION_REGISTER.json", inventory)
        write_json(args.outdir / "APPROVED_BUILD_CONTRACT_DRAFT.json", draft)
        write_markdown(inventory, draft, args.outdir / "BUILD_CONTRACT_REVIEW.md")
        if args.lock_if_ready:
            if not inventory["ready_to_lock"]:
                raise SchemaError("contract has pending decisions and cannot be locked")
            write_json(args.outdir / "APPROVED_BUILD_CONTRACT.json", lock_contract(draft))
        print(args.outdir.resolve())
        return 0
    except (SchemaError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

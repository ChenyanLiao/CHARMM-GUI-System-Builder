#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Create a non-destructive v2.1 copy of a legacy CHARMM-GUI run state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.evidence import redact  # noqa: E402
from core.io import load_structured, write_json_atomic  # noqa: E402
from core.schema import SCHEMA_VERSION, SchemaError, assert_no_secret_fields  # noqa: E402


def _runtime_state(old: dict[str, Any]) -> str:
    if old.get("workflow_complete"):
        return "technical_pass"
    if old.get("fatal_errors") or old.get("backend_state") == "fatal":
        return "technical_fail"
    if str(old.get("backend_state", "")).startswith("complete"):
        return "backend_done"
    if old.get("running") or old.get("backend_state") == "running":
        return "running"
    if old.get("needs_user_attention"):
        return "waiting_user_or_authorized_action"
    return "prepared"


def migrate_state(old: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    sanitized = redact(old)
    assert_no_secret_fields(sanitized)
    state = {
        "schema_version": SCHEMA_VERSION,
        "legacy_schema_version": sanitized.get("schema_version"),
        "run_id": sanitized.get("run_id", ""),
        "mode": sanitized.get("mode", "Candidate_Not_For_MD"),
        "contract_sha256": "",
        "jobid": sanitized.get("jobid", ""),
        "project": sanitized.get("project", ""),
        "current_step": sanitized.get("current_step", ""),
        "runtime_state": _runtime_state(old),
        "submission_state": "submitted" if old.get("jobid") else "not_submitted",
        "submissions_used": 1 if old.get("jobid") else 0,
        "max_submissions": 1,
        "auth_state": sanitized.get("auth_state", "unknown"),
        "browser_state": sanitized.get("browser_state", "unknown"),
        "page_state": sanitized.get("page_state", "unknown"),
        "backend_state": sanitized.get("backend_state", "unknown"),
        "download_state": sanitized.get("download_state", "not_requested"),
        "next_allowed_action": sanitized.get("next_allowed_action", ""),
        "required_products": sanitized.get("required_products", []),
        "closure_gates": sanitized.get("closure_gates", {}),
        "warnings": sanitized.get("warnings", []),
        "fatal_errors": sanitized.get("fatal_errors", []),
        "production_ready": False,
        "no_mdrun": True,
        "legacy_state": sanitized,
    }
    unknown = [
        "contract_sha256",
        "approved parameter decisions",
        "staged approval evidence",
        "execution authorization",
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "source_schema_version": sanitized.get("schema_version"),
        "source_modified": False,
        "mapped_fields": sorted(key for key in state if key != "legacy_state"),
        "unknown_or_not_captured": unknown,
        "critical_reconfirmation_required": True,
        "production_ready": False,
        "no_mdrun": True,
    }
    assert_no_secret_fields(state)
    assert_no_secret_fields(report)
    return state, report


def write_migration_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# CHARMM-GUI State Migration Report",
        "",
        f"- Target schema: `{report['schema_version']}`",
        f"- Source schema: `{report['source_schema_version']}`",
        f"- Source modified: {report['source_modified']}",
        f"- Critical reconfirmation required: {report['critical_reconfirmation_required']}",
        "- Production-ready: false",
        "- gmx mdrun allowed: false",
        "",
        "## Unknown Or Not Captured",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unknown_or_not_captured"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--state-out", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    parser.add_argument("--markdown-report-out", type=Path)
    args = parser.parse_args()
    try:
        source = args.source.expanduser().resolve()
        markdown_report = (
            args.markdown_report_out.expanduser().resolve()
            if args.markdown_report_out
            else args.report_out.expanduser().resolve().with_suffix(".md")
        )
        state_out = args.state_out.expanduser().resolve()
        report_out = args.report_out.expanduser().resolve()
        if markdown_report == report_out:
            markdown_report = report_out.with_name(f"{report_out.name}.md")
        destinations = {state_out, report_out, markdown_report}
        if len(destinations) != 3:
            raise SchemaError("migration outputs must be three distinct paths")
        if source in destinations:
            raise SchemaError("migration output cannot overwrite the source")
        if any(path.exists() for path in destinations):
            raise SchemaError("migration output already exists; refusing to overwrite")
        state, report = migrate_state(load_structured(source))
        write_json_atomic(args.state_out, state)
        write_json_atomic(args.report_out, report)
        write_migration_markdown(report, markdown_report)
        print(args.state_out)
        print(args.report_out)
        print(markdown_report)
        return 0
    except (SchemaError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

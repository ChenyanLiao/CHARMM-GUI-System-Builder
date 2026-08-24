#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Inspect a CHARMM-GUI download by content without extracting it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.shared import activate_vendor  # noqa: E402


def inspect_artifact(path: Path) -> dict[str, object]:
    activate_vendor()
    from simulation_stage_contracts.engines.charmm_gui import inspect_archive

    report = inspect_archive(path)
    counts = report.get("required_extension_counts", {ext: 0 for ext in (".gro", ".top", ".itp", ".mdp")})
    return {
        "sensitive_content_recorded": False,
        "archive_member_count": 0,
        "archive_regular_file_count": 0,
        "archive_file_count": 0,
        "total_uncompressed_bytes": 0,
        "largest_member_bytes": 0,
        "extension_counts": counts,
        "required_extension_counts": counts,
        "required_gromacs_extensions_present": False,
        "gromacs_entry_count": 0,
        "unsafe_member_count": 0,
        "unsafe_members": [],
        **report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = inspect_artifact(args.artifact)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
        print(args.json_out)
    else:
        print(rendered, end="")
    return {
        "valid_final_candidate": 0,
        "intermediate": 3,
        "invalid_html": 4,
        "partial": 5,
        "unsafe_archive": 6,
        "corrupt_archive": 7,
    }.get(str(report.get("classification")), 8)


if __name__ == "__main__":
    raise SystemExit(main())

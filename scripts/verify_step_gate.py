#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Verify local CHARMM-GUI step products before permitting the next action."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path


FATAL_MARKERS = (
    "ABNORMAL TERMINATION",
    "Execution terminated due to the detection of a fatal error",
    "MOST SEVERE WARNING WAS AT LEVEL  0",
    "cannot be opened",
)


def load_files(root: Path) -> dict[str, bytes]:
    if root.is_dir():
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*") if path.is_file()
        }
    if not tarfile.is_tarfile(root):
        raise ValueError(f"not a directory or tar archive: {root}")
    out = {}
    with tarfile.open(root, "r:*") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            handle = archive.extractfile(member)
            if handle is not None:
                out[member.name] = handle.read()
    return out


def matches(files: dict[str, bytes], suffix: str) -> list[str]:
    return sorted(name for name in files if name.endswith(suffix))


def text_for(files: dict[str, bytes], suffix: str) -> str:
    names = matches(files, suffix)
    if not names:
        return ""
    return files[names[0]].decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--step",
        required=True,
        choices=("pdb_reader", "orientation", "system_size", "packing", "assembly", "input_generation"),
    )
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()

    files = load_files(args.root)
    required: list[str] = []
    alternatives: list[list[str]] = []
    output_suffix = None
    require_normal = False
    require_gromacs_extensions = False
    if args.step == "pdb_reader":
        required = ["step1_pdbreader.out", "step1_pdbreader.pdb"]
        output_suffix = "step1_pdbreader.out"
        require_normal = True
    elif args.step == "orientation":
        required = ["step2_orient.pdb"]
        alternatives = [["step2_area.str", "step2_protein_area.str"]]
    elif args.step == "system_size":
        required = ["step3_size.str"]
    elif args.step == "packing":
        required = ["step3_packing.out", "step3_packing_head.psf", "step3_packing_head.crd"]
        output_suffix = "step3_packing.out"
    elif args.step == "assembly":
        required = ["step5_assembly.psf", "step5_assembly.crd", "step5_assembly.pdb"]
        alternatives = [["step5_assembly.out", "step5_input.out"]]
        output_suffix = "step5_assembly.out" if matches(files, "step5_assembly.out") else "step5_input.out"
    elif args.step == "input_generation":
        required = ["step5_input.out"]
        output_suffix = "step5_input.out"
        require_normal = True
        require_gromacs_extensions = True

    found = {suffix: matches(files, suffix) for suffix in required}
    missing = [suffix for suffix, names in found.items() if not names]
    alternatives_found = []
    for group in alternatives:
        present = {suffix: matches(files, suffix) for suffix in group}
        alternatives_found.append(present)
        if not any(present.values()):
            missing.append("one_of:" + ",".join(group))

    output_text = text_for(files, output_suffix) if output_suffix else ""
    fatal_markers = [marker for marker in FATAL_MARKERS if marker in output_text]
    normal_termination = "NORMAL TERMINATION" in output_text if output_text else False
    extension_counts = {
        extension: sum(name.endswith(extension) and ("/gromacs/" in name or name.startswith("gromacs/")) for name in files)
        for extension in (".gro", ".top", ".itp", ".mdp")
    }
    gromacs_complete = all(count > 0 for count in extension_counts.values())
    passed = not missing and not fatal_markers
    if require_normal:
        passed = passed and normal_termination
    if require_gromacs_extensions:
        passed = passed and gromacs_complete

    result = {
        "root": str(args.root.resolve()),
        "step": args.step,
        "required_files": found,
        "alternative_files": alternatives_found,
        "missing": missing,
        "output_file": output_suffix,
        "normal_termination": normal_termination,
        "fatal_markers": fatal_markers,
        "gromacs_extension_counts": extension_counts,
        "gromacs_complete": gromacs_complete,
        "gate_passed": passed,
        "next_allowed_action": "ADVANCE_ONCE" if passed else "STOP_AND_REVIEW",
        "production_ready": False,
        "no_mdrun": True,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

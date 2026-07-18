#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Validate a CHARMM-GUI GROMACS archive without modifying or extracting it."""

from __future__ import annotations

import argparse
import json
import math
import re
import tarfile
from pathlib import Path
from typing import Dict, List, Tuple

from inspect_charmmgui_download import inspect_artifact


EXAMPLE_NINE_SEGMENT_COMPONENTS = (
    "PROA", "PROB", "PROC", "PROD", "PROE", "PROF", "PROG", "PROH", "PROI",
    "CAL", "LIG", "CHL1", "POPC", "SOD", "CLA", "TIP3",
)
COMPONENT_PROFILES = {
    "none": (),
    "example-9segment-membrane": EXAMPLE_NINE_SEGMENT_COMPONENTS,
}


def regular_members(package: Path) -> list[tarfile.TarInfo]:
    with tarfile.open(package, "r:*") as archive:
        return [member for member in archive.getmembers() if member.isfile()]


def read_member_text(
    package: Path, suffix: str, max_bytes: int = 250_000_000
) -> Tuple[str | None, str]:
    with tarfile.open(package, "r:*") as archive:
        matches = sorted(
            (
                member for member in archive.getmembers()
                if member.name.endswith(suffix) and member.isfile()
            ),
            key=lambda member: member.name,
        )
        if not matches:
            return None, ""
        member = matches[0]
        if member.size > max_bytes:
            return member.name, ""
        handle = archive.extractfile(member)
        if handle is None:
            return member.name, ""
        return member.name, handle.read().decode("utf-8", errors="replace")


def parse_topol_molecules(text: str) -> Dict[str, int]:
    in_molecules = False
    molecules: Dict[str, int] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("["):
            in_molecules = bool(re.match(r"\[\s*molecules\s*\]", line, re.I))
            continue
        if in_molecules:
            fields = line.split()
            if len(fields) >= 2:
                try:
                    molecules[fields[0]] = int(fields[1])
                except ValueError:
                    continue
    return molecules


def ligand_charge_from_itp(text: str) -> float | None:
    charges: List[float] = []
    in_atoms = False
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            in_atoms = bool(re.match(r"\[\s*atoms\s*\]", line, re.I))
            continue
        if in_atoms:
            fields = line.split()
            if len(fields) >= 7:
                try:
                    charges.append(float(fields[6]))
                except ValueError:
                    continue
    return round(sum(charges), 6) if charges else None


def termination_state(text: str) -> tuple[bool, bool]:
    abnormal = bool(re.search(r"(?m)^\s*ABNORMAL TERMINATION\b", text))
    normal = bool(re.search(r"(?m)^\s*NORMAL TERMINATION\b", text))
    return normal, abnormal


def invalid_report(package: Path, inspection: dict[str, object]) -> Dict[str, object]:
    return {
        "package": str(package),
        "download_inspection": inspection,
        "package_size_bytes": inspection.get("size_bytes"),
        "sha256": inspection.get("sha256"),
        "member_count": 0,
        "member_count_definition": "regular-file tar members only",
        "counts": {"gro": 0, "top": 0, "itp": 0, "mdp": 0, "gromacs_entries": 0},
        "topol_member": None,
        "step5_input_out_member": None,
        "ligand_itp_member": None,
        "molecules": {},
        "known_component_checks": {
            name: False for name in EXAMPLE_NINE_SEGMENT_COMPONENTS
        },
        "required_component_checks": {},
        "missing_required_components": [],
        "ligand_charge": None,
        "ligand_charge_matches_expected": False,
        "step5_input_normal_termination": False,
        "step5_input_abnormal_termination": False,
        "has_required_gromacs_files": False,
        "validation_passed": False,
        "status": "Invalid_Download_Artifact",
        "production_ready": False,
        "no_mdrun": True,
    }


def validate(
    package: Path,
    *,
    require_ligand: bool = False,
    ligand_name: str = "LIG",
    expected_ligand_charge: float | None = None,
    expected_components: tuple[str, ...] = (),
) -> Dict[str, object]:
    package = package.expanduser().resolve()
    inspection = inspect_artifact(package)
    if inspection["classification"] != "valid_final_candidate":
        return invalid_report(package, inspection)

    members = regular_members(package)
    names = [member.name for member in members]
    counts = {
        "gro": sum(name.lower().endswith(".gro") for name in names),
        "top": sum(name.lower().endswith(".top") for name in names),
        "itp": sum(name.lower().endswith(".itp") for name in names),
        "mdp": sum(name.lower().endswith(".mdp") for name in names),
        "gromacs_entries": sum(
            "/gromacs/" in f"/{name.lower().lstrip('/')}" for name in names
        ),
    }
    topol_name, topol_text = read_member_text(package, "gromacs/topol.top")
    if not topol_text:
        topol_name, topol_text = read_member_text(package, "topol.top")
    step5_name, step5_text = read_member_text(package, "step5_input.out")
    ligand_member, ligand_text = read_member_text(
        package, f"gromacs/toppar/{ligand_name}.itp"
    )
    if not ligand_text:
        ligand_member, ligand_text = read_member_text(package, f"{ligand_name}.itp")

    molecules = parse_topol_molecules(topol_text)
    ligand_charge = ligand_charge_from_itp(ligand_text) if ligand_text else None
    normal, abnormal = termination_state(step5_text)
    has_required_files = all(counts[key] > 0 for key in ("gro", "top", "itp", "mdp"))
    ligand_present = bool(ligand_text and molecules.get(ligand_name, 0) > 0)
    ligand_ok = not require_ligand or ligand_present
    if expected_ligand_charge is None:
        charge_ok = ligand_charge is not None if require_ligand else True
    else:
        charge_ok = ligand_charge is not None and math.isclose(
            ligand_charge, expected_ligand_charge, abs_tol=1e-6
        )
    known_checks = {
        name: molecules.get(name, 0) > 0
        for name in EXAMPLE_NINE_SEGMENT_COMPONENTS
    }
    required_checks = {name: molecules.get(name, 0) > 0 for name in expected_components}
    missing_components = [name for name, present in required_checks.items() if not present]
    passed = bool(
        has_required_files
        and topol_text
        and molecules
        and normal
        and not abnormal
        and ligand_ok
        and charge_ok
        and not missing_components
    )
    return {
        "package": str(package),
        "download_inspection": inspection,
        "package_size_bytes": package.stat().st_size,
        "sha256": inspection["sha256"],
        "member_count": len(members),
        "member_count_definition": "regular-file tar members only",
        "counts": counts,
        "topol_member": topol_name,
        "step5_input_out_member": step5_name,
        "ligand_itp_member": ligand_member,
        "molecules": molecules,
        "known_component_checks": known_checks,
        "required_component_checks": required_checks,
        "missing_required_components": missing_components,
        "ligand_name": ligand_name,
        "ligand_required": require_ligand,
        "ligand_charge": ligand_charge,
        "expected_ligand_charge": expected_ligand_charge,
        "ligand_charge_matches_expected": charge_ok,
        "step5_input_normal_termination": normal,
        "step5_input_abnormal_termination": abnormal,
        "has_required_gromacs_files": has_required_files,
        "validation_passed": passed,
        "status": (
            "Technical_Pass_Not_Production_Approval"
            if passed else "Candidate_Validation_Failed"
        ),
        "production_ready": False,
        "no_mdrun": True,
    }


def write_markdown(report: Dict[str, object], path: Path) -> None:
    counts = report["counts"]
    molecules = report["molecules"]
    inspection = report["download_inspection"]
    lines = [
        "# CHARMM-GUI Package Validation",
        "",
        f"- Package: `{report['package']}`",
        f"- Status: `{report['status']}`",
        f"- Validation passed: {report['validation_passed']}",
        f"- Download classification: `{inspection['classification']}`",
        f"- Size: {report['package_size_bytes']} bytes",
        f"- SHA256: `{report['sha256']}`",
        f"- Regular-file members: {report['member_count']}",
        f"- Required GROMACS files present: {report['has_required_gromacs_files']}",
        f"- Step5 normal termination: {report['step5_input_normal_termination']}",
        f"- Step5 abnormal termination: {report['step5_input_abnormal_termination']}",
        f"- Ligand charge: {report['ligand_charge']}",
        f"- Missing required components: {report['missing_required_components']}",
        "- Production-ready: false",
        "- gmx mdrun executed: No",
        "",
        "## File Counts",
        "",
        "| Extension/Group | Count |",
        "|---|---:|",
    ]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Molecules", "", "| Molecule | Count |", "|---|---:|"])
    for key, value in molecules.items():
        lines.append(f"| {key} | {value} |")
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--outdir", type=Path, default=None)
    parser.add_argument("--prefix", default="charmmgui_package_validation")
    parser.add_argument("--require-ligand", action="store_true")
    parser.add_argument("--ligand-name", default="LIG")
    parser.add_argument("--expected-ligand-charge", type=float)
    parser.add_argument(
        "--component-profile",
        choices=sorted(COMPONENT_PROFILES),
        default="none",
    )
    parser.add_argument("--expected-component", action="append", default=[])
    args = parser.parse_args()

    expected_components = tuple(dict.fromkeys(
        (*COMPONENT_PROFILES[args.component_profile], *args.expected_component)
    ))
    outdir = (args.outdir or Path.cwd()).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    report = validate(
        args.package,
        require_ligand=args.require_ligand,
        ligand_name=args.ligand_name,
        expected_ligand_charge=args.expected_ligand_charge,
        expected_components=expected_components,
    )
    json_path = outdir / f"{args.prefix}.json"
    md_path = outdir / f"{args.prefix}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    write_markdown(report, md_path)
    print(json_path)
    print(md_path)
    return 0 if report["validation_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

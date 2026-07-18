#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Verify frozen custom ligand parameters in a CHARMM-GUI GROMACS package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import tarfile
from pathlib import Path

from inspect_charmmgui_download import inspect_artifact


KCAL_TO_KJ = 4.184
DEFAULT_TARGETS = (
    ((13, 25, 26, 27), ("C12", "C22", "O2", "C23")),
    ((30, 25, 26, 27), ("C25", "C22", "O2", "C23")),
    ((72, 25, 26, 27), ("H33", "C22", "O2", "C23")),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_case_insensitive(root: Path, relative: str) -> Path:
    current = root
    for part in Path(relative).parts:
        direct = current / part
        if direct.exists():
            current = direct
            continue
        if not current.is_dir():
            return direct
        matches = [child for child in current.iterdir() if child.name.lower() == part.lower()]
        if len(matches) != 1:
            return direct
        current = matches[0]
    return current


def read_package_file(package: Path, suffixes: list[str]) -> tuple[str | None, str]:
    suffixes = [suffix.replace("\\", "/") for suffix in suffixes]
    if package.is_dir():
        matches = sorted(
            path for path in package.rglob("*")
            if path.is_file()
            and any(path.as_posix().endswith(suffix) for suffix in suffixes)
        )
        if not matches:
            return None, ""
        return str(matches[0]), matches[0].read_text(errors="replace")
    if not tarfile.is_tarfile(package):
        raise ValueError(f"not a tar archive or directory: {package}")
    with tarfile.open(package, "r:*") as archive:
        matches = sorted(
            (
                member for member in archive.getmembers()
                if member.isfile() and any(member.name.endswith(suffix) for suffix in suffixes)
            ),
            key=lambda member: member.name,
        )
        if not matches:
            return None, ""
        handle = archive.extractfile(matches[0])
        if handle is None:
            return None, ""
        text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace").read()
        return matches[0].name, text


def parse_expected(path: Path) -> list[dict[str, object]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected = []
    for row in rows:
        if not row.get("new_kchi", "").strip():
            continue
        force_constant = float(row["new_kchi"])
        expected.append(
            {
                "action": row.get("action", ""),
                "source_line": row.get("source_line", ""),
                "types": tuple(row["atom_types"].split()),
                "multiplicity": int(row["multiplicity"]),
                "phase": float(row["phase_deg"]),
                "force_constant_kcal_mol": force_constant,
                "force_constant_kj_mol": force_constant * KCAL_TO_KJ,
            }
        )
    if not expected:
        raise ValueError("no expected changed parameter definitions found")
    return expected


def parse_charmm_dihedrals(text: str) -> list[dict[str, object]]:
    section = None
    rows = []
    for raw in text.splitlines():
        clean = raw.split("!", 1)[0].strip()
        if not clean or clean.startswith("*"):
            continue
        upper = clean.upper()
        if upper in {"BONDS", "ANGLES", "DIHEDRALS", "IMPROPERS", "NONBONDED", "END"}:
            section = upper
            continue
        if section != "DIHEDRALS":
            continue
        fields = clean.split()
        if len(fields) < 7:
            continue
        try:
            rows.append(
                {
                    "types": tuple(fields[:4]),
                    "function": None,
                    "force_constant": float(fields[4]),
                    "multiplicity": int(fields[5]),
                    "phase": float(fields[6]),
                    "line": raw,
                }
            )
        except ValueError:
            continue
    return rows


def parse_gromacs_dihedraltypes(text: str) -> list[dict[str, object]]:
    section = None
    rows = []
    for raw in text.splitlines():
        clean = raw.split(";", 1)[0].strip()
        if not clean or clean.startswith("#"):
            continue
        if clean.startswith("[") and "]" in clean:
            section = clean.strip("[] ").lower()
            continue
        if section != "dihedraltypes":
            continue
        fields = clean.split()
        if len(fields) < 8:
            continue
        try:
            rows.append(
                {
                    "types": tuple(fields[:4]),
                    "function": int(fields[4]),
                    "phase": float(fields[5]),
                    "force_constant": float(fields[6]),
                    "multiplicity": int(fields[7]),
                    "line": raw,
                }
            )
        except ValueError:
            continue
    return rows


def same_types(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    return left == right or left == tuple(reversed(right))


def same_phase(left: float, right: float, tolerance: float = 1e-6) -> bool:
    delta = abs((left - right) % 360.0)
    delta = min(delta, 360.0 - delta)
    return delta <= tolerance


def check_charmm_terms(
    expected: list[dict[str, object]], actual: list[dict[str, object]]
) -> list[dict[str, object]]:
    checks = []
    for row in expected:
        candidates = [
            term for term in actual
            if same_types(term["types"], row["types"])
            and term["multiplicity"] == row["multiplicity"]
            and same_phase(term["phase"], row["phase"])
        ]
        exact = [
            term for term in candidates
            if math.isclose(
                term["force_constant"], row["force_constant_kcal_mol"],
                rel_tol=1e-7, abs_tol=1e-7,
            )
        ]
        checks.append(
            {
                "action": row["action"],
                "source_line": row["source_line"],
                "atom_types": " ".join(row["types"]),
                "multiplicity": row["multiplicity"],
                "phase_deg": row["phase"],
                "expected_force_constant_kcal_mol": row["force_constant_kcal_mol"],
                "actual_candidates_kcal_mol": [term["force_constant"] for term in candidates],
                "matched": bool(exact),
            }
        )
    return checks


def check_gromacs_terms(
    expected: list[dict[str, object]], actual: list[dict[str, object]]
) -> list[dict[str, object]]:
    checks = []
    for row in expected:
        candidates = [
            term for term in actual
            if term["function"] == 9
            and same_types(term["types"], row["types"])
            and term["multiplicity"] == row["multiplicity"]
            and same_phase(term["phase"], row["phase"])
        ]
        exact = [
            term for term in candidates
            if math.isclose(
                term["force_constant"], row["force_constant_kj_mol"],
                rel_tol=2e-6, abs_tol=2e-5,
            )
        ]
        checks.append(
            {
                "action": row["action"],
                "source_line": row["source_line"],
                "atom_types": " ".join(row["types"]),
                "function": 9,
                "multiplicity": row["multiplicity"],
                "phase_deg_modulo_360": row["phase"] % 360.0,
                "expected_force_constant_kcal_mol": row["force_constant_kcal_mol"],
                "expected_force_constant_kj_mol": row["force_constant_kj_mol"],
                "actual_candidates_kj_mol": [term["force_constant"] for term in candidates],
                "matched": bool(exact),
            }
        )
    return checks


def parse_rtf(text: str) -> dict[str, object]:
    residue_charge = None
    atom_rows = []
    for raw in text.splitlines():
        fields = raw.split()
        if len(fields) >= 3 and fields[0].upper() == "RESI" and fields[1].upper() == "LIG":
            try:
                residue_charge = float(fields[2])
            except ValueError:
                pass
        if len(fields) >= 4 and fields[0].upper() == "ATOM":
            try:
                atom_rows.append((fields[1], fields[2], float(fields[3])))
            except ValueError:
                continue
    return {
        "residue_charge": residue_charge,
        "atom_count": len(atom_rows),
        "atom_charge_sum": sum(row[2] for row in atom_rows),
        "atom_rows": atom_rows,
    }


def parse_itp(text: str) -> dict[str, object]:
    section = None
    atoms: list[dict[str, object]] = []
    dihedrals: list[dict[str, object]] = []
    for raw in text.splitlines():
        clean = raw.split(";", 1)[0].strip()
        if not clean or clean.startswith("#"):
            continue
        if clean.startswith("[") and "]" in clean:
            section = clean.strip("[] ").lower()
            continue
        fields = clean.split()
        if section == "atoms" and len(fields) >= 8:
            try:
                atoms.append(
                    {
                        "index": int(fields[0]),
                        "type": fields[1],
                        "residue": fields[3],
                        "name": fields[4],
                        "charge": float(fields[6]),
                    }
                )
            except ValueError:
                continue
        elif section == "dihedrals" and len(fields) >= 5:
            try:
                dihedrals.append(
                    {
                        "indices": tuple(int(value) for value in fields[:4]),
                        "function": int(fields[4]),
                    }
                )
            except ValueError:
                continue
    return {
        "atoms": atoms,
        "atom_count": len(atoms),
        "charge_sum": sum(float(row["charge"]) for row in atoms),
        "dihedrals": dihedrals,
    }


def atom_identity_matches(left: dict[str, object], right: dict[str, object]) -> bool:
    left_atoms = left.get("atoms", [])
    right_atoms = right.get("atoms", [])
    if len(left_atoms) != len(right_atoms):
        return False
    for lhs, rhs in zip(left_atoms, right_atoms):
        if (lhs["index"], lhs["name"], lhs["type"]) != (
            rhs["index"], rhs["name"], rhs["type"]
        ):
            return False
        if not math.isclose(float(lhs["charge"]), float(rhs["charge"]), abs_tol=1e-7):
            return False
    return True


def target_connectivity_checks(itp: dict[str, object]) -> list[dict[str, object]]:
    atoms = {int(row["index"]): row for row in itp.get("atoms", [])}
    dihedrals = itp.get("dihedrals", [])
    checks = []
    for indices, expected_names in DEFAULT_TARGETS:
        matches = [
            row for row in dihedrals
            if row["function"] == 9
            and (row["indices"] == indices or row["indices"] == tuple(reversed(indices)))
        ]
        actual_names = tuple(atoms.get(index, {}).get("name") for index in indices)
        actual_types = tuple(atoms.get(index, {}).get("type") for index in indices)
        checks.append(
            {
                "atom_indices": list(indices),
                "expected_atom_names": list(expected_names),
                "actual_atom_names": list(actual_names),
                "actual_atom_types": list(actual_types),
                "function": 9,
                "atom_names_match": actual_names == expected_names,
                "connectivity_present": bool(matches),
                "matched": bool(matches) and actual_names == expected_names,
            }
        )
    return checks


def parse_hash_manifest(path: Path, root: Path) -> dict[str, object]:
    checks = []
    if not path.exists():
        return {"manifest": str(path), "exists": False, "checks": checks, "passed": False}
    for raw in path.read_text(errors="replace").splitlines():
        fields = raw.split(maxsplit=1)
        if len(fields) != 2:
            continue
        expected_hash, relative = fields
        relative = relative.lstrip("* ")
        candidate = resolve_case_insensitive(root, relative)
        if not candidate.exists() or not candidate.is_file():
            continue
        actual_hash = sha256(candidate)
        checks.append(
            {
                "path": relative,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "matched": actual_hash == expected_hash,
            }
        )
    return {
        "manifest": str(path),
        "exists": True,
        "checks": checks,
        "passed": bool(checks) and all(row["matched"] for row in checks),
    }


def invalid_download_result(package: Path, inspection: dict[str, object]) -> dict[str, object]:
    return {
        "package": str(package),
        "download_inspection": inspection,
        "custom_parameter_injection_verified": False,
        "status": "Invalid_Download_Artifact",
        "production_ready": False,
        "no_mdrun": True,
    }


def verify(
    frozen_dir: Path,
    package: Path,
    *,
    manifest: Path | None = None,
    ready_manifest: Path | None = None,
    primary_required_types: tuple[str, ...] = ("OG302", "CG2O2"),
    primary_count: int = 5,
) -> dict[str, object]:
    frozen_dir = frozen_dir.expanduser().resolve()
    package = package.expanduser().resolve()
    inspection = None
    if package.is_file():
        inspection = inspect_artifact(package)
        if inspection["classification"] != "valid_final_candidate":
            return invalid_download_result(package, inspection)

    expected = parse_expected(resolve_case_insensitive(frozen_dir, "changed_parameter_terms.tsv"))
    required_types = set(primary_required_types)
    primary = [
        row for row in expected
        if row["action"] == "candidate_replaced"
        and required_types.issubset(set(row["types"]))
    ]
    if len(primary) != primary_count:
        raise ValueError(f"expected {primary_count} primary terms, found {len(primary)}")

    prm_member, prm_text = read_package_file(package, ["/lig/lig.prm", "/lig/optimized_lig.prm"])
    rtf_member, rtf_text = read_package_file(package, ["/lig/lig.rtf", "/lig/optimized_lig.rtf"])
    str_member, str_text = read_package_file(package, ["/lig/lig.str", "/lig/optimized_LIG.str"])
    itp_member, itp_text = read_package_file(package, ["/gromacs/toppar/LIG.itp", "/optimized_LIG.itp"])
    forcefield_member, forcefield_text = read_package_file(
        package, ["/gromacs/toppar/forcefield.itp", "/forcefield.itp"]
    )

    pair_layout = bool(rtf_text and prm_text)
    standalone_str_layout = bool(
        str_text and parse_rtf(str_text)["atom_count"] and parse_charmm_dihedrals(str_text)
    )
    if pair_layout:
        package_layout = "lig.rtf_plus_lig.prm"
        effective_rtf_text = rtf_text
        effective_prm_text = prm_text
    elif standalone_str_layout:
        package_layout = "standalone_lig.str"
        effective_rtf_text = str_text
        effective_prm_text = str_text
    else:
        package_layout = "unsupported_or_incomplete"
        effective_rtf_text = ""
        effective_prm_text = ""

    missing_required_members = []
    if package_layout == "unsupported_or_incomplete":
        missing_required_members.append("lig.rtf+lig.prm or standalone lig.str")
    if not itp_text:
        missing_required_members.append("gromacs/toppar/LIG.itp")
    if not forcefield_text:
        missing_required_members.append("gromacs/toppar/forcefield.itp")

    charmm_actual = parse_charmm_dihedrals(effective_prm_text)
    gromacs_actual = parse_gromacs_dihedraltypes(forcefield_text)
    prm_checks = check_charmm_terms(expected, charmm_actual)
    primary_prm_checks = check_charmm_terms(primary, charmm_actual)
    forcefield_checks = check_gromacs_terms(expected, gromacs_actual)
    primary_forcefield_checks = check_gromacs_terms(primary, gromacs_actual)

    frozen_rtf_path = resolve_case_insensitive(frozen_dir, "optimized_lig.rtf")
    frozen_itp_path = resolve_case_insensitive(frozen_dir, "optimized_LIG.itp")
    frozen_rtf = parse_rtf(frozen_rtf_path.read_text(errors="replace"))
    package_rtf = parse_rtf(effective_rtf_text)
    frozen_itp = parse_itp(frozen_itp_path.read_text(errors="replace"))
    package_itp = parse_itp(itp_text)
    rtf_identity_match = package_rtf == frozen_rtf
    itp_atom_identity_match = atom_identity_matches(package_itp, frozen_itp)
    connectivity_checks = target_connectivity_checks(package_itp)

    package_root = frozen_dir.parent
    manifest_path = manifest or resolve_case_insensitive(
        package_root, "manifests/FILE_SHA256SUMS.txt"
    )
    hash_manifest = parse_hash_manifest(manifest_path, package_root)
    provenance_path = resolve_case_insensitive(frozen_dir, "parameter_provenance.json")
    provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
    ready_manifest_path = ready_manifest or resolve_case_insensitive(
        package_root, "manifests/CHARMMGUI_READY_INPUT_MANIFEST.json"
    )
    ready = json.loads(ready_manifest_path.read_text()) if ready_manifest_path.exists() else {}
    provenance_sha = provenance.get("frozen_parameter_sha256")
    ready_sha = ready.get("validation_gate", {}).get("frozen_parameter_sha256")
    frozen_parameter_sha_match = bool(provenance_sha) and provenance_sha == ready_sha

    expected_atom_count = frozen_rtf["atom_count"]
    expected_charge = frozen_rtf["residue_charge"]
    identity_ok = bool(
        rtf_identity_match
        and itp_atom_identity_match
        and package_rtf["atom_count"] == expected_atom_count
        and package_itp["atom_count"] == expected_atom_count
        and expected_charge is not None
        and math.isclose(float(package_rtf["residue_charge"]), float(expected_charge), abs_tol=1e-6)
        and math.isclose(float(package_rtf["atom_charge_sum"]), float(expected_charge), abs_tol=1e-6)
        and math.isclose(float(package_itp["charge_sum"]), float(expected_charge), abs_tol=1e-6)
    )
    primary_prm_matched = sum(bool(row["matched"]) for row in primary_prm_checks)
    primary_forcefield_matched = sum(bool(row["matched"]) for row in primary_forcefield_checks)
    prm_matched = sum(bool(row["matched"]) for row in prm_checks)
    forcefield_matched = sum(bool(row["matched"]) for row in forcefield_checks)
    connectivity_matched = sum(bool(row["matched"]) for row in connectivity_checks)
    passed = bool(
        not missing_required_members
        and prm_matched == len(expected)
        and forcefield_matched == len(expected)
        and primary_prm_matched == primary_count
        and primary_forcefield_matched == primary_count
        and connectivity_matched == len(DEFAULT_TARGETS)
        and identity_ok
        and hash_manifest["passed"]
        and frozen_parameter_sha_match
    )
    return {
        "package": str(package),
        "frozen_dir": str(frozen_dir),
        "download_inspection": inspection,
        "package_layout": package_layout,
        "parameter_storage_model": "LIG.itp function-9 connectivity plus toppar/forcefield.itp dihedraltypes",
        "package_members": {
            "rtf": rtf_member,
            "prm": prm_member,
            "str": str_member,
            "itp": itp_member,
            "forcefield_itp": forcefield_member,
        },
        "missing_required_members": missing_required_members,
        "lig_str_present": bool(str_text),
        "lig_str_required": False,
        "lig_str_absent_is_blocking": False,
        "primary_target_expected": primary_count,
        "primary_target_prm_matched": primary_prm_matched,
        "primary_target_forcefield_matched": primary_forcefield_matched,
        "primary_target_matched": primary_forcefield_matched,
        "primary_target_prm_checks": primary_prm_checks,
        "primary_target_forcefield_checks": primary_forcefield_checks,
        "changed_definition_expected": len(expected),
        "changed_definition_prm_matched": prm_matched,
        "changed_definition_forcefield_matched": forcefield_matched,
        "all_changed_prm_definitions_matched": prm_matched == len(expected),
        "all_changed_forcefield_dihedraltypes_matched": forcefield_matched == len(expected),
        "forcefield_kcal_to_kj_factor": KCAL_TO_KJ,
        "rtf_identity_match": rtf_identity_match,
        "itp_atom_identity_match": itp_atom_identity_match,
        "itp_semantic_match": itp_atom_identity_match,
        "rtf_atom_count": package_rtf.get("atom_count"),
        "rtf_charge": package_rtf.get("residue_charge"),
        "rtf_charge_sum": package_rtf.get("atom_charge_sum"),
        "itp_atom_count": package_itp.get("atom_count"),
        "itp_charge_sum": package_itp.get("charge_sum"),
        "target_connectivity_expected": len(DEFAULT_TARGETS),
        "target_connectivity_matched": connectivity_matched,
        "target_connectivity_checks": connectivity_checks,
        "hash_manifest_validation": hash_manifest,
        "frozen_parameter_sha256": provenance_sha,
        "ready_manifest_frozen_parameter_sha256": ready_sha,
        "frozen_parameter_sha_match": frozen_parameter_sha_match,
        "custom_parameter_injection_verified": passed,
        "status": (
            "Technical_Pass_Not_Production_Approval"
            if passed else "Candidate_Validation_Failed"
        ),
        "production_ready": False,
        "no_mdrun": True,
        "interpretation": (
            "A standalone lig.str is not required when lig.rtf and lig.prm are present. "
            "The final GROMACS package stores ligand connectivity in LIG.itp and "
            "converted custom dihedral values in forcefield.itp [ dihedraltypes ]."
        ),
    }


def write_reports(result: dict[str, object], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "custom_ligand_injection_validation.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    lines = [
        "# Custom Ligand Injection Validation",
        "",
        f"- Verified: **{result.get('custom_parameter_injection_verified', False)}**",
        f"- Status: `{result['status']}`",
        f"- Package layout: `{result.get('package_layout', 'unknown')}`",
        f"- Standalone lig.str required: **{result.get('lig_str_required', False)}**",
        f"- Changed PRM terms: {result.get('changed_definition_prm_matched', 0)}/{result.get('changed_definition_expected', 0)}",
        f"- Changed GROMACS dihedraltypes: {result.get('changed_definition_forcefield_matched', 0)}/{result.get('changed_definition_expected', 0)}",
        f"- Primary optimized GROMACS terms: {result.get('primary_target_forcefield_matched', 0)}/{result.get('primary_target_expected', 0)}",
        f"- Target function-9 connections: {result.get('target_connectivity_matched', 0)}/{result.get('target_connectivity_expected', 0)}",
        f"- LIG atom identity match: {result.get('itp_atom_identity_match', False)}",
        f"- Frozen parameter SHA match: {result.get('frozen_parameter_sha_match', False)}",
        "- Parameter storage: `LIG.itp` function-9 connectivity plus `toppar/forcefield.itp` dihedraltypes.",
        "- Production-ready: **false**",
        "- gmx mdrun executed: **No**",
        "",
    ]
    (output / "custom_ligand_injection_validation.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-dir", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--ready-manifest", type=Path)
    parser.add_argument("--primary-required-type", action="append")
    parser.add_argument("--primary-count", type=int, default=5)
    args = parser.parse_args()

    result = verify(
        args.frozen_dir,
        args.package,
        manifest=args.manifest,
        ready_manifest=args.ready_manifest,
        primary_required_types=tuple(args.primary_required_type or ("OG302", "CG2O2")),
        primary_count=args.primary_count,
    )
    write_reports(result, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("custom_parameter_injection_verified") else 2


if __name__ == "__main__":
    raise SystemExit(main())

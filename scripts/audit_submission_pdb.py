#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Audit a segmented CHARMM-GUI submission PDB against immutable sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_RANGES = {
    "A": (96, 160),
    "B": (169, 309),
    "C": (338, 425),
    "D": (788, 875),
    "E": (881, 942),
    "F": (952, 1019),
    "G": (1282, 1384),
    "H": (1388, 1564),
    "I": (1604, 1866),
}
WATER = {"HOH", "WAT", "TIP3", "TIP3P", "SOL"}
OLD_BULK_IONS = {"NA", "SOD", "CL", "CLA", "MG", "MG2"}
FORBIDDEN_HETERO = {"JL3", "Y01", "LPE", "NAG"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_atom_line(line: str) -> bool:
    return line.startswith("ATOM  ") or line.startswith("HETATM")


def parse_atom(line: str) -> dict[str, object]:
    return {
        "record": line[:6].strip(),
        "serial": int(line[6:11]),
        "name": line[12:16].strip(),
        "altloc": line[16:17].strip(),
        "resname": line[17:20].strip(),
        "chain": line[21:22],
        "resid": int(line[22:26]),
        "icode": line[26:27].strip(),
        "xyz": tuple(float(line[start:end]) for start, end in ((30, 38), (38, 46), (46, 54))),
        "element": line[76:78].strip() if len(line) >= 78 else "",
    }


def ligand_record(atom: dict[str, object]) -> bool:
    return atom["record"] == "HETATM" and atom["resname"] == "LIG" and atom["chain"] == "A" and atom["resid"] == 2416


def mask_allowed_ligand_name_change(line: str) -> str:
    if is_atom_line(line):
        atom = parse_atom(line)
        if ligand_record(atom):
            return line[:12] + "    " + line[16:]
    return line


def coordinate_rmsd(left: list[dict[str, object]], right: list[dict[str, object]]) -> float | None:
    if len(left) != len(right) or not left:
        return None
    squared = 0.0
    for a, b in zip(left, right):
        squared += sum((x - y) ** 2 for x, y in zip(a["xyz"], b["xyz"]))
    return math.sqrt(squared / len(left))


def parse_rtf(path: Path) -> dict[str, object]:
    atoms = []
    residue_charge = None
    for raw in path.read_text(errors="replace").splitlines():
        fields = raw.split()
        if len(fields) >= 3 and fields[0].upper() == "RESI" and fields[1] == "LIG":
            residue_charge = float(fields[2])
        if len(fields) >= 4 and fields[0].upper() == "ATOM":
            atoms.append({"name": fields[1], "type": fields[2], "charge": float(fields[3])})
    heavy_names = [row["name"] for row in atoms if not row["name"].upper().startswith("H")]
    return {
        "residue_charge": residue_charge,
        "atom_count": len(atoms),
        "heavy_atom_names": heavy_names,
        "atom_charge_sum": sum(row["charge"] for row in atoms),
    }


def analyze(path: Path) -> tuple[list[str], list[dict[str, object]], list[str], list[dict[str, str]]]:
    lines = path.read_text(errors="strict").splitlines(keepends=True)
    atoms = [parse_atom(line) for line in lines if is_atom_line(line)]
    ter_boundaries = []
    ter_label_warnings = []
    previous_protein_chain = None
    for line in lines:
        if line.startswith("ATOM  "):
            previous_protein_chain = line[21:22]
        elif line.startswith("TER"):
            record_chain = line[21:22].strip() if len(line) > 21 else ""
            boundary_chain = previous_protein_chain or record_chain
            ter_boundaries.append(boundary_chain or "")
            if record_chain and previous_protein_chain and record_chain != previous_protein_chain:
                ter_label_warnings.append(
                    {"boundary_after_chain": previous_protein_chain, "ter_record_chain": record_chain}
                )
            previous_protein_chain = None
    return lines, atoms, ter_boundaries, ter_label_warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--segmented-source", type=Path, required=True)
    parser.add_argument("--aligned-ligand-source", type=Path, required=True)
    parser.add_argument("--rtf", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    submission_lines, atoms, ter_chains, ter_label_warnings = analyze(args.submission)
    segmented_lines, segmented_atoms, _, source_ter_label_warnings = analyze(args.segmented_source)
    _, aligned_atoms, _, _ = analyze(args.aligned_ligand_source)

    protein = [atom for atom in atoms if atom["record"] == "ATOM"]
    ligand = [atom for atom in atoms if ligand_record(atom)]
    calcium = [
        atom for atom in atoms
        if atom["record"] == "HETATM" and atom["resname"] == "CA" and atom["chain"] == "A" and atom["resid"] == 2403
    ]
    aligned_ligand = [atom for atom in aligned_atoms if ligand_record(atom)]
    segmented_protein = [atom for atom in segmented_atoms if atom["record"] == "ATOM"]

    residues_by_chain: dict[str, set[int]] = defaultdict(set)
    for atom in protein:
        residues_by_chain[str(atom["chain"])].add(int(atom["resid"]))
    observed_ranges = {
        chain: (min(residues), max(residues)) for chain, residues in sorted(residues_by_chain.items())
    }

    protein_keys = [
        (atom["chain"], atom["resid"], atom["icode"], atom["name"], atom["altloc"])
        for atom in protein
    ]
    ligand_keys = [(atom["chain"], atom["resid"], atom["name"], atom["altloc"]) for atom in ligand]
    duplicate_protein = [key for key, count in Counter(protein_keys).items() if count > 1]
    duplicate_ligand = [key for key, count in Counter(ligand_keys).items() if count > 1]

    hetero = [atom for atom in atoms if atom["record"] == "HETATM"]
    old_solvent_or_ions = sorted({str(atom["resname"]) for atom in hetero if atom["resname"] in WATER | OLD_BULK_IONS})
    forbidden_hetero = sorted({str(atom["resname"]) for atom in hetero if atom["resname"] in FORBIDDEN_HETERO})
    unrelated_hetero = sorted({
        str(atom["resname"]) for atom in hetero
        if atom["resname"] not in {"LIG", "CA"} | WATER | OLD_BULK_IONS | FORBIDDEN_HETERO
    })

    rtf = parse_rtf(args.rtf)
    ligand_names = [str(atom["name"]) for atom in ligand]
    aligned_names = [str(atom["name"]) for atom in aligned_ligand]
    rtf_heavy_names = list(rtf["heavy_atom_names"])
    only_name_field_changed = (
        len(submission_lines) == len(segmented_lines)
        and all(
            mask_allowed_ligand_name_change(left) == mask_allowed_ligand_name_change(right)
            for left, right in zip(submission_lines, segmented_lines)
        )
    )

    protein_rmsd = coordinate_rmsd(protein, segmented_protein)
    ligand_rmsd = coordinate_rmsd(ligand, aligned_ligand)
    altlocs = sorted({str(atom["altloc"]) for atom in atoms if atom["altloc"]})

    checks = {
        "protein_chains_and_ranges_exact": observed_ranges == EXPECTED_RANGES,
        "nine_independent_protein_chains": set(observed_ranges) == set(EXPECTED_RANGES),
        "nine_ter_boundaries_present": len(ter_chains) >= 9 and set(EXPECTED_RANGES).issubset(set(ter_chains)),
        "ca_a2403_one_atom": len(calcium) == 1,
        "lig_a2416_39_heavy_atoms": len(ligand) == 39 and all(atom["element"] != "H" for atom in ligand),
        "ligand_names_match_aligned_source": ligand_names == aligned_names,
        "ligand_names_match_optimized_rtf": ligand_names == rtf_heavy_names,
        "ligand_coordinate_rmsd_zero": ligand_rmsd is not None and ligand_rmsd <= 1e-9,
        "protein_coordinate_rmsd_zero": protein_rmsd is not None and protein_rmsd <= 1e-9,
        "only_ligand_atom_name_fields_changed": only_name_field_changed,
        "no_old_water_na_cl_mg": not old_solvent_or_ions,
        "no_jl3_y01_lpe_nag": not forbidden_hetero,
        "no_unrelated_hetero": not unrelated_hetero,
        "no_duplicate_protein_atoms": not duplicate_protein,
        "no_duplicate_ligand_atoms": not duplicate_ligand,
        "no_altlocs": not altlocs,
        "rtf_identity_92_atoms_charge_plus_1": (
            rtf["atom_count"] == 92
            and math.isclose(float(rtf["residue_charge"]), 1.0, abs_tol=1e-6)
            and math.isclose(float(rtf["atom_charge_sum"]), 1.0, abs_tol=1e-6)
        ),
    }
    passed = all(checks.values())
    result = {
        "submission": str(args.submission.resolve()),
        "submission_sha256": sha256(args.submission),
        "segmented_source": str(args.segmented_source.resolve()),
        "aligned_ligand_source": str(args.aligned_ligand_source.resolve()),
        "optimized_rtf": str(args.rtf.resolve()),
        "observed_protein_ranges": observed_ranges,
        "expected_protein_ranges": EXPECTED_RANGES,
        "ter_count": len(ter_chains),
        "ter_chains": ter_chains,
        "ter_record_label_warnings": ter_label_warnings,
        "source_ter_record_label_warnings": source_ter_label_warnings,
        "protein_atom_count": len(protein),
        "ligand_heavy_atom_count": len(ligand),
        "calcium_atom_count": len(calcium),
        "protein_coordinate_rmsd_angstrom": protein_rmsd,
        "ligand_coordinate_rmsd_angstrom": ligand_rmsd,
        "old_solvent_or_ions": old_solvent_or_ions,
        "forbidden_hetero": forbidden_hetero,
        "unrelated_hetero": unrelated_hetero,
        "duplicate_protein_atoms": duplicate_protein,
        "duplicate_ligand_atoms": duplicate_ligand,
        "altlocs": altlocs,
        "checks": checks,
        "passed": passed,
        "upload_allowed": passed,
        "production_ready": False,
        "no_mdrun": True,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n")
    rows = "\n".join(f"| {name} | {value} |" for name, value in checks.items())
    args.markdown.write_text(
        "# Submission PDB Audit\n\n"
        f"- Passed: **{passed}**\n"
        f"- Upload allowed: **{passed}**\n"
        f"- Submission SHA256: `{result['submission_sha256']}`\n"
        f"- Protein/LIG/CA atoms: {len(protein)} / {len(ligand)} / {len(calcium)}\n"
        f"- Protein/LIG coordinate RMSD: {protein_rmsd} / {ligand_rmsd} A\n"
        "- Production-ready: **false**\n"
        "- gmx mdrun executed: **No**\n\n"
        "| Check | Pass |\n|---|---|\n" + rows + "\n"
    )
    print(json.dumps(result, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

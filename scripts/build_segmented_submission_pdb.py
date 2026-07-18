#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Build a segmented submission PDB by changing only ligand atom-name fields."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def is_atom_line(line: str) -> bool:
    return line.startswith("ATOM  ") or line.startswith("HETATM")


def residue_id(line: str) -> tuple[str, str, int]:
    return line[17:20].strip(), line[21:22], int(line[22:26])


def selected(line: str, resname: str, chain: str, resid: int) -> bool:
    return is_atom_line(line) and residue_id(line) == (resname, chain, resid)


def atom_record(line: str) -> dict[str, object]:
    return {
        "serial": int(line[6:11]),
        "name_field": line[12:16],
        "name": line[12:16].strip(),
        "xyz": tuple(float(line[start:end]) for start, end in ((30, 38), (38, 46), (46, 54))),
        "occupancy": line[54:60],
        "bfactor": line[60:66],
        "element": line[76:78].strip() if len(line) >= 78 else "",
    }


def rmsd(left: list[dict[str, object]], right: list[dict[str, object]]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("cannot calculate RMSD for unequal or empty atom sets")
    squared = 0.0
    for a, b in zip(left, right):
        squared += sum((x - y) ** 2 for x, y in zip(a["xyz"], b["xyz"]))
    return math.sqrt(squared / len(left))


def mapping_name_fields(path: Path, source_records: list[dict[str, object]]) -> list[str]:
    with path.open(newline="") as handle:
        rows = sorted(csv.DictReader(handle, delimiter="\t"), key=lambda row: int(row["heavy_atom_order"]))
    if len(rows) != len(source_records):
        raise ValueError(f"mapping rows {len(rows)} != ligand atoms {len(source_records)}")
    fields = []
    for row, source in zip(rows, source_records):
        if row["old_pdb_atom_name"] != source["name"]:
            raise ValueError(
                f"mapping/source mismatch at atom {row['heavy_atom_order']}: "
                f"{row['old_pdb_atom_name']} != {source['name']}"
            )
        fields.append(f"{row['submission_atom_name']:>4}"[-4:])
    return fields


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segmented-pdb", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--aligned-ligand-pdb", type=Path)
    source.add_argument("--mapping-tsv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--resname", default="LIG")
    parser.add_argument("--chain", default="A")
    parser.add_argument("--resid", type=int, default=2416)
    parser.add_argument("--coordinate-tolerance", type=float, default=1e-6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    segmented_lines = args.segmented_pdb.read_text(errors="strict").splitlines(keepends=True)
    selected_indices = [
        index for index, line in enumerate(segmented_lines)
        if selected(line, args.resname, args.chain, args.resid)
    ]
    segmented_records = [atom_record(segmented_lines[index]) for index in selected_indices]
    if not segmented_records:
        raise SystemExit("selected ligand was not found in segmented PDB")

    aligned_records: list[dict[str, object]] | None = None
    if args.aligned_ligand_pdb:
        aligned_lines = args.aligned_ligand_pdb.read_text(errors="strict").splitlines(keepends=True)
        aligned_selected = [
            line for line in aligned_lines
            if selected(line, args.resname, args.chain, args.resid)
        ]
        aligned_records = [atom_record(line) for line in aligned_selected]
        if len(aligned_records) != len(segmented_records):
            raise SystemExit(
                f"ligand atom-count mismatch: segmented={len(segmented_records)}, "
                f"aligned={len(aligned_records)}"
            )
        for index, (segmented, aligned) in enumerate(zip(segmented_records, aligned_records), start=1):
            for field in ("serial", "occupancy", "bfactor", "element"):
                if segmented[field] != aligned[field]:
                    raise SystemExit(f"ligand {field} mismatch at atom {index}")
        coordinate_rmsd = rmsd(segmented_records, aligned_records)
        if coordinate_rmsd > args.coordinate_tolerance:
            raise SystemExit(f"ligand coordinate RMSD {coordinate_rmsd} exceeds tolerance")
        new_name_fields = [str(record["name_field"]) for record in aligned_records]
    else:
        coordinate_rmsd = 0.0
        new_name_fields = mapping_name_fields(args.mapping_tsv, segmented_records)

    output_lines = list(segmented_lines)
    changes = []
    for source_index, name_field in zip(selected_indices, new_name_fields):
        old_line = output_lines[source_index]
        old_name = old_line[12:16].strip()
        new_name = name_field.strip()
        output_lines[source_index] = old_line[:12] + name_field + old_line[16:]
        changes.append({"serial": int(old_line[6:11]), "old_name": old_name, "new_name": new_name})

    report = {
        "segmented_pdb": str(args.segmented_pdb.resolve()),
        "aligned_ligand_pdb": str(args.aligned_ligand_pdb.resolve()) if args.aligned_ligand_pdb else None,
        "mapping_tsv": str(args.mapping_tsv.resolve()) if args.mapping_tsv else None,
        "output": str(args.output.resolve()),
        "dry_run": args.dry_run,
        "ligand_selector": {"resname": args.resname, "chain": args.chain, "resid": args.resid},
        "ligand_atom_count": len(segmented_records),
        "ligand_coordinate_rmsd_angstrom": coordinate_rmsd,
        "changed_atom_name_count": sum(row["old_name"] != row["new_name"] for row in changes),
        "changes": changes,
        "only_pdb_atom_name_field_changed": True,
    }

    if not args.dry_run:
        if args.output.exists():
            raise SystemExit(f"refusing to overwrite existing output: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("".join(output_lines))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

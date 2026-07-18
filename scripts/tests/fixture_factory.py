# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
from __future__ import annotations

import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path


COMPONENTS = {
    "PROA": 1, "PROB": 1, "PROC": 1, "PROD": 1, "PROE": 1,
    "PROF": 1, "PROG": 1, "PROH": 1, "PROI": 1, "CAL": 1,
    "LIG": 1, "CHL1": 216, "POPC": 504, "SOD": 194, "CLA": 204,
    "TIP3": 70874,
}


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    archive.addfile(info, io.BytesIO(data))


def topol_text(components: dict[str, int] | None = None) -> str:
    rows = ["[ system ]", "fixture", "", "[ molecules ]"]
    rows.extend(f"{name:<8} {count}" for name, count in (components or COMPONENTS).items())
    return "\n".join(rows) + "\n"


def create_download_archive(
    path: Path,
    *,
    gzip: bool = False,
    include_gromacs: bool = True,
    unsafe_name: str | None = None,
    step5_text: str = "NORMAL TERMINATION\n",
    components: dict[str, int] | None = None,
) -> Path:
    mode = "w:gz" if gzip else "w"
    with tarfile.open(path, mode) as archive:
        if unsafe_name:
            add_bytes(archive, unsafe_name, b"unsafe fixture\n")
        if include_gromacs:
            members = {
                "job/gromacs/step5_input.gro": b"fixture\n",
                "job/gromacs/topol.top": topol_text(components).encode(),
                "job/gromacs/toppar/LIG.itp": b"[ atoms ]\n1 CG331 1 LIG C1 1 1.0 12.011\n",
                "job/gromacs/step7_production.mdp": b"integrator = md\n",
                "job/step5_input.out": step5_text.encode(),
            }
        else:
            members = {"job/step1_pdbreader.pdb": b"ATOM fixture\n"}
        for name, data in members.items():
            add_bytes(archive, name, data)
    return path


def expected_terms() -> list[dict[str, object]]:
    rows = [
        ("candidate_replaced", "CG2O2 OG302 CG3C51 CG3C51", 1, 180.0, 1.533),
        ("candidate_replaced", "CG2O2 OG302 CG3C51 CG3C51", 3, 0.0, 0.0),
        ("candidate_replaced", "CG2O2 OG302 CG3C51 CG3C52", 1, 180.0, 3.97),
        ("candidate_replaced", "CG2O2 OG302 CG3C51 CG3C52", 3, 0.0, 0.0),
        ("candidate_replaced", "CG2O2 OG302 CG3C51 HGA1", 3, 0.0, 0.0),
    ]
    for index in range(1, 42):
        rows.append(
            (
                "candidate_inserted",
                f"T{index}A T{index}B T{index}C T{index}D",
                index % 6 + 1,
                180.0 if index % 2 else 0.0,
                round(index * 0.071, 6),
            )
        )
    return [
        {
            "action": action,
            "source_line": str(index + 1),
            "atom_types": types,
            "multiplicity": multiplicity,
            "phase_deg": phase,
            "old_kchi": 0.0,
            "new_kchi": force,
        }
        for index, (action, types, multiplicity, phase, force) in enumerate(rows)
    ]


def atom_rows() -> list[dict[str, object]]:
    special = {
        13: ("C12", "CG3C51"),
        25: ("C22", "CG3C51"),
        26: ("O2", "OG302"),
        27: ("C23", "CG2O2"),
        30: ("C25", "CG3C52"),
        72: ("H33", "HGA1"),
    }
    rows = []
    for index in range(1, 93):
        name, atom_type = special.get(index, (f"A{index}", "CG331"))
        rows.append(
            {
                "index": index,
                "name": name,
                "type": atom_type,
                "charge": 1.0 if index == 1 else 0.0,
            }
        )
    return rows


def rtf_text() -> str:
    rows = ["* fixture", "*", "RESI LIG 1.000"]
    rows.extend(
        f"ATOM {row['name']:<5} {row['type']:<8} {row['charge']:.6f}"
        for row in atom_rows()
    )
    rows.append("END")
    return "\n".join(rows) + "\n"


def prm_text(terms: list[dict[str, object]]) -> str:
    rows = ["* fixture", "*", "DIHEDRALS"]
    for row in terms:
        rows.append(
            f"{row['atom_types']} {row['new_kchi']:.6f} "
            f"{row['multiplicity']} {row['phase_deg']:.6f}"
        )
    rows.append("END")
    return "\n".join(rows) + "\n"


def itp_text(*, explicit_parameters: bool, omit_connection: bool = False) -> str:
    rows = ["[ moleculetype ]", "LIG 3", "", "[ atoms ]"]
    rows.extend(
        f"{row['index']:5d} {row['type']:<8} 1 LIG {row['name']:<5} "
        f"{row['index']:5d} {row['charge']:.6f} 12.011"
        for row in atom_rows()
    )
    rows.extend(["", "[ dihedrals ]"])
    connections = [(13, 25, 26, 27), (27, 26, 25, 30), (27, 26, 25, 72)]
    if omit_connection:
        connections.pop()
    for connection in connections:
        suffix = " 180.0 6.414072 1" if explicit_parameters else ""
        rows.append(" ".join(str(value) for value in connection) + " 9" + suffix)
    return "\n".join(rows) + "\n"


def forcefield_text(
    terms: list[dict[str, object]], *, missing_term_index: int | None = None
) -> str:
    rows = ["[ dihedraltypes ]"]
    for index, row in enumerate(terms):
        if index == missing_term_index:
            continue
        types = row["atom_types"].split()
        if index % 2:
            types.reverse()
        phase = float(row["phase_deg"]) + (360.0 if index % 3 == 0 else 0.0)
        force_kj = float(row["new_kchi"]) * 4.184
        rows.append(
            f"{' '.join(types)} 9 {phase:.6f} {force_kj:.8e} {row['multiplicity']}"
        )
    return "\n".join(rows) + "\n"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def create_custom_case(
    root: Path,
    *,
    standalone_str: bool = False,
    missing_forcefield_term_index: int | None = None,
    omit_connection: bool = False,
) -> tuple[Path, Path]:
    frozen_dir = root / "00_Inputs" / "Ligand"
    manifest_dir = root / "00_Inputs" / "Manifests"
    frozen_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True)
    terms = expected_terms()

    changed = frozen_dir / "changed_parameter_terms.tsv"
    with changed.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "action", "source_line", "atom_types", "multiplicity",
                "phase_deg", "old_kchi", "new_kchi",
            ),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(terms)
    (frozen_dir / "optimized_lig.rtf").write_text(rtf_text())
    (frozen_dir / "optimized_lig.prm").write_text(prm_text(terms))
    (frozen_dir / "optimized_LIG.itp").write_text(itp_text(explicit_parameters=True))
    frozen_sha = "fixture-frozen-parameter-sha"
    (frozen_dir / "parameter_provenance.json").write_text(
        json.dumps({"frozen_parameter_sha256": frozen_sha}) + "\n"
    )
    (manifest_dir / "CHARMMGUI_READY_INPUT_MANIFEST.json").write_text(
        json.dumps({"validation_gate": {"frozen_parameter_sha256": frozen_sha}}) + "\n"
    )
    manifest_rows = []
    for path in sorted(frozen_dir.iterdir()):
        if path.is_file():
            manifest_rows.append(f"{file_sha256(path)}  ligand/{path.name}")
    (manifest_dir / "FILE_SHA256SUMS.txt").write_text("\n".join(manifest_rows) + "\n")

    package = root / "custom_fixture.tar"
    package_itp = itp_text(explicit_parameters=False, omit_connection=omit_connection)
    ff_text = forcefield_text(terms, missing_term_index=missing_forcefield_term_index)
    members = {
        "job/gromacs/step5_input.gro": "fixture\n",
        "job/gromacs/topol.top": topol_text(),
        "job/gromacs/toppar/LIG.itp": package_itp,
        "job/gromacs/toppar/forcefield.itp": ff_text,
        "job/gromacs/step7_production.mdp": "integrator = md\n",
        "job/step5_input.out": "NORMAL TERMINATION\n",
    }
    if standalone_str:
        members["job/lig/lig.str"] = rtf_text() + "\n" + prm_text(terms)
    else:
        members["job/lig/lig.rtf"] = rtf_text()
        members["job/lig/lig.prm"] = prm_text(terms)
    with tarfile.open(package, "w") as archive:
        for name, text in members.items():
            add_bytes(archive, name, text.encode())
    return frozen_dir, package

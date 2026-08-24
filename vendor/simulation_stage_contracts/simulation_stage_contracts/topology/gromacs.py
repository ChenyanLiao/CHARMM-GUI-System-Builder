from __future__ import annotations

import re


def _sections(text: str) -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    current = ""
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r"\[\s*([^]]+?)\s*\]", line)
        if match:
            current = match.group(1).strip().lower()
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line.split())
    return sections


def parse_molecules(text: str) -> dict[str, int]:
    molecules: dict[str, int] = {}
    for row in _sections(text).get("molecules", []):
        if len(row) >= 2:
            try:
                molecules[row[0]] = molecules.get(row[0], 0) + int(row[1])
            except ValueError:
                continue
    return molecules


def parse_gromacs_topology(text: str) -> dict:
    sections = _sections(text)
    atoms = []
    for row in sections.get("atoms", []):
        if len(row) >= 7:
            try:
                atoms.append({"index": int(row[0]), "type": row[1], "residue": row[3], "name": row[4], "charge": float(row[6])})
            except ValueError:
                continue
    dihedrals = []
    for row in sections.get("dihedrals", []):
        if len(row) >= 5:
            try:
                dihedrals.append({"indices": tuple(map(int, row[:4])), "function": int(row[4]), "parameters": tuple(row[5:])})
            except ValueError:
                continue
    types = []
    for row in sections.get("dihedraltypes", []):
        if len(row) >= 8:
            try:
                types.append({
                    "atom_types": tuple(row[:4]),
                    "function": int(row[4]),
                    "phase": float(row[5]),
                    "force_constant": float(row[6]),
                    "multiplicity": int(row[7]),
                })
            except ValueError:
                continue
    return {"atoms": atoms, "dihedrals": dihedrals, "dihedraltypes": types, "molecules": parse_molecules(text)}

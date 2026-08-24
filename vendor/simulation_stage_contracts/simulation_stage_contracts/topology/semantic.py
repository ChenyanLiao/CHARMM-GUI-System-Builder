from __future__ import annotations

from collections import Counter

from .gromacs import parse_gromacs_topology


def _bonded_key(row: dict) -> tuple:
    indices = tuple(row["indices"])
    canonical = min(indices, tuple(reversed(indices)))
    return canonical, int(row["function"]), tuple(row.get("parameters", ()))


def compare_topologies(expected_text: str, actual_text: str) -> dict:
    expected = parse_gromacs_topology(expected_text)
    actual = parse_gromacs_topology(actual_text)
    expected_atoms = [(row["index"], row["name"], row["type"], round(row["charge"], 8)) for row in expected["atoms"]]
    actual_atoms = [(row["index"], row["name"], row["type"], round(row["charge"], 8)) for row in actual["atoms"]]
    expected_dihedrals = Counter(_bonded_key(row) for row in expected["dihedrals"])
    actual_dihedrals = Counter(_bonded_key(row) for row in actual["dihedrals"])
    return {
        "atoms_match": expected_atoms == actual_atoms,
        "dihedral_connectivity_match": expected_dihedrals == actual_dihedrals,
        "molecules_match": expected["molecules"] == actual["molecules"],
        "semantic_match": expected_atoms == actual_atoms and expected_dihedrals == actual_dihedrals and expected["molecules"] == actual["molecules"],
    }


def derive_component_roles(molecules: dict[str, int], role_rules: dict[str, list[str]]) -> dict:
    roles: dict[str, dict[str, int]] = {}
    assigned: set[str] = set()
    for role, names in role_rules.items():
        selected = {name: molecules[name] for name in names if name in molecules}
        roles[role] = selected
        assigned.update(selected)
    roles["unclassified"] = {name: count for name, count in molecules.items() if name not in assigned}
    return roles

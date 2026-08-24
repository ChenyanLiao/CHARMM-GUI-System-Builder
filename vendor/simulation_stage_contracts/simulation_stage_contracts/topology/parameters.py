from __future__ import annotations

import math


def normalize_phase(value: float) -> float:
    normalized = value % 360.0
    return 0.0 if math.isclose(normalized, 360.0, abs_tol=1e-9) else normalized


def compare_periodic_dihedrals(expected: dict, actual: dict, tolerance: float = 1e-6) -> bool:
    forward = tuple(expected["atom_types"])
    observed = tuple(actual["atom_types"])
    return bool(
        observed in {forward, tuple(reversed(forward))}
        and int(expected["function"]) == int(actual["function"])
        and int(expected["multiplicity"]) == int(actual["multiplicity"])
        and math.isclose(normalize_phase(float(expected["phase"])), normalize_phase(float(actual["phase"])), abs_tol=tolerance)
        and math.isclose(float(expected["force_constant"]), float(actual["force_constant"]), rel_tol=tolerance, abs_tol=tolerance)
    )

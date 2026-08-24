from __future__ import annotations

from collections import defaultdict

from ..errors import StageContractError
from .model import SegmentIdentity


def reconcile_segments(expected: list[SegmentIdentity], actual_molecules: set[str], allowed_coalescence: dict[str, list[str]] | None = None) -> dict:
    allowed_coalescence = allowed_coalescence or {}
    by_actual: dict[str, list[str]] = defaultdict(list)
    missing: list[str] = []
    for row in expected:
        if row.gromacs_molecule in actual_molecules:
            by_actual[row.gromacs_molecule].append(row.biological_segment)
            continue
        target = next((name for name, sources in allowed_coalescence.items() if row.biological_segment in sources and name in actual_molecules), None)
        if target:
            by_actual[target].append(row.biological_segment)
        else:
            missing.append(row.biological_segment)
    unexplained = {
        target: sources for target, sources in by_actual.items()
        if len(sources) > 1 and set(sources) != set(allowed_coalescence.get(target, []))
    }
    if missing or unexplained:
        raise StageContractError("E_SEGMENT_MISMATCH", "segment identities cannot be reconciled", {"missing": missing, "unexplained_coalescence": unexplained})
    return {"status": "PASS", "matrix": dict(by_actual), "missing": [], "unexplained_coalescence": {}}

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SegmentIdentity:
    biological_segment: str
    pdb_chain: str
    charmm_segment: str
    gromacs_molecule: str

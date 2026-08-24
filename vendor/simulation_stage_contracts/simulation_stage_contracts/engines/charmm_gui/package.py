from __future__ import annotations

import re
from pathlib import Path

from ...topology.gromacs import parse_molecules
from .archive import inspect_archive, read_text_member


def inspect_package(path: Path) -> dict:
    inspection = inspect_archive(path)
    if inspection.get("classification") != "valid_final_candidate":
        return {
            "technical_status": "BLOCKED",
            "download_inspection": inspection,
            "molecules": {},
            "normal_termination": False,
            "abnormal_termination": False,
            "production_ready": False,
            "no_mdrun": True,
        }
    topol_member, topol = read_text_member(path, "gromacs/topol.top")
    if not topol:
        topol_member, topol = read_text_member(path, "topol.top")
    output_member, output = read_text_member(path, "step5_input.out")
    normal = bool(re.search(r"(?m)^\s*NORMAL TERMINATION\b", output))
    abnormal = bool(re.search(r"(?m)^\s*ABNORMAL TERMINATION\b", output))
    molecules = parse_molecules(topol)
    passed = bool(topol and molecules and normal and not abnormal)
    return {
        "technical_status": "Technical_Pass_Not_Production_Approval" if passed else "BLOCKED",
        "download_inspection": inspection,
        "topol_member": topol_member,
        "step5_input_out_member": output_member,
        "molecules": molecules,
        "normal_termination": normal,
        "abnormal_termination": abnormal,
        "production_ready": False,
        "no_mdrun": True,
    }

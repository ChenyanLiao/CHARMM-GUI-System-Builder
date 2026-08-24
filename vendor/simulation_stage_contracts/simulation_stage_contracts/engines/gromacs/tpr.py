from __future__ import annotations

import subprocess
from pathlib import Path

from ...artifacts import artifact_identity
from ...errors import StageContractError


def read_tpr(executable: Path, workdir: Path, tpr: str, timeout: int = 120) -> dict:
    workdir = workdir.resolve()
    tpr_path = workdir / tpr
    if not tpr_path.is_file():
        raise StageContractError("E_TPR_READBACK_FAILED", "TPR artifact is missing")
    attempts = ([str(executable.resolve()), "dump", "-s", tpr], [str(executable.resolve()), "check", "-s1", tpr])
    results = []
    for command in attempts:
        result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=timeout, check=False)
        results.append({"command": command, "exit_code": result.returncode})
        if result.returncode == 0:
            return {
                "passed": True,
                "method": command[1],
                "attempts": results,
                "tpr": artifact_identity(workdir, tpr, "tpr"),
                "production_ready": False,
                "no_mdrun": True,
            }
    raise StageContractError("E_TPR_READBACK_FAILED", "no supported TPR readback command succeeded", {"attempts": results})

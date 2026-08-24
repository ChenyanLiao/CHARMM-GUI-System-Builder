from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ...artifacts import artifact_identity
from ...errors import StageContractError


def run_strict_grompp(
    executable: Path,
    workdir: Path,
    *,
    mdp: str,
    coordinates: str,
    topology: str,
    output: str = "strict_preflight.tpr",
    timeout: int = 300,
) -> dict:
    workdir = workdir.resolve()
    command = [str(executable.resolve()), "grompp", "-f", mdp, "-c", coordinates, "-p", topology, "-o", output]
    if any("maxwarn" in token.lower() for token in command):
        raise StageContractError("E_GROMPP_FAILED", "strict grompp must not use -maxwarn")
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=timeout, check=False)
    combined = f"{result.stdout}\n{result.stderr}"
    warnings = len(re.findall(r"(?im)^\s*WARNING\b", combined))
    fatals = len(re.findall(r"(?im)^\s*(?:Fatal error|ERROR)\b", combined))
    output_path = workdir / output
    passed = result.returncode == 0 and warnings == 0 and fatals == 0 and output_path.is_file()
    report = {
        "command": command,
        "exit_code": result.returncode,
        "warning_count": warnings,
        "fatal_count": fatals,
        "strict": True,
        "used_maxwarn": False,
        "passed": passed,
        "output": artifact_identity(workdir, output, "tpr") if output_path.is_file() else None,
        "production_ready": False,
        "no_mdrun": True,
    }
    if not passed:
        raise StageContractError("E_GROMPP_FAILED", "strict grompp did not pass", report)
    return report

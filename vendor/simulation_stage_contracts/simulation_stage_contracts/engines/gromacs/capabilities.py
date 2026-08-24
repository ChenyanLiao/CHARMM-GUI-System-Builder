from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ...canonicalization import sha256_file
from ...errors import StageContractError


def _run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def probe_gromacs(executable: Path, timeout: int = 30) -> dict:
    executable = executable.expanduser().resolve()
    if not executable.is_file():
        raise StageContractError("E_ENGINE_UNSUPPORTED", "GROMACS executable is missing")
    version = _run([str(executable), "--version"], timeout)
    combined = f"{version.stdout}\n{version.stderr}"
    if version.returncode != 0 or "GROMACS" not in combined.upper():
        raise StageContractError("E_ENGINE_UNSUPPORTED", "executable did not identify as GROMACS")
    help_result = _run([str(executable), "help", "commands"], timeout)
    help_text = f"{help_result.stdout}\n{help_result.stderr}"
    match = re.search(r"GROMACS version:\s*([^\s]+)", combined, re.I)
    return {
        "engine": "gromacs",
        "executable": str(executable),
        "executable_sha256": sha256_file(executable),
        "version": match.group(1) if match else "UNKNOWN",
        "version_exit_code": version.returncode,
        "commands": {name: bool(re.search(rf"\b{name}\b", help_text)) for name in ("grompp", "dump", "check")},
        "production_ready": False,
        "no_mdrun": True,
    }

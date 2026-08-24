from __future__ import annotations

import os
from pathlib import Path

from ..errors import StageContractError


class BranchFileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._descriptor: int | None = None

    def __enter__(self) -> "BranchFileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(self._descriptor, str(os.getpid()).encode("ascii"))
            os.fsync(self._descriptor)
        except FileExistsError as exc:
            raise StageContractError("E_CONCURRENT_UPDATE", "branch receipt lock is already held") from exc
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._descriptor is not None:
            os.close(self._descriptor)
            self._descriptor = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ERROR_EXIT_CODES = {
    "E_SCHEMA_UNSUPPORTED": 3,
    "E_SCHEMA_INVALID": 2,
    "E_HASH_MISMATCH": 4,
    "E_EVIDENCE_STALE": 4,
    "E_BRANCH_AMBIGUOUS": 2,
    "E_VENDOR_MISMATCH": 4,
    "E_RECEIPT_LEGACY": 2,
    "E_RECEIPT_SUPERSEDED": 4,
    "E_RECEIPT_CHAIN_INVALID": 4,
    "E_AUTH_MISSING": 2,
    "E_AUTH_EXPIRED": 2,
    "E_ENGINE_UNSUPPORTED": 3,
    "E_ARCHIVE_INVALID": 2,
    "E_ARCHIVE_UNSAFE": 4,
    "E_TOPOLOGY_INVALID": 2,
    "E_GROMPP_FAILED": 2,
    "E_TPR_READBACK_FAILED": 2,
    "E_SEGMENT_MISMATCH": 2,
    "E_PARAMETER_INJECTION_UNVERIFIED": 2,
    "E_PRIVACY_POLICY_FAILED": 5,
    "E_CONCURRENT_UPDATE": 6,
    "E_INTERNAL": 7,
}


@dataclass
class StageContractError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.code not in ERROR_EXIT_CODES:
            self.code = "E_INTERNAL"
        super().__init__(self.message)

    @property
    def exit_code(self) -> int:
        return ERROR_EXIT_CODES[self.code]

    def as_dict(self) -> dict[str, Any]:
        return {
            "success": False,
            "error_code": self.code,
            "message": self.message,
            "details": self.details or {},
        }


def result_envelope(command: str, success: bool, **values: Any) -> dict[str, Any]:
    return {"command": command, "success": success, **values}

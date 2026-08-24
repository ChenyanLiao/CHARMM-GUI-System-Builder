from __future__ import annotations

from typing import Any

from ..errors import StageContractError


def require_branch_identity(record: dict[str, Any]) -> tuple[str, str, int]:
    pipeline_id = str(record.get("pipeline_id", "")).strip()
    branch_id = str(record.get("branch_id", "")).strip()
    revision = record.get("revision")
    if not pipeline_id or not branch_id or not isinstance(revision, int) or revision < 1:
        raise StageContractError("E_SCHEMA_INVALID", "pipeline_id, branch_id, and positive revision are required")
    return pipeline_id, branch_id, revision


def require_same_branch(*records: dict[str, Any]) -> tuple[str, str]:
    identities = {(str(item.get("pipeline_id", "")), str(item.get("branch_id", ""))) for item in records}
    if len(identities) != 1 or ("", "") in identities:
        raise StageContractError("E_BRANCH_AMBIGUOUS", "records do not bind one exact pipeline branch")
    return next(iter(identities))

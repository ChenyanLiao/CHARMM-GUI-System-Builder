"""Staged approval records and scoped execution authorizations."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .schema import SCHEMA_VERSION, SchemaError, assert_no_secret_fields


VALID_APPROVAL_ORIGINS = {
    "local_os_confirmed",
    "preauthorized_signed_contract",
    "remote_user_confirmed",
}
INVALID_APPROVAL_ORIGIN = "agent_generated"
SIGNATURE_FIELD = "authorization_hmac_sha256"


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _signature_payload(authorization: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(authorization)
    payload.pop(SIGNATURE_FIELD, None)
    return payload


def sign_authorization(authorization: dict[str, Any], signing_key: bytes) -> str:
    return hmac.new(
        signing_key,
        canonical_json(_signature_payload(authorization)).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def mint_authorization(
    *,
    contract_sha256: str,
    allowed_actions: list[str],
    expires_at: str,
    signing_key: bytes,
    approval_origin: str,
    max_submissions: int = 1,
    authorization_id: str = "",
) -> dict[str, Any]:
    if approval_origin not in VALID_APPROVAL_ORIGINS:
        raise SchemaError(f"invalid approval origin: {approval_origin}")
    if max_submissions < 0:
        raise SchemaError("max_submissions cannot be negative")
    authorization = {
        "schema_version": SCHEMA_VERSION,
        "authorization_id": authorization_id,
        "contract_sha256": contract_sha256,
        "allowed_actions": sorted(set(allowed_actions)),
        "expires_at": expires_at,
        "max_submissions": max_submissions,
        "approval_origin": approval_origin,
        "production_ready": False,
        "no_mdrun": True,
    }
    assert_no_secret_fields(authorization)
    authorization[SIGNATURE_FIELD] = sign_authorization(authorization, signing_key)
    return authorization


def verify_authorization(
    authorization: dict[str, Any],
    *,
    signing_key: bytes,
    contract_sha256: str,
    action: str,
    now: datetime | None = None,
    side_effecting_submission: bool = False,
    submissions_used: int = 0,
) -> tuple[bool, str]:
    assert_no_secret_fields(authorization)
    origin = authorization.get("approval_origin")
    if origin not in VALID_APPROVAL_ORIGINS:
        return False, "approval origin is not trusted"
    if authorization.get("contract_sha256") != contract_sha256:
        return False, "contract hash mismatch"
    signature = authorization.get(SIGNATURE_FIELD)
    expected = sign_authorization(authorization, signing_key)
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        return False, "authorization integrity check failed"
    current = now or datetime.now(timezone.utc)
    if current.astimezone(timezone.utc) >= _parse_timestamp(
        str(authorization.get("expires_at", ""))
    ):
        return False, "authorization expired"
    if action not in authorization.get("allowed_actions", []):
        return False, "action is outside authorization scope"
    if side_effecting_submission:
        maximum = int(authorization.get("max_submissions", 0))
        if submissions_used >= maximum:
            return False, "submission allowance exhausted"
    return True, "authorized"


def append_approval(path: Path, event: dict[str, Any]) -> None:
    assert_no_secret_fields(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

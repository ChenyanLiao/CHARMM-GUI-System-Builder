"""Stage 2 record-specific schema constraints."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


BUILD_CONTRACT_SCHEMA_VERSION = "2.2"
RUN_REQUEST_SCHEMA_VERSION = "2.1"
DECISION_REGISTER_SCHEMA_VERSION = "2.1"
CAPABILITY_REGISTRY_SCHEMA_VERSION = "2.1"
RULE_PACK_SCHEMA_VERSION = "2.1"
APPROVAL_RECORD_SCHEMA_VERSION = "2.1"
EXECUTION_PLAN_SCHEMA_VERSION = "2.1"

# Backward-compatible alias for v2.1 record types. New code must use the
# record-specific constants above.
SCHEMA_VERSION = RUN_REQUEST_SCHEMA_VERSION

PROHIBITED_SECRET_KEYS = {
    "apikey",
    "auth",
    "authorization",
    "password",
    "passwd",
    "cookie",
    "cookies",
    "credential",
    "token",
    "jwt",
    "csrf",
    "private_key",
    "secret_key",
    "session",
    "sessionid",
    "session_id",
    "session_token",
    "session_cookie",
    "set_cookie",
    "mfa_code",
    "captcha",
    "captcha_response",
    "otp",
    "api_key",
    "secret",
}


class SchemaError(ValueError):
    """Raised when a v2.1 record violates a safety or structural rule."""


def normalized_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_")


def is_secret_key(value: object) -> bool:
    key = normalized_key(value)
    secret_suffixes = ("_password", "_token", "_secret")
    return key in PROHIBITED_SECRET_KEYS or key.endswith(secret_suffixes)


def assert_no_secret_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if is_secret_key(key):
                raise SchemaError(f"prohibited secret field at {path}.{key}")
            assert_no_secret_fields(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, item in enumerate(value):
            assert_no_secret_fields(item, f"{path}[{index}]")


def require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaError(f"{label} must be a mapping")
    return value


def require_fields(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise SchemaError(f"{label} missing required fields: {', '.join(missing)}")


def require_schema_version(value: Mapping[str, Any], expected: str) -> None:
    if str(value.get("schema_version", "")) != expected:
        raise SchemaError(
            f"schema_version must be {expected!r}, got "
            f"{value.get('schema_version')!r}"
        )

"""Sanitized append-only evidence records."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .schema import (
    SCHEMA_VERSION,
    assert_no_secret_fields,
    is_secret_key,
    normalized_key,
)


REDACTED = "[REDACTED]"
LOGIN_ACTIONS = {"login", "authenticate", "mfa", "captcha", "account_challenge"}
FIELD_NAME_KEYS = {"field", "id", "key", "name"}
FIELD_VALUE_KEYS = {"content", "default_value", "value"}
INLINE_SECRET_PATTERN = re.compile(
    r"(?i)\b(password|passwd|token|jwt|csrf|session(?:id|_id|_token|_cookie)?|"
    r"cookie|authorization|api[_-]?key|private[_-]?key|secret)\b"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[^\s,;]+")


def _redact_url(value: str) -> str:
    if not value.lower().startswith(("http://", "https://")):
        return value
    parsed = urlsplit(value)
    query = [
        (key, REDACTED if is_secret_key(key) else item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    hostname = parsed.hostname or ""
    netloc = hostname
    if parsed.port:
        netloc = f"{hostname}:{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, urlencode(query), ""))


def _redact_text(value: str) -> str:
    value = BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    return INLINE_SECRET_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}", value
    )


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        field_name = next(
            (
                item
                for key, item in value.items()
                if normalized_key(key) in FIELD_NAME_KEYS
            ),
            "",
        )
        secret_field = is_secret_key(field_name)
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            normalized = normalized_key(key)
            if is_secret_key(key) or (
                secret_field and normalized in FIELD_VALUE_KEYS
            ):
                redacted[f"{normalized_key(key)}_redacted"] = REDACTED
            else:
                redacted[str(key)] = redact(item)
        return redacted
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _redact_url(_redact_text(value))
    return value


def make_event(**fields: Any) -> dict[str, Any]:
    event = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **redact(fields),
    }
    assert_no_secret_fields(event)
    return event


def make_page_event(
    *,
    action: str,
    page_fields: dict[str, Any] | None = None,
    screenshot_path: str = "",
    **fields: Any,
) -> dict[str, Any]:
    """Create page evidence while suppressing the entire login capture surface."""

    if action.strip().lower() in LOGIN_ACTIONS:
        return make_event(
            action=action,
            capture_suppressed=True,
            page_fields={},
            screenshot_path="",
            **fields,
        )
    return make_event(
        action=action,
        capture_suppressed=False,
        page_fields=page_fields or {},
        screenshot_path=screenshot_path,
        **fields,
    )


def append_event(path: Path, event: dict[str, Any]) -> None:
    assert_no_secret_fields(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

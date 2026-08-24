from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


SECRET_MARKERS = (
    "authorization",
    "cookie",
    "csrf",
    "password",
    "private_key",
    "session",
    "token",
)


def _secret_key(key: str) -> bool:
    normalized = key.casefold().replace("-", "_")
    if normalized.endswith("_redacted"):
        return False
    return any(marker in normalized for marker in SECRET_MARKERS)


def sanitize_event(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            sanitized[f"{key}_redacted" if _secret_key(str(key)) else key] = (
                "[REDACTED]" if _secret_key(str(key)) else sanitize_event(item)
            )
        return sanitized
    if isinstance(value, list):
        return [sanitize_event(item) for item in value]
    return deepcopy(value)


def append_event(path: Path, event: dict) -> dict:
    sanitized = sanitize_event(event)
    payload = (json.dumps(sanitized, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return sanitized

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Iterable


def canonical_json_bytes(value: Any, exclude_top_level: Iterable[str] = ()) -> bytes:
    normalized = deepcopy(value)
    if isinstance(normalized, dict):
        for key in exclude_top_level:
            normalized.pop(key, None)
    return json.dumps(
        normalized,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

from __future__ import annotations

import json
import os
from pathlib import Path

from ..canonicalization import sha256_data
from ..errors import StageContractError


def read_chain(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError
                events.append(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt chain cannot be parsed") from exc
    return events


def verify_chain(events: list[dict]) -> bool:
    previous_event: str | None = None
    branch_revisions: dict[tuple[str, str], int] = {}
    branch_receipts: dict[tuple[str, str], str | None] = {}
    for event in events:
        if event.get("previous_event_sha256") != previous_event:
            raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt event chain link mismatch")
        actual = sha256_data(event, exclude_top_level=("event_sha256",))
        if event.get("event_sha256") != actual:
            raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt event hash mismatch")
        branch = (str(event.get("pipeline_id", "")), str(event.get("branch_id", "")))
        expected_revision = branch_revisions.get(branch, 0) + 1
        if event.get("revision") != expected_revision:
            raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt branch revision is not sequential")
        if event.get("previous_receipt_sha256") != branch_receipts.get(branch):
            raise StageContractError("E_RECEIPT_CHAIN_INVALID", "receipt supersession link mismatch")
        branch_revisions[branch] = expected_revision
        branch_receipts[branch] = str(event.get("receipt_sha256"))
        previous_event = actual
    return True


def current_event(events: list[dict], pipeline_id: str, branch_id: str) -> dict | None:
    for event in reversed(events):
        if event.get("pipeline_id") == pipeline_id and event.get("branch_id") == branch_id:
            return event
    return None


def append_chain_event(path: Path, event: dict) -> dict:
    events = read_chain(path)
    verify_chain(events)
    previous = events[-1].get("event_sha256") if events else None
    value = dict(event)
    value["record_type"] = "receipt-chain-event"
    value["schema_version"] = "1.0"
    value["previous_event_sha256"] = previous
    value["event_sha256"] = sha256_data(value)
    payload = (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    verify_chain([*events, value])
    return value

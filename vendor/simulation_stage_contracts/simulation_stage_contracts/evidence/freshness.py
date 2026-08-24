from __future__ import annotations


def evidence_freshness(index: dict) -> str:
    nodes = index.get("nodes", [])
    if not nodes:
        return "UNKNOWN"
    return "STALE" if any(node.get("freshness") != "FRESH" for node in nodes) else "FRESH"

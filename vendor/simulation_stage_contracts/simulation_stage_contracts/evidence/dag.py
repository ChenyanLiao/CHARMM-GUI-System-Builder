from __future__ import annotations

from copy import deepcopy

from ..canonicalization import sha256_data
from ..errors import StageContractError


def _topological_order(nodes: dict[str, dict]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise StageContractError("E_SCHEMA_INVALID", "evidence dependency cycle detected")
        if node_id not in nodes:
            raise StageContractError("E_SCHEMA_INVALID", f"unknown evidence dependency: {node_id}")
        visiting.add(node_id)
        for dependency in nodes[node_id].get("depends_on", []):
            visit(str(dependency))
        visiting.remove(node_id)
        visited.add(node_id)
        order.append(node_id)

    for identifier in sorted(nodes):
        visit(identifier)
    return order


def build_evidence_index(raw_nodes: list[dict]) -> dict:
    nodes: dict[str, dict] = {}
    for raw in raw_nodes:
        node = deepcopy(raw)
        identifier = str(node.get("id", "")).strip()
        recorded = str(node.get("sha256", ""))
        if not identifier or len(recorded) != 64:
            raise StageContractError("E_SCHEMA_INVALID", "evidence nodes require id and SHA-256")
        if identifier in nodes:
            raise StageContractError("E_SCHEMA_INVALID", f"duplicate evidence id: {identifier}")
        node["depends_on"] = sorted(str(value) for value in node.get("depends_on", []))
        nodes[identifier] = node

    order = _topological_order(nodes)
    stale: dict[str, bool] = {}
    normalized: list[dict] = []
    for identifier in order:
        node = nodes[identifier]
        current = node.get("current_sha256")
        direct_stale = current is not None and str(current) != str(node["sha256"])
        dependency_stale = any(stale[dependency] for dependency in node["depends_on"])
        stale[identifier] = direct_stale or dependency_stale
        node["freshness"] = "STALE" if stale[identifier] else "FRESH"
        normalized.append(node)

    index = {
        "record_type": "evidence-index",
        "schema_version": "1.0",
        "nodes": normalized,
    }
    index["root_sha256"] = sha256_data(index)
    return index


def verify_evidence_index(index: dict) -> bool:
    expected = index.get("root_sha256")
    actual = sha256_data(index, exclude_top_level=("root_sha256",))
    if expected != actual:
        raise StageContractError("E_HASH_MISMATCH", "evidence index root hash mismatch")
    rebuilt = build_evidence_index(
        [
            {key: value for key, value in node.items() if key != "freshness"}
            for node in index.get("nodes", [])
        ]
    )
    if rebuilt["root_sha256"] != expected:
        raise StageContractError("E_HASH_MISMATCH", "evidence index is not canonical")
    if any(node.get("freshness") != "FRESH" for node in index.get("nodes", [])):
        raise StageContractError("E_EVIDENCE_STALE", "evidence index contains stale nodes")
    return True

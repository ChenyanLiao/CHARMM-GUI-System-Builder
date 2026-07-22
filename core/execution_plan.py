"""Derive immutable execution route and maturity from reviewed registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .capabilities import CapabilityRegistry
from .io import load_structured
from .schema import SCHEMA_VERSION, SchemaError


BUILDER_CAPABILITIES = {
    "pdb_reader": "browser.pdb_reader",
    "ligand_reader": "browser.ligand_reader",
    "membrane_builder": "browser.membrane_builder",
    "solution_builder": "browser.solution_builder",
    "quick_bilayer": "api.quick_bilayer",
}
MODULE_MATURITY_KEYS = {
    "pdb_reader": "pdb_reader_submission",
    "ligand_reader": "ligand_reader_submission",
    "membrane_builder": "membrane_builder_submission",
    "solution_builder": "solution_builder_submission",
    "quick_bilayer": "official_api_quick_bilayer",
    "gromacs": "gromacs_package_validation",
}


def _maturity_map(root: Path) -> dict[str, str]:
    registry = load_structured(root / "community/MODULE_MATURITY_REGISTRY.json")
    if str(registry.get("schema_version")) != SCHEMA_VERSION:
        raise SchemaError("module maturity registry schema_version must be 2.1")
    return {
        str(row["module"]): str(row["maturity"])
        for row in registry.get("modules", [])
    }


def derive_execution_plan(
    root: Path,
    *,
    builder: str,
    active_modules: list[str],
) -> dict[str, Any]:
    try:
        capability_id = BUILDER_CAPABILITIES[builder]
    except KeyError as exc:
        raise SchemaError(f"no reviewed execution capability for builder: {builder}") from exc
    capability = CapabilityRegistry.from_file(
        root / "rules/capabilities/official_api.json"
    ).get(capability_id)
    maturity = _maturity_map(root)
    module_levels: dict[str, str] = {
        "guided_decision_and_contracts": maturity["guided_decision_and_contracts"]
    }
    for module in active_modules:
        key = MODULE_MATURITY_KEYS.get(module)
        if key:
            if key not in maturity:
                raise SchemaError(f"module maturity is not registered: {key}")
            module_levels[module] = maturity[key]
    return {
        "capability_id": capability.capability_id,
        "execution_route": capability.route,
        "route_maturity": capability.maturity,
        "module_maturity": module_levels,
    }

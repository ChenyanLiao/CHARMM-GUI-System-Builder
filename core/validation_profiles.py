"""Derive output expectations from a locked v2.1 build contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import validate_contract


WATER_COMPONENTS = {"TIP3P": "TIP3"}


@dataclass(frozen=True)
class ValidationExpectations:
    expected_components: tuple[str, ...]
    require_ligand: bool
    ligand_name: str
    expected_ligand_charge: float | None
    expectation_errors: tuple[str, ...]


def _lipid_names(composition: Any) -> list[str]:
    if not isinstance(composition, str) or not composition:
        return []
    names = composition.split("=", 1)[0]
    return [item for item in names.split(":") if item]


def _ion_names(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return [item for item in value.replace(":", "/").split("/") if item]


def expectations_from_contract(contract: dict[str, Any]) -> ValidationExpectations:
    validate_contract(contract, require_locked=True)
    expected = contract.get("expected_output") or {}
    parameters = contract.get("parameters") or {}
    components = list(expected.get("components") or [])
    components.extend(expected.get("protein_segments") or [])

    for key in ("membrane.upper_leaflet", "membrane.lower_leaflet"):
        components.extend(_lipid_names(parameters.get(key)))
    components.extend(_ion_names(parameters.get("membrane.ions.internal_names")))
    water = WATER_COMPONENTS.get(str(parameters.get("membrane.water_model", "")))
    if water:
        components.append(water)

    ligand = expected.get("ligand") or {}
    ligand_name = str(ligand.get("residue_name") or "LIG")
    require_ligand = bool(ligand.get("required", False))
    if require_ligand:
        components.append(ligand_name)
    charge = ligand.get("formal_charge")
    expected_charge = float(charge) if charge is not None else None
    unique_components = tuple(dict.fromkeys(str(item) for item in components))
    errors: list[str] = []
    if not unique_components:
        errors.append(
            "locked contract does not declare or derive any expected output components"
        )

    return ValidationExpectations(
        expected_components=unique_components,
        require_ligand=require_ligand,
        ligand_name=ligand_name,
        expected_ligand_charge=expected_charge,
        expectation_errors=tuple(errors),
    )

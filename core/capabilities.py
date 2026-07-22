"""Versioned CHARMM-GUI transport capability registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import load_structured
from .schema import SCHEMA_VERSION, SchemaError, assert_no_secret_fields


VALID_ROUTES = {"official_api", "audited_browser", "validation_only", "unsupported"}
VALID_MATURITY = {
    "Stable",
    "Beta",
    "Browser-Assisted",
    "Validation-Only",
    "Unsupported",
}


@dataclass(frozen=True)
class Capability:
    capability_id: str
    module: str
    action: str
    route: str
    maturity: str
    method: str = ""
    endpoint: str = ""
    official_source: str = ""
    last_verified: str = ""
    side_effecting: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Capability":
        assert_no_secret_fields(value)
        capability = cls(**value)
        if capability.route not in VALID_ROUTES:
            raise SchemaError(f"invalid capability route: {capability.route}")
        if capability.maturity not in VALID_MATURITY:
            raise SchemaError(f"invalid capability maturity: {capability.maturity}")
        if capability.route == "official_api":
            if not capability.endpoint.startswith("https://charmm-gui.org/api/"):
                raise SchemaError(
                    f"official API capability has invalid endpoint: {capability.endpoint}"
                )
            if not capability.official_source.startswith(
                "https://www.charmm-gui.org/?doc=api"
            ):
                raise SchemaError("official API capability lacks official documentation")
        return capability


class CapabilityRegistry:
    def __init__(self, capabilities: list[Capability]):
        self._items = {item.capability_id: item for item in capabilities}
        if len(self._items) != len(capabilities):
            raise SchemaError("duplicate capability_id")

    @classmethod
    def from_file(cls, path: Path) -> "CapabilityRegistry":
        data = load_structured(path)
        if str(data.get("schema_version", "")) != SCHEMA_VERSION:
            raise SchemaError("capability registry schema_version must be 2.1")
        return cls([Capability.from_dict(item) for item in data["capabilities"]])

    def get(self, capability_id: str) -> Capability:
        try:
            return self._items[capability_id]
        except KeyError as exc:
            raise SchemaError(f"unknown capability: {capability_id}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "capabilities": [item.__dict__ for item in self._items.values()],
        }

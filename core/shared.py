"""Load and verify the vendored simulation-stage-contracts snapshot."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from .schema import SchemaError


ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = ROOT / "vendor" / "simulation_stage_contracts"
VENDOR_MANIFEST = ROOT / "VENDOR_MANIFEST.json"


def verify_vendor_integrity() -> dict:
    manifest = json.loads(VENDOR_MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for entry in manifest.get("files", []):
        path = VENDOR_ROOT / entry["path"]
        if not path.is_file():
            mismatches.append({"path": entry["path"], "reason": "missing"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"] or path.stat().st_size != entry["size"]:
            mismatches.append({"path": entry["path"], "reason": "identity_mismatch"})
    if mismatches:
        raise SchemaError(f"vendored shared core failed integrity verification: {len(mismatches)} file(s)")
    return {
        "status": "PASS",
        "package_version": manifest["package_version"],
        "tree_sha256": manifest["tree_sha256"],
        "file_count": len(manifest["files"]),
    }


def activate_vendor() -> Path:
    verify_vendor_integrity()
    value = str(VENDOR_ROOT)
    if value not in sys.path:
        sys.path.insert(0, value)
    return VENDOR_ROOT

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Summarize GROMACS topol.top molecule counts from a file or archive."""

from __future__ import annotations

import argparse
import json
import re
import tarfile
from pathlib import Path


def parse_molecules(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    in_molecules = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("["):
            in_molecules = bool(re.match(r"\[\s*molecules\s*\]", line, re.I))
            continue
        if in_molecules:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    out[parts[0]] = int(parts[1])
                except ValueError:
                    pass
    return out


def read_topol(path: Path) -> tuple[str, str]:
    if tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as tf:
            members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith("gromacs/topol.top")]
            if not members:
                members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith("topol.top")]
            if not members:
                raise SystemExit("topol.top not found in archive")
            fh = tf.extractfile(members[0])
            if fh is None:
                raise SystemExit("Could not read topol.top")
            return members[0].name, fh.read().decode("utf-8", errors="replace")
    return str(path), path.read_text(errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    name, text = read_topol(args.path.expanduser().resolve())
    molecules = parse_molecules(text)
    if args.json:
        print(json.dumps({"topol": name, "molecules": molecules}, indent=2, ensure_ascii=False))
    else:
        print(f"topol: {name}")
        for key, value in molecules.items():
            print(f"{key}\\t{value}")


if __name__ == "__main__":
    main()

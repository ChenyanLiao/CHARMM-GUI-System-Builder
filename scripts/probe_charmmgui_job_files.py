#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
# Additional terms: see ADDITIONAL_TERMS.md.
"""Read-only probe for expected CHARMM-GUI uploaded job files."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


DEFAULT_FILES = [
    "step1_pdbreader.out",
    "step2_orient.pdb",
    "step3_packing.out",
    "step3_packing_head.psf",
    "step3_packing_head.crd",
    "step4_lipid.out",
    "step5_assembly.psf",
    "step5_assembly.crd",
    "step5_assembly.pdb",
    "step5_input.out",
    "gromacs/step5_input.gro",
    "gromacs/topol.top",
    "gromacs/index.ndx",
    "gromacs/step6.0_minimization.mdp",
    "gromacs/step6.1_equilibration.mdp",
    "gromacs/step7_production.mdp",
]


def probe(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {
                "url": url,
                "status": resp.status,
                "content_length": resp.headers.get("Content-Length"),
                "last_modified": resp.headers.get("Last-Modified"),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": exc.code, "content_length": None, "last_modified": None, "error": str(exc)}
    except Exception as exc:
        return {"url": url, "status": None, "content_length": None, "last_modified": None, "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jobid")
    parser.add_argument("--base-url", default="https://www.charmm-gui.org/uploaded_pdb")
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    rows = []
    for name in args.files:
        url = f"{args.base_url.rstrip('/')}/{args.jobid}/{name}"
        rows.append(probe(url))
    report = {"timestamp": datetime.now().isoformat(), "jobid": args.jobid, "rows": rows}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()

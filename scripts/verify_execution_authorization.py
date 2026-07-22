#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Verify a scoped execution authorization without exposing its signing key."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.approvals import verify_authorization  # noqa: E402
from core.contracts import validate_contract  # noqa: E402
from core.credentials import CredentialBroker, create_secret_store  # noqa: E402
from core.io import load_structured  # noqa: E402
from core.schema import SchemaError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("--provider", choices=("macos-keychain", "system-keyring"), required=True)
    parser.add_argument("--signing-ref", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--submissions-used", type=int, default=0)
    parser.add_argument("--side-effecting-submission", action="store_true")
    args = parser.parse_args()
    try:
        contract = load_structured(args.contract)
        validate_contract(contract, require_locked=True)
        signing_key = CredentialBroker(
            create_secret_store(args.provider)
        ).get_signing_key(args.signing_ref)
        ok, reason = verify_authorization(
            load_structured(args.authorization),
            signing_key=signing_key,
            contract_sha256=contract["contract_sha256"],
            action=args.action,
            side_effecting_submission=args.side_effecting_submission,
            submissions_used=args.submissions_used,
        )
        print(json.dumps({"authorized": ok, "reason": reason}, indent=2))
        return 0 if ok else 2
    except (SchemaError, OSError, ValueError) as exc:
        print(json.dumps({"authorized": False, "reason": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

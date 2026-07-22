#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Mint a signed, time-limited authorization after local confirmation."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.approvals import mint_authorization  # noqa: E402
from core.contracts import validate_contract  # noqa: E402
from core.credentials import CredentialBroker, create_secret_store  # noqa: E402
from core.io import load_structured, write_json  # noqa: E402
from core.schema import SchemaError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--provider", choices=("macos-keychain", "system-keyring"), required=True)
    parser.add_argument("--signing-ref", required=True)
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--allow-action", action="append", required=True)
    parser.add_argument("--max-submissions", type=int, default=1)
    args = parser.parse_args()

    try:
        if not sys.stdin.isatty():
            raise SchemaError("authorization minting requires an interactive terminal")
        contract = load_structured(args.contract)
        validate_contract(contract, require_locked=True)
        prompt = f"APPROVE {contract['contract_sha256'][:12]}"
        if input(f"Type '{prompt}' to authorize: ").strip() != prompt:
            raise SchemaError("authorization confirmation did not match")
        broker = CredentialBroker(create_secret_store(args.provider))
        authorization = mint_authorization(
            contract_sha256=contract["contract_sha256"],
            allowed_actions=args.allow_action,
            expires_at=args.expires_at,
            signing_key=broker.get_signing_key(args.signing_ref),
            approval_origin="local_os_confirmed",
            max_submissions=args.max_submissions,
            authorization_id=str(uuid.uuid4()),
        )
        write_json(args.output, authorization)
        print(args.output)
        return 0
    except (SchemaError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

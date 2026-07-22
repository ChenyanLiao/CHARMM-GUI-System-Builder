#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Interactively manage local CHARMM-GUI credential-vault references."""

from __future__ import annotations

import argparse
import getpass
import secrets
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.credentials import (  # noqa: E402
    Credential,
    CredentialBroker,
    create_secret_store,
)
from core.schema import SchemaError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("macos-keychain", "system-keyring"),
        required=True,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    store = subparsers.add_parser("store-credential")
    store.add_argument("--reference", default="")
    store.add_argument("--account", default="")

    probe = subparsers.add_parser("probe")
    probe.add_argument("reference")
    probe.add_argument("--kind", choices=("credential", "signing-key"), required=True)

    delete = subparsers.add_parser("delete")
    delete.add_argument("reference")

    signing = subparsers.add_parser("create-signing-key")
    signing.add_argument("--reference", default="")

    args = parser.parse_args()
    try:
        broker = CredentialBroker(create_secret_store(args.provider))
        if args.command == "store-credential":
            if not sys.stdin.isatty():
                raise SchemaError("credential storage requires an interactive terminal")
            reference = args.reference or f"credential-{uuid.uuid4()}"
            account = args.account or input("CHARMM-GUI account: ").strip()
            password = getpass.getpass("CHARMM-GUI password: ")
            confirmation = getpass.getpass("Confirm password: ")
            if not account or not password or password != confirmation:
                raise SchemaError("account is empty or passwords do not match")
            broker.store_credential(reference, Credential(account, password))
            print(reference)
            return 0
        if args.command == "create-signing-key":
            if not sys.stdin.isatty():
                raise SchemaError("signing-key creation requires an interactive terminal")
            reference = args.reference or f"authorization-signing-{uuid.uuid4()}"
            broker.store_signing_key(reference, secrets.token_bytes(32))
            print(reference)
            return 0
        if args.command == "probe":
            if args.kind == "credential":
                broker.get_credential(args.reference)
            else:
                broker.get_signing_key(args.reference)
            print("available")
            return 0
        broker.delete(args.reference)
        print("deleted")
        return 0
    except (SchemaError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

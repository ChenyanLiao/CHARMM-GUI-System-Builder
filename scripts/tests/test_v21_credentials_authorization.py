from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.credentials import (  # noqa: E402
    Credential,
    CredentialBroker,
    InMemorySecretStore,
    create_secret_store,
)
from core.schema import SchemaError  # noqa: E402


class CredentialBrokerTests(unittest.TestCase):
    def test_memory_provider_round_trips_without_serialized_output(self) -> None:
        store = InMemorySecretStore()
        broker = CredentialBroker(store)
        broker.store_credential(
            "credential-ref", Credential("user@example.invalid", "fictional-password")
        )
        credential = broker.get_credential("credential-ref")
        self.assertEqual(credential.account, "user@example.invalid")
        self.assertEqual(credential.password, "fictional-password")
        broker.delete("credential-ref")
        with self.assertRaises(SchemaError):
            broker.get_credential("credential-ref")

    def test_signing_key_is_separate_from_credential(self) -> None:
        broker = CredentialBroker(InMemorySecretStore())
        broker.store_signing_key("signing-ref", b"test-key")
        self.assertEqual(broker.get_signing_key("signing-ref"), b"test-key")
        with self.assertRaises(SchemaError):
            broker.get_credential("signing-ref")

    def test_unknown_provider_fails_closed(self) -> None:
        with self.assertRaises(SchemaError):
            create_secret_store("plaintext-file")


if __name__ == "__main__":
    unittest.main()

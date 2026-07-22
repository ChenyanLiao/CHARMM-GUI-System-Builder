"""Credential-vault interfaces that never print stored values."""

from __future__ import annotations

import ctypes
import json
import platform
from dataclasses import dataclass
from typing import Protocol

from .schema import SchemaError


DEFAULT_KEYCHAIN_SERVICE = "io.github.ChenyanLiao.charmm-gui-system-builder"
ERR_SEC_ITEM_NOT_FOUND = -25300


@dataclass(frozen=True)
class Credential:
    account: str
    password: str


class SecretStore(Protocol):
    def set(self, reference: str, value: str) -> None: ...

    def get(self, reference: str) -> str: ...

    def delete(self, reference: str) -> None: ...


class InMemorySecretStore:
    """Test-only provider; values never leave the current process."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def set(self, reference: str, value: str) -> None:
        self._values[reference] = value

    def get(self, reference: str) -> str:
        try:
            return self._values[reference]
        except KeyError as exc:
            raise SchemaError("credential reference was not found") from exc

    def delete(self, reference: str) -> None:
        self._values.pop(reference, None)


class MacOSKeychainSecretStore:
    """Native Security.framework generic-password storage for macOS."""

    def __init__(self, service: str = DEFAULT_KEYCHAIN_SERVICE) -> None:
        if platform.system() != "Darwin":
            raise SchemaError("macOS Keychain provider is available only on macOS")
        self.service = service.encode("utf-8")
        self._security = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/Security.framework/Security"
        )
        self._core_foundation = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        self._configure_functions()

    def _configure_functions(self) -> None:
        security = self._security
        security.SecKeychainFindGenericPassword.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        security.SecKeychainFindGenericPassword.restype = ctypes.c_int32
        security.SecKeychainAddGenericPassword.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        security.SecKeychainAddGenericPassword.restype = ctypes.c_int32
        security.SecKeychainItemModifyAttributesAndData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        security.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
        security.SecKeychainItemDelete.argtypes = [ctypes.c_void_p]
        security.SecKeychainItemDelete.restype = ctypes.c_int32
        security.SecKeychainItemFreeContent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        security.SecKeychainItemFreeContent.restype = ctypes.c_int32
        self._core_foundation.CFRelease.argtypes = [ctypes.c_void_p]

    def _find(self, reference: str) -> tuple[int, ctypes.c_void_p, ctypes.c_void_p, int]:
        account = reference.encode("utf-8")
        length = ctypes.c_uint32()
        data = ctypes.c_void_p()
        item = ctypes.c_void_p()
        status = self._security.SecKeychainFindGenericPassword(
            None,
            len(self.service),
            self.service,
            len(account),
            account,
            ctypes.byref(length),
            ctypes.byref(data),
            ctypes.byref(item),
        )
        return int(status), data, item, int(length.value)

    def set(self, reference: str, value: str) -> None:
        account = reference.encode("utf-8")
        encoded = value.encode("utf-8")
        encoded_buffer = ctypes.create_string_buffer(encoded)
        status, data, item, _ = self._find(reference)
        if data:
            self._security.SecKeychainItemFreeContent(None, data)
        if status == 0:
            try:
                result = self._security.SecKeychainItemModifyAttributesAndData(
                    item, None, len(encoded), ctypes.cast(encoded_buffer, ctypes.c_void_p)
                )
            finally:
                if item:
                    self._core_foundation.CFRelease(item)
        elif status == ERR_SEC_ITEM_NOT_FOUND:
            result = self._security.SecKeychainAddGenericPassword(
                None,
                len(self.service),
                self.service,
                len(account),
                account,
                len(encoded),
                ctypes.cast(encoded_buffer, ctypes.c_void_p),
                None,
            )
        else:
            raise SchemaError(f"macOS Keychain lookup failed with status {status}")
        if int(result) != 0:
            raise SchemaError(f"macOS Keychain write failed with status {int(result)}")

    def get(self, reference: str) -> str:
        status, data, item, length = self._find(reference)
        if status == ERR_SEC_ITEM_NOT_FOUND:
            raise SchemaError("credential reference was not found")
        if status != 0:
            raise SchemaError(f"macOS Keychain lookup failed with status {status}")
        try:
            return ctypes.string_at(data, length).decode("utf-8")
        finally:
            if data:
                self._security.SecKeychainItemFreeContent(None, data)
            if item:
                self._core_foundation.CFRelease(item)

    def delete(self, reference: str) -> None:
        status, data, item, _ = self._find(reference)
        if data:
            self._security.SecKeychainItemFreeContent(None, data)
        if status == ERR_SEC_ITEM_NOT_FOUND:
            return
        if status != 0:
            raise SchemaError(f"macOS Keychain lookup failed with status {status}")
        try:
            result = self._security.SecKeychainItemDelete(item)
        finally:
            if item:
                self._core_foundation.CFRelease(item)
        if int(result) != 0:
            raise SchemaError(f"macOS Keychain delete failed with status {int(result)}")


class PythonKeyringSecretStore:
    """Optional Secret Service/keyring provider for non-macOS systems."""

    def __init__(self, service: str = DEFAULT_KEYCHAIN_SERVICE) -> None:
        try:
            import keyring  # type: ignore[import-not-found]
        except ImportError as exc:
            raise SchemaError(
                "system keyring provider requires the optional 'keyring' package"
            ) from exc
        self._keyring = keyring
        self.service = service

    def set(self, reference: str, value: str) -> None:
        self._keyring.set_password(self.service, reference, value)

    def get(self, reference: str) -> str:
        value = self._keyring.get_password(self.service, reference)
        if value is None:
            raise SchemaError("credential reference was not found")
        return value

    def delete(self, reference: str) -> None:
        try:
            self._keyring.delete_password(self.service, reference)
        except self._keyring.errors.PasswordDeleteError:
            return


class CredentialBroker:
    def __init__(self, store: SecretStore) -> None:
        self.store = store

    def store_credential(self, reference: str, credential: Credential) -> None:
        payload = json.dumps(
            {"account": credential.account, "password": credential.password},
            separators=(",", ":"),
        )
        self.store.set(reference, payload)

    def get_credential(self, reference: str) -> Credential:
        try:
            payload = json.loads(self.store.get(reference))
            return Credential(account=payload["account"], password=payload["password"])
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise SchemaError("stored credential payload is invalid") from exc

    def store_signing_key(self, reference: str, value: bytes) -> None:
        self.store.set(reference, value.hex())

    def get_signing_key(self, reference: str) -> bytes:
        try:
            return bytes.fromhex(self.store.get(reference))
        except ValueError as exc:
            raise SchemaError("stored signing key is invalid") from exc

    def delete(self, reference: str) -> None:
        self.store.delete(reference)


def create_secret_store(provider: str) -> SecretStore:
    if provider == "macos-keychain":
        return MacOSKeychainSecretStore()
    if provider == "system-keyring":
        return PythonKeyringSecretStore()
    if provider == "memory-test-only":
        return InMemorySecretStore()
    raise SchemaError(f"unsupported credential provider: {provider}")

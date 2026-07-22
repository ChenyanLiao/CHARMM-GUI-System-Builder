#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Liao Chenyan
# SPDX-License-Identifier: AGPL-3.0-only
"""Use only documented CHARMM-GUI APIs with explicit live-action gates."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.approvals import verify_authorization  # noqa: E402
from core.capabilities import CapabilityRegistry  # noqa: E402
from core.contracts import validate_contract  # noqa: E402
from core.credentials import Credential, CredentialBroker, create_secret_store  # noqa: E402
from core.evidence import redact  # noqa: E402
from core.io import load_structured, write_json, write_json_atomic  # noqa: E402
from core.router import (  # noqa: E402
    ensure_submission_allowed,
    record_submission_success,
    record_submission_uncertain,
    require_existing_job,
)
from core.schema import SchemaError, assert_no_secret_fields  # noqa: E402


REGISTRY_PATH = ROOT / "rules/capabilities/official_api.json"
QUICK_BILAYER_KEYS = {
    "jobid",
    "membrane_only",
    "upper",
    "lower",
    "membtype",
    "margin",
    "wdist",
    "Ion_conc",
    "Ion_type",
    "prot_projection_upper",
    "prot_projection_lower",
    "ppm",
    "topologyIn",
    "heteroatoms",
    "clone_job",
}
QUICK_BILAYER_CONTRACT_FIELDS = {
    "jobid": ("quick_bilayer.source_pdbreader_jobid", "string"),
    "membrane_only": ("quick_bilayer.membrane_only", "boolean"),
    "upper": ("quick_bilayer.upper", "string"),
    "lower": ("quick_bilayer.lower", "string"),
    "margin": ("quick_bilayer.margin_angstrom", "number"),
    "wdist": ("quick_bilayer.water_distance_angstrom", "number"),
    "Ion_conc": ("quick_bilayer.ion_concentration_m", "number"),
    "Ion_type": ("quick_bilayer.ion_type", "string_ci"),
    "prot_projection_upper": (
        "quick_bilayer.protein_projection_upper",
        "boolean",
    ),
    "prot_projection_lower": (
        "quick_bilayer.protein_projection_lower",
        "boolean",
    ),
    "ppm": ("quick_bilayer.ppm", "boolean"),
    "heteroatoms": ("quick_bilayer.heteroatoms", "boolean"),
}


class ApiError(RuntimeError):
    """Sanitized API failure without response bodies or credentials."""


def validate_quick_bilayer_request(value: dict[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(value) - QUICK_BILAYER_KEYS)
    if unknown:
        raise SchemaError(f"unsupported Quick Bilayer parameters: {', '.join(unknown)}")
    if "margin" not in value:
        raise SchemaError("Quick Bilayer requires margin")
    if not ({"upper", "lower"} <= set(value) or value.get("membtype")):
        raise SchemaError("provide upper/lower compositions or membtype")
    membrane_only = str(value.get("membrane_only", "")).lower() in {
        "true",
        "1",
        "yes",
    }
    if not membrane_only and not value.get("jobid"):
        raise SchemaError("protein Quick Bilayer requests require a PDB Reader jobid")
    return dict(value)


def _normalize_contract_value(value: Any, value_type: str) -> Any:
    if value_type == "boolean":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        raise SchemaError(f"invalid boolean API value: {value!r}")
    if value_type == "number":
        if isinstance(value, bool):
            raise SchemaError(f"invalid numeric API value: {value!r}")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise SchemaError(f"invalid numeric API value: {value!r}") from exc
    normalized = str(value).strip()
    return normalized.lower() if value_type == "string_ci" else normalized


def _normalized_builder(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def validate_request_matches_contract(
    parameters: dict[str, Any], contract: dict[str, Any]
) -> None:
    """Require every live Quick Bilayer field to match the locked contract."""
    validate_contract(contract, require_locked=True)
    if _normalized_builder(contract.get("builder")) != "quick_bilayer":
        raise SchemaError("Quick Bilayer API requires a quick_bilayer build contract")
    if contract.get("capability_id") != "api.quick_bilayer":
        raise SchemaError("build contract is not bound to api.quick_bilayer")
    if contract.get("execution_route") != "official_api":
        raise SchemaError("build contract is not bound to the official API route")

    contract_parameters = contract.get("parameters", {})
    membrane_only = _normalize_contract_value(
        contract_parameters.get("quick_bilayer.membrane_only", False), "boolean"
    )
    if not membrane_only and not contract.get("inputs"):
        raise SchemaError(
            "protein Quick Bilayer contract requires hashed input provenance"
        )
    for api_field, submitted_value in parameters.items():
        binding = QUICK_BILAYER_CONTRACT_FIELDS.get(api_field)
        if binding is None:
            raise SchemaError(
                f"live Quick Bilayer field {api_field!r} has no v2.1 contract binding"
            )
        parameter_id, value_type = binding
        if parameter_id not in contract_parameters:
            raise SchemaError(
                f"live Quick Bilayer field {api_field!r} is absent from the contract"
            )
        expected = _normalize_contract_value(
            contract_parameters[parameter_id], value_type
        )
        actual = _normalize_contract_value(submitted_value, value_type)
        if actual != expected:
            raise SchemaError(
                f"Quick Bilayer field {api_field!r} differs from the locked contract"
            )

    reverse_bindings = {
        parameter_id: api_field
        for api_field, (parameter_id, _value_type) in QUICK_BILAYER_CONTRACT_FIELDS.items()
    }
    missing = sorted(
        reverse_bindings[parameter_id]
        for parameter_id in contract_parameters
        if parameter_id in reverse_bindings
        and reverse_bindings[parameter_id] not in parameters
    )
    if missing:
        raise SchemaError(
            "Quick Bilayer request omits contracted fields: " + ", ".join(missing)
        )


def validate_existing_job_gate(
    *,
    jobid: str,
    action: str,
    contract: dict[str, Any],
    authorization: dict[str, Any],
    signing_key: bytes,
    state: dict[str, Any],
) -> None:
    """Bind a status or download action to one authorized existing job."""
    validate_contract(contract, require_locked=True)
    assert_no_secret_fields(authorization)
    assert_no_secret_fields(state)
    if state.get("contract_sha256") != contract["contract_sha256"]:
        raise SchemaError("run state belongs to a different build contract")
    if str(jobid) != require_existing_job(state):
        raise SchemaError("requested jobid differs from the run-state jobid")
    ok, reason = verify_authorization(
        authorization,
        signing_key=signing_key,
        contract_sha256=contract["contract_sha256"],
        action=action,
    )
    if not ok:
        raise SchemaError(reason)


def request_summary(capability_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    registry = CapabilityRegistry.from_file(REGISTRY_PATH)
    capability = registry.get(capability_id)
    if capability_id == "api.quick_bilayer":
        parameters = validate_quick_bilayer_request(parameters)
    return {
        "capability_id": capability.capability_id,
        "method": capability.method,
        "endpoint": capability.endpoint,
        "maturity": capability.maturity,
        "parameters": parameters,
        "contains_credentials": False,
        "live_request_executed": False,
        "production_ready": False,
        "no_mdrun": True,
    }


class CharmmGuiApiClient:
    def __init__(
        self,
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
        timeout: int = 60,
    ) -> None:
        self._opener = opener
        self._timeout = timeout
        self._jwt: str | None = None

    def _open(self, request: urllib.request.Request) -> Any:
        try:
            return self._opener(request, timeout=self._timeout)
        except urllib.error.HTTPError as exc:
            raise ApiError(f"CHARMM-GUI API returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ApiError("CHARMM-GUI API network request failed") from exc

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_body: dict[str, Any] | None = None,
        form: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Accept": "application/json"}
        data: bytes | None = None
        if json_body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(json_body).encode("utf-8")
        elif form is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            data = urllib.parse.urlencode(form).encode("utf-8")
        if self._jwt:
            headers["Authorization"] = f"Bearer {self._jwt}"
        request = urllib.request.Request(endpoint, data=data, headers=headers, method=method)
        response = self._open(request)
        try:
            payload = response.read()
        except OSError as exc:
            raise ApiError("CHARMM-GUI API response read failed") from exc
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError("CHARMM-GUI API returned invalid JSON") from exc

    def login(self, credential: Credential) -> None:
        result = self._request(
            "POST",
            "https://charmm-gui.org/api/login",
            json_body={"email": credential.account, "password": credential.password},
        )
        token = result.get("token") if isinstance(result, dict) else None
        if not isinstance(token, str) or not token:
            raise ApiError("CHARMM-GUI login response did not contain a token")
        self._jwt = token

    def check_status(self, jobid: str) -> dict[str, Any]:
        endpoint = "https://charmm-gui.org/api/check_status?" + urllib.parse.urlencode(
            {"jobid": jobid}
        )
        return self._request("GET", endpoint)

    def download(self, jobid: str, destination: Path) -> None:
        endpoint = "https://charmm-gui.org/api/download?" + urllib.parse.urlencode(
            {"jobid": jobid}
        )
        destination = destination.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        headers = {"Accept": "application/octet-stream"}
        if self._jwt:
            headers["Authorization"] = f"Bearer {self._jwt}"
        request = urllib.request.Request(endpoint, headers=headers, method="GET")
        response = self._open(request)
        handle, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".partial", dir=destination.parent
        )
        try:
            with os.fdopen(handle, "wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            Path(temporary_name).replace(destination)
        except BaseException:
            Path(temporary_name).unlink(missing_ok=True)
            raise

    def submit_quick_bilayer(
        self, parameters: dict[str, Any], *, authorization_ok: bool
    ) -> dict[str, Any]:
        if not authorization_ok:
            raise SchemaError("Quick Bilayer submission requires verified authorization")
        request = validate_quick_bilayer_request(parameters)
        return self._request(
            "POST",
            "https://charmm-gui.org/api/quick_bilayer",
            form=request,
        )


def _extract_jobid(response: Any) -> str:
    if not isinstance(response, dict):
        return ""
    for key in ("jobid", "jobId", "job_id"):
        value = response.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _safe_response_summary(response: Any, jobid: str) -> dict[str, Any]:
    keys = sorted(str(key) for key in response) if isinstance(response, dict) else []
    summary = {
        "jobid": jobid,
        "response_type": type(response).__name__,
        "response_keys": keys,
    }
    assert_no_secret_fields(summary)
    return summary


def _persist_submission_uncertain(
    *,
    state: dict[str, Any],
    contract_sha256: str,
    state_path: Path,
    reason: str,
) -> None:
    uncertain = record_submission_uncertain(
        state,
        contract_sha256=contract_sha256,
        reason=reason,
    )
    write_json_atomic(state_path, uncertain)


def validate_submission_gate(
    *,
    parameters: dict[str, Any],
    contract: dict[str, Any],
    authorization: dict[str, Any],
    signing_key: bytes,
    state: dict[str, Any],
) -> None:
    """Validate the exact one-submission gate without network access."""
    assert_no_secret_fields(parameters)
    assert_no_secret_fields(authorization)
    assert_no_secret_fields(state)
    validate_quick_bilayer_request(parameters)
    validate_request_matches_contract(parameters, contract)
    ok, reason = verify_authorization(
        authorization,
        signing_key=signing_key,
        contract_sha256=contract["contract_sha256"],
        action="submit_quick_bilayer",
        side_effecting_submission=True,
        submissions_used=int(state.get("submissions_used", 0)),
    )
    if not ok:
        raise SchemaError(reason)
    ensure_submission_allowed(
        state,
        contract_sha256=contract["contract_sha256"],
        authorization_ok=True,
    )


def execute_quick_bilayer_submission(
    *,
    client: CharmmGuiApiClient,
    parameters: dict[str, Any],
    contract: dict[str, Any],
    authorization: dict[str, Any],
    signing_key: bytes,
    state: dict[str, Any],
    state_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Submit once, persisting either a job ID or an uncertain-attempt lock."""
    validate_submission_gate(
        parameters=parameters,
        contract=contract,
        authorization=authorization,
        signing_key=signing_key,
        state=state,
    )

    try:
        response = client.submit_quick_bilayer(parameters, authorization_ok=True)
    except ApiError:
        _persist_submission_uncertain(
            state=state,
            contract_sha256=contract["contract_sha256"],
            state_path=state_path,
            reason=(
                "Quick Bilayer POST outcome is uncertain; inspect existing jobs "
                "before any retry."
            ),
        )
        raise

    jobid = _extract_jobid(response)
    if not jobid:
        _persist_submission_uncertain(
            state=state,
            contract_sha256=contract["contract_sha256"],
            state_path=state_path,
            reason=(
                "Quick Bilayer response contained no jobid; inspect existing jobs "
                "before any retry."
            ),
        )
        raise ApiError("Quick Bilayer response did not contain a jobid")

    updated = record_submission_success(
        state,
        jobid=jobid,
        contract_sha256=contract["contract_sha256"],
    )
    updated.update(
        capability_id="api.quick_bilayer",
        execution_route="official_api",
        module_maturity="Beta",
        authorization_state="verified",
        authorized_actions=list(authorization.get("allowed_actions", [])),
        previous_action="SUBMIT_QUICK_BILAYER",
        next_allowed_action="API_CHECK_STATUS",
        runtime_state="submitted",
    )
    write_json_atomic(state_path, updated)
    return updated, _safe_response_summary(response, jobid)


def execute_status_check(
    *,
    client: CharmmGuiApiClient,
    jobid: str,
    contract: dict[str, Any],
    authorization: dict[str, Any],
    signing_key: bytes,
    state: dict[str, Any],
    state_path: Path,
) -> tuple[dict[str, Any], Any]:
    validate_existing_job_gate(
        jobid=jobid,
        action="api_check_status",
        contract=contract,
        authorization=authorization,
        signing_key=signing_key,
        state=state,
    )
    response = redact(client.check_status(jobid))
    updated = copy.deepcopy(state)
    backend_state = "unknown"
    if isinstance(response, dict):
        backend_state = str(response.get("status", "unknown")).strip().lower()
    updated.update(
        previous_action="API_CHECK_STATUS",
        previous_action_timestamp=datetime.now(timezone.utc).isoformat(),
        backend_state=backend_state,
        next_allowed_action=(
            "API_DOWNLOAD_FINAL_PACKAGE"
            if backend_state in {"complete", "completed", "finished", "done"}
            else "API_CHECK_STATUS"
        ),
    )
    write_json_atomic(state_path, updated)
    return updated, response


def execute_download(
    *,
    client: CharmmGuiApiClient,
    jobid: str,
    destination: Path,
    contract: dict[str, Any],
    authorization: dict[str, Any],
    signing_key: bytes,
    state: dict[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    validate_existing_job_gate(
        jobid=jobid,
        action="api_download_final_package",
        contract=contract,
        authorization=authorization,
        signing_key=signing_key,
        state=state,
    )
    destination = destination.expanduser().resolve()
    client.download(jobid, destination)
    updated = copy.deepcopy(state)
    updated.update(
        previous_action="API_DOWNLOAD_FINAL_PACKAGE",
        previous_action_timestamp=datetime.now(timezone.utc).isoformat(),
        download_state="downloaded_unverified",
        next_allowed_action="INSPECT_DOWNLOAD_ARTIFACT",
    )
    transfer = copy.deepcopy(updated.get("download_transfer") or {})
    transfer.update(state="downloaded_unverified", destination_path=str(destination))
    updated["download_transfer"] = transfer
    write_json_atomic(state_path, updated)
    return updated


def _broker(provider: str) -> CredentialBroker:
    if provider == "memory-test-only":
        raise SchemaError("memory-test-only provider is unavailable from the live CLI")
    return CredentialBroker(create_secret_store(provider))


def _live_client(args: argparse.Namespace) -> CharmmGuiApiClient:
    if not args.allow_live:
        raise SchemaError("live API access requires --allow-live")
    credential = _broker(args.provider).get_credential(args.credential_ref)
    client = CharmmGuiApiClient()
    client.login(credential)
    return client


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("capabilities")

    summary_parser = subparsers.add_parser("quick-bilayer-summary")
    summary_parser.add_argument("request", type=Path)
    summary_parser.add_argument("--json-out", type=Path)

    for name in ("status", "download", "submit-quick-bilayer"):
        live = subparsers.add_parser(name)
        live.add_argument("--provider", choices=("macos-keychain", "system-keyring"), required=True)
        live.add_argument("--credential-ref", required=True)
        live.add_argument("--allow-live", action="store_true")
        live.add_argument("--contract", type=Path, required=True)
        live.add_argument("--authorization", type=Path, required=True)
        live.add_argument("--run-state", type=Path, required=True)
        live.add_argument("--signing-ref", required=True)
        if name in {"status", "download"}:
            live.add_argument("jobid")
        if name == "download":
            live.add_argument("destination", type=Path)
        if name == "submit-quick-bilayer":
            live.add_argument("request", type=Path)
            live.add_argument("--json-out", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "capabilities":
            print(json.dumps(CapabilityRegistry.from_file(REGISTRY_PATH).to_dict(), indent=2))
            return 0
        if args.command == "quick-bilayer-summary":
            report = request_summary("api.quick_bilayer", load_structured(args.request))
            if args.json_out:
                write_json(args.json_out, report)
            else:
                print(json.dumps(report, indent=2))
            return 0

        contract = load_structured(args.contract)
        validate_contract(contract, require_locked=True)
        authorization = load_structured(args.authorization)
        state = load_structured(args.run_state)
        signing_key = _broker(args.provider).get_signing_key(args.signing_ref)
        if args.command == "status":
            validate_existing_job_gate(
                jobid=args.jobid,
                action="api_check_status",
                contract=contract,
                authorization=authorization,
                signing_key=signing_key,
                state=state,
            )
            client = _live_client(args)
            _updated, response = execute_status_check(
                client=client,
                jobid=args.jobid,
                contract=contract,
                authorization=authorization,
                signing_key=signing_key,
                state=state,
                state_path=args.run_state,
            )
            print(json.dumps(response, indent=2))
            return 0
        if args.command == "download":
            validate_existing_job_gate(
                jobid=args.jobid,
                action="api_download_final_package",
                contract=contract,
                authorization=authorization,
                signing_key=signing_key,
                state=state,
            )
            client = _live_client(args)
            execute_download(
                client=client,
                jobid=args.jobid,
                destination=args.destination,
                contract=contract,
                authorization=authorization,
                signing_key=signing_key,
                state=state,
                state_path=args.run_state,
            )
            print(args.destination.expanduser().resolve())
            return 0

        if contract.get("mode") not in {"test_only", "Candidate_Not_For_MD"}:
            raise SchemaError("v2.1 API submission CLI permits only test-only modes")
        parameters = load_structured(args.request)
        validate_submission_gate(
            parameters=parameters,
            contract=contract,
            authorization=authorization,
            signing_key=signing_key,
            state=state,
        )
        client = _live_client(args)
        updated_state, response_summary = execute_quick_bilayer_submission(
            client=client,
            parameters=parameters,
            contract=contract,
            authorization=authorization,
            signing_key=signing_key,
            state=state,
            state_path=args.run_state,
        )
        write_json_atomic(
            args.json_out,
            {
                "response": response_summary,
                "jobid": updated_state["jobid"],
                "contract_sha256": contract["contract_sha256"],
                "production_ready": False,
                "no_mdrun": True,
            },
        )
        print(args.json_out)
        return 0
    except (SchemaError, ApiError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

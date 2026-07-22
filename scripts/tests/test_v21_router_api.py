from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from charmmgui_api_client import (  # noqa: E402
    CharmmGuiApiClient,
    ApiError,
    execute_download,
    execute_quick_bilayer_submission,
    execute_status_check,
    request_summary,
    validate_existing_job_gate,
    validate_quick_bilayer_request,
    validate_request_matches_contract,
)
from core.capabilities import CapabilityRegistry  # noqa: E402
from core.credentials import Credential  # noqa: E402
from core.approvals import mint_authorization  # noqa: E402
from core.contracts import lock_contract  # noqa: E402
from core.io import load_structured, write_json_atomic  # noqa: E402
from core.router import (  # noqa: E402
    ensure_submission_allowed,
    record_submission_success,
    record_submission_uncertain,
    require_existing_job,
    select_capability,
)
from core.schema import SchemaError  # noqa: E402


REGISTRY = ROOT / "rules/capabilities/official_api.json"


class FakeResponse:
    def __init__(self, value: object):
        self.payload = json.dumps(value).encode("utf-8")

    def read(self, size: int = -1) -> bytes:
        if not self.payload:
            return b""
        if size < 0:
            value, self.payload = self.payload, b""
            return value
        value, self.payload = self.payload[:size], self.payload[size:]
        return value


class FakeOpener:
    def __init__(self) -> None:
        self.requests = []

    def __call__(self, request, timeout=0):
        self.requests.append((request, timeout))
        if request.full_url.endswith("/api/login"):
            return FakeResponse({"token": "fictional-jwt-never-logged"})
        if "check_status" in request.full_url:
            return FakeResponse({"status": "running", "lastOutFile": "step3.out"})
        return FakeResponse({"jobid": "9000000001", "submitted": "true"})


def base_state() -> dict:
    return {
        "contract_sha256": "a" * 64,
        "jobid": "",
        "submission_state": "not_submitted",
        "submissions_used": 0,
        "max_submissions": 1,
    }


REQUEST_TO_CONTRACT = {
    "jobid": "quick_bilayer.source_pdbreader_jobid",
    "membrane_only": "quick_bilayer.membrane_only",
    "upper": "quick_bilayer.upper",
    "lower": "quick_bilayer.lower",
    "margin": "quick_bilayer.margin_angstrom",
    "wdist": "quick_bilayer.water_distance_angstrom",
    "Ion_conc": "quick_bilayer.ion_concentration_m",
    "Ion_type": "quick_bilayer.ion_type",
    "prot_projection_upper": "quick_bilayer.protein_projection_upper",
    "prot_projection_lower": "quick_bilayer.protein_projection_lower",
    "ppm": "quick_bilayer.ppm",
    "heteroatoms": "quick_bilayer.heteroatoms",
}


def locked_contract(parameters: dict | None = None) -> dict:
    parameters = parameters or {}
    contract_parameters = {
        REQUEST_TO_CONTRACT[key]: value for key, value in parameters.items()
    }
    return lock_contract(
        {
            "run_id": "test-run",
            "target_id": "test-target",
            "builder": "quick_bilayer",
            "mode": "test_only",
            "inputs": [],
            "parameters": contract_parameters,
            "decision_records": [
                {
                    "parameter_id": parameter_id,
                    "recommended_value": value,
                    "evidence_sources": [],
                    "risk_level": "Contextual",
                    "contract_value": value,
                    "approval_status": "confirmed",
                }
                for parameter_id, value in contract_parameters.items()
            ],
            "capability_id": "api.quick_bilayer",
            "execution_route": "official_api",
            "production_ready": False,
            "no_mdrun": True,
        }
    )


def authorization_for(
    contract: dict,
    key: bytes = b"test-signing-key",
    actions: list[str] | None = None,
) -> dict:
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    return mint_authorization(
        contract_sha256=contract["contract_sha256"],
        allowed_actions=actions or ["submit_quick_bilayer"],
        expires_at=expires.isoformat(),
        signing_key=key,
        approval_origin="preauthorized_signed_contract",
        max_submissions=1,
    )


class CapabilityAndRouterTests(unittest.TestCase):
    def test_registry_contains_only_documented_api_endpoints(self) -> None:
        registry = CapabilityRegistry.from_file(REGISTRY)
        for identifier in (
            "api.login",
            "api.check_status",
            "api.download",
            "api.quick_bilayer",
        ):
            capability = registry.get(identifier)
            self.assertEqual(capability.route, "official_api")
            self.assertTrue(capability.endpoint.startswith("https://charmm-gui.org/api/"))
            self.assertTrue(capability.official_source.startswith("https://www.charmm-gui.org/?doc=api"))

    def test_browser_route_is_explicit(self) -> None:
        capability = select_capability(
            CapabilityRegistry.from_file(REGISTRY), "browser.membrane_builder"
        )
        self.assertEqual(capability.route, "audited_browser")
        self.assertEqual(capability.maturity, "Browser-Assisted")

    def test_submission_requires_authorization(self) -> None:
        with self.assertRaises(SchemaError):
            ensure_submission_allowed(
                base_state(), contract_sha256="a" * 64, authorization_ok=False
            )

    def test_success_persists_job_and_prevents_resubmission(self) -> None:
        state = base_state()
        ensure_submission_allowed(
            state, contract_sha256="a" * 64, authorization_ok=True
        )
        updated = record_submission_success(
            state, jobid="9000000001", contract_sha256="a" * 64
        )
        self.assertEqual(require_existing_job(updated), "9000000001")
        with self.assertRaises(SchemaError):
            ensure_submission_allowed(
                updated, contract_sha256="a" * 64, authorization_ok=True
            )

    def test_uncertain_submission_cannot_be_retried(self) -> None:
        uncertain = record_submission_uncertain(
            base_state(),
            contract_sha256="a" * 64,
            reason="POST response was lost",
        )
        self.assertEqual(uncertain["submission_state"], "submission_uncertain")
        self.assertTrue(uncertain["needs_user_attention"])
        with self.assertRaises(SchemaError):
            ensure_submission_allowed(
                uncertain, contract_sha256="a" * 64, authorization_ok=True
            )


class ApiClientTests(unittest.TestCase):
    def test_quick_bilayer_summary_is_dry_and_redacted(self) -> None:
        report = request_summary(
            "api.quick_bilayer",
            {
                "membrane_only": "true",
                "upper": "POPC:CHL1=70:30",
                "lower": "POPC:CHL1=70:30",
                "margin": 20,
                "Ion_conc": 0.15,
                "Ion_type": "NaCl",
            },
        )
        self.assertFalse(report["live_request_executed"])
        self.assertFalse(report["contains_credentials"])
        self.assertFalse(report["production_ready"])

    def test_protein_request_requires_jobid(self) -> None:
        with self.assertRaises(SchemaError):
            validate_quick_bilayer_request(
                {
                    "upper": "POPC=1",
                    "lower": "POPC=1",
                    "margin": 20,
                }
            )

    def test_client_keeps_token_internal_and_status_works(self) -> None:
        opener = FakeOpener()
        client = CharmmGuiApiClient(opener=opener)
        client.login(Credential("user@example.invalid", "fictional-password"))
        result = client.check_status("9000000001")
        self.assertEqual(result["status"], "running")
        status_request = opener.requests[-1][0]
        self.assertTrue(status_request.get_header("Authorization").startswith("Bearer "))

    def test_quick_bilayer_requires_verified_authorization(self) -> None:
        client = CharmmGuiApiClient(opener=FakeOpener())
        with self.assertRaises(SchemaError):
            client.submit_quick_bilayer(
                {
                    "membrane_only": "true",
                    "upper": "POPC=1",
                    "lower": "POPC=1",
                    "margin": 20,
                },
                authorization_ok=False,
            )

    def test_live_request_must_match_locked_contract(self) -> None:
        parameters = {
            "membrane_only": "true",
            "upper": "POPC:CHL1=70:30",
            "lower": "POPC:CHL1=70:30",
            "margin": 20,
        }
        contract = locked_contract(parameters)
        validate_request_matches_contract(parameters, contract)
        changed = dict(parameters, upper="POPC:CHL1=80:20")
        with self.assertRaisesRegex(SchemaError, "differs from the locked contract"):
            validate_request_matches_contract(changed, contract)

    def test_uncontracted_live_field_is_rejected(self) -> None:
        parameters = {
            "membrane_only": "true",
            "upper": "POPC=1",
            "lower": "POPC=1",
            "margin": 20,
        }
        contract = locked_contract(parameters)
        with self.assertRaisesRegex(SchemaError, "no v2.1 contract binding"):
            validate_request_matches_contract(
                dict(parameters, topologyIn="unreviewed.str"), contract
            )

    def test_protein_quick_bilayer_requires_hashed_input_provenance(self) -> None:
        parameters = {
            "jobid": "9000000000",
            "membrane_only": False,
            "upper": "POPC=1",
            "lower": "POPC=1",
            "margin": 20,
        }
        contract = locked_contract(parameters)
        with self.assertRaisesRegex(SchemaError, "hashed input provenance"):
            validate_request_matches_contract(parameters, contract)

    def test_download_streams_to_atomic_destination(self) -> None:
        payload = b"archive-bytes" * 100

        class BinaryOpener:
            def __call__(self, request, timeout=0):
                response = FakeResponse({})
                response.payload = payload
                return response

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "final.tar"
            CharmmGuiApiClient(opener=BinaryOpener()).download(
                "9000000001", destination
            )
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(list(destination.parent.glob("*.partial")), [])

    def test_status_and_download_are_bound_to_existing_job(self) -> None:
        contract = locked_contract()
        state = base_state()
        state.update(
            contract_sha256=contract["contract_sha256"],
            jobid="9000000001",
            submission_state="submitted",
        )
        authorization = authorization_for(
            contract,
            actions=["api_check_status", "api_download_final_package"],
        )
        validate_existing_job_gate(
            jobid="9000000001",
            action="api_check_status",
            contract=contract,
            authorization=authorization,
            signing_key=b"test-signing-key",
            state=state,
        )
        with self.assertRaisesRegex(SchemaError, "differs from the run-state jobid"):
            validate_existing_job_gate(
                jobid="9000000002",
                action="api_check_status",
                contract=contract,
                authorization=authorization,
                signing_key=b"test-signing-key",
                state=state,
            )

        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "RUN_STATE.json"
            destination = Path(temporary) / "final.tar"
            updated, response = execute_status_check(
                client=CharmmGuiApiClient(opener=FakeOpener()),
                jobid="9000000001",
                contract=contract,
                authorization=authorization,
                signing_key=b"test-signing-key",
                state=state,
                state_path=state_path,
            )
            self.assertEqual(response["status"], "running")
            self.assertEqual(updated["previous_action"], "API_CHECK_STATUS")

            payload = b"archive-bytes"

            class BinaryOpener:
                def __call__(self, request, timeout=0):
                    response = FakeResponse({})
                    response.payload = payload
                    return response

            downloaded = execute_download(
                client=CharmmGuiApiClient(opener=BinaryOpener()),
                jobid="9000000001",
                destination=destination,
                contract=contract,
                authorization=authorization,
                signing_key=b"test-signing-key",
                state=updated,
                state_path=state_path,
            )
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(downloaded["download_state"], "downloaded_unverified")

    def test_submission_persists_jobid_and_redacted_summary(self) -> None:
        parameters = {
            "membrane_only": "true",
            "upper": "POPC=1",
            "lower": "POPC=1",
            "margin": 20,
        }
        contract = locked_contract(parameters)
        state = base_state()
        state["contract_sha256"] = contract["contract_sha256"]
        authorization = authorization_for(contract)
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "RUN_STATE.json"
            updated, summary = execute_quick_bilayer_submission(
                client=CharmmGuiApiClient(opener=FakeOpener()),
                parameters=parameters,
                contract=contract,
                authorization=authorization,
                signing_key=b"test-signing-key",
                state=state,
                state_path=state_path,
            )
            self.assertEqual(updated["jobid"], "9000000001")
            self.assertEqual(load_structured(state_path)["jobid"], "9000000001")
            self.assertEqual(summary["jobid"], "9000000001")
            self.assertNotIn("token", json.dumps(summary).lower())

    def test_missing_jobid_persists_uncertain_and_blocks_retry(self) -> None:
        class MissingJobOpener(FakeOpener):
            def __call__(self, request, timeout=0):
                self.requests.append((request, timeout))
                return FakeResponse({"submitted": "unknown"})

        parameters = {
            "membrane_only": "true",
            "upper": "POPC=1",
            "lower": "POPC=1",
            "margin": 20,
        }
        contract = locked_contract(parameters)
        state = base_state()
        state["contract_sha256"] = contract["contract_sha256"]
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "RUN_STATE.json"
            with self.assertRaises(ApiError):
                execute_quick_bilayer_submission(
                    client=CharmmGuiApiClient(opener=MissingJobOpener()),
                    parameters=parameters,
                    contract=contract,
                    authorization=authorization_for(contract),
                    signing_key=b"test-signing-key",
                    state=state,
                    state_path=state_path,
                )
            persisted = load_structured(state_path)
            self.assertEqual(persisted["submission_state"], "submission_uncertain")
            self.assertEqual(persisted["submissions_used"], 1)

    def test_response_read_timeout_persists_uncertain_lock(self) -> None:
        class TimeoutResponse:
            def read(self, size: int = -1) -> bytes:
                raise TimeoutError("fictional timeout")

        class TimeoutOpener:
            def __call__(self, request, timeout=0):
                return TimeoutResponse()

        parameters = {
            "membrane_only": "true",
            "upper": "POPC=1",
            "lower": "POPC=1",
            "margin": 20,
        }
        contract = locked_contract(parameters)
        state = base_state()
        state["contract_sha256"] = contract["contract_sha256"]
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "RUN_STATE.json"
            with self.assertRaises(ApiError):
                execute_quick_bilayer_submission(
                    client=CharmmGuiApiClient(opener=TimeoutOpener()),
                    parameters=parameters,
                    contract=contract,
                    authorization=authorization_for(contract),
                    signing_key=b"test-signing-key",
                    state=state,
                    state_path=state_path,
                )
            persisted = load_structured(state_path)
            self.assertEqual(persisted["submission_state"], "submission_uncertain")
            self.assertEqual(persisted["submissions_used"], 1)

    def test_atomic_json_replaces_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            path.write_text("incomplete", encoding="utf-8")
            write_json_atomic(path, {"status": "complete"})
            self.assertEqual(load_structured(path), {"status": "complete"})


if __name__ == "__main__":
    unittest.main()

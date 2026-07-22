# CHARMM-GUI System Builder v2.1.0 Implementation Plan

Status: Authorized for repository implementation
Design source: `docs/superpowers/specs/2026-07-21-charmm-gui-system-builder-v2.1.0-design.md`
Release actions: not authorized by this plan

## Constraints

- Preserve the existing v1.1.1 CLI and validator behavior.
- Use Python 3.10+ standard library for required runtime code.
- Do not submit a real CHARMM-GUI job, log in, access a real credential, or run
  `gmx mdrun`.
- Do not overwrite the installed skill or push/tag GitHub without a separate
  approval.
- Keep `production_ready=false` and `no_mdrun=true` in technical outputs.

## Task 1: Add v2.1 Core Models

Files:

- Add `core/__init__.py`.
- Add `core/canonical.py` for deterministic JSON and SHA-256.
- Add `core/decisions.py` for Routine/Contextual/Critical records, evidence
  ranking, conflicts, and guided-question rendering.
- Add `core/contracts.py` for contract validation, locking, revision diff, and
  content hash.
- Add `core/approvals.py` for append-only staged approvals and authorization
  integrity verification.
- Add `core/evidence.py` for sanitized append-only evidence events.
- Add `core/schema.py` for shared validation helpers and prohibited secret
  fields.

Tests:

- Add `scripts/tests/test_v21_contracts.py`.
- Verify deterministic hashes, revisions, risk gates, conflict escalation,
  prohibited secret fields, and append-only records.

## Task 2: Add Capability Registry and Safe Router

Files:

- Add `core/capabilities.py` for documented module/action metadata and maturity.
- Add `core/router.py` for route selection, single-submit checks,
  `submission_uncertain`, and job-ID reuse.
- Add `rules/capabilities/official_api.json` with only documented endpoints.
- Add `scripts/charmmgui_api_client.py` with login/status/download/Quick Bilayer
  request builders, dry-run request summaries, redaction, and explicit live
  execution gates.

Tests:

- Add `scripts/tests/test_v21_router_api.py`.
- Mock HTTP responses; never use a real account or network in CI.
- Verify that a lost POST response cannot be retried automatically.

## Task 3: Add Credential Providers and Authorization

Files:

- Add `core/credentials.py` with manual, in-memory test, optional macOS
  Keychain, and unsupported-provider behavior.
- Add `scripts/credential_broker.py` for interactive store/probe/delete only;
  never print a secret.
- Add `scripts/mint_execution_authorization.py` for local interactive contract
  approval and integrity signing.
- Add `scripts/verify_execution_authorization.py` for read-only verification.

Tests:

- Add `scripts/tests/test_v21_credentials_authorization.py`.
- Use only an in-memory provider and fictional values.
- Verify expiration, contract mismatch, action scope, submission count, and
  output redaction.

## Task 4: Add Templates, Rules, and Parameter Inventory

Files:

- Add `templates/TARGET_PROFILE_TEMPLATE.yaml`.
- Add `templates/RUN_REQUEST_TEMPLATE.yaml`.
- Add `templates/DECISION_REGISTER_TEMPLATE.yaml`.
- Add `templates/APPROVED_BUILD_CONTRACT_TEMPLATE.yaml`.
- Add `templates/EXECUTION_AUTHORIZATION_TEMPLATE.json`.
- Add `templates/APPROVAL_LEDGER_EVENT_TEMPLATE.json`.
- Add `templates/EVIDENCE_LEDGER_EVENT_TEMPLATE.json`.
- Update `templates/RUN_STATE_TEMPLATE.json` to v2.1 while preserving a legacy
  fixture.
- Add rule packs under `rules/` for PDB Reader, Ligand Reader, Membrane Builder,
  Solution Builder, Quick Bilayer, and GROMACS.
- Add `scripts/prepare_build_contract.py` to expand a run request into a
  reviewable draft without executing CHARMM-GUI.

Tests:

- Add `scripts/tests/test_v21_decision_inventory.py`.
- Cover salts, membrane orientation, custom ligand, CGenFF penalty, missing
  residues, and output engine dependencies.

## Task 5: Extend State, Recovery, Migration, and Validation

Files:

- Extend `scripts/classify_charmmgui_state.py` and
  `scripts/continuation_guard.py` for v2.1 states without breaking v1.1.1.
- Add `scripts/migrate_v1_state.py` for non-destructive migration and diff.
- Extend `scripts/validate_charmmgui_package.py` with
  `--build-contract`, deriving expected components and ligand charge.
- Add `core/validation_profiles.py` for contract-derived GROMACS expectations.

Tests:

- Extend `scripts/tests/test_state_machine.py`.
- Add `scripts/tests/test_v21_migration_validation.py`.
- Prove old state reading, no overwrite, contract-derived components, and
  legacy status mapping.

## Task 6: Cross-Agent and Documentation Upgrade

Files:

- Update `SKILL.md` to v2.1.0 while staying below 500 lines.
- Update adapters and install guides for capability manifests, Guided Decision
  Protocol, Credential Broker, and API/browser hybrid routing.
- Update `docs/CAPABILITY_MATRIX.md`, `docs/CROSS_AGENT_ARCHITECTURE.md`,
  `scripts/README.md`, checklists, references, README, security policy,
  contribution guidance, and examples.
- Add `docs/API_CAPABILITY_REGISTRY.md`, `docs/CREDENTIAL_SECURITY.md`, and
  `docs/COMMUNITY_VALIDATION.md`.
- Add community report and rule-change templates.
- Update `metadata/compatibility.json`, `metadata/provenance.json`,
  `CITATION.cff`, and `CHANGELOG.md` to 2.1.0.

Tests:

- Extend `scripts/validate_skill_package.py` required paths and metadata checks.
- Extend `scripts/tests/test_skill_package.py` for v2.1 artifacts and safety
  declarations.

## Task 7: Full Verification and Review

Commands:

```bash
python3 -m compileall -q core scripts
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/validate_skill_package.py .
```

Additional checks:

- Search tracked files for accidental credential fixtures.
- Verify no code path invokes `gmx mdrun` or undocumented endpoints.
- Run behavior-preserving code simplification.
- Run code review focused on side effects, authentication, duplicate
  submission, migration safety, and production status.
- Produce installation diff and rollback instructions without installing.

## Completion Evidence

- All old and new tests pass.
- Package validator reports version 2.1.0, `production_ready=false`, and
  `no_mdrun=true`.
- Repository contains the approved design, implementation plan, migration
  path, module maturity registry, and security documentation.
- Git remains uncommitted and unpushed until the user separately approves the
  release action.

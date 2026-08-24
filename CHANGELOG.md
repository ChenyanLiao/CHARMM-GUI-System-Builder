# Changelog

## 2.2.0 - 2026-08-24

- Vendors `simulation-stage-contracts` v1.0.0 with deterministic integrity
  verification and independent per-record schema versions.
- Adds approved build contract 2.2 while preserving 2.1 as read-only legacy
  input and preventing dual contract authorities.
- Adds semantic topology, segment reconciliation, strict `grompp`, TPR
  readback, evidence freshness, and contract-derived closure primitives.
- Moves Receipt 2.0 issuance into Stage 2 with separate read-only audit,
  explicit atomic lock, verification, and hash-chained supersession.
- Keeps every receipt and validation output at `production_ready=false`,
  `md_execution_allowed=false`, and `no_mdrun=true`.
- Adds a structural-environment parity ledger so structure-resolved pocket
  lipids, ions, and cofactors cannot be silently removed as bulk HETATM.
- Adds contract-derived pose-preservation and restraint-handoff gates; Stage 2
  records downstream sensitivity/release requirements but never runs MD.
- Replaces the historical target-specific public case summary with synthetic,
  redacted fixtures that exercise the same gates without publishing private
  molecular-system details or licensed CHARMM-GUI artifacts.

## 2.1.0 - 2026-07-22

- Adds a Guided Decision Protocol that expands each requested system into a
  complete, evidence-ranked parameter inventory before any builder action.
- Adds Routine, Contextual, and Critical risk handling, conflict escalation,
  Critical stop conditions, and clearly labeled test-only assumptions.
- Adds reusable target profiles, immutable SHA-256 build contracts,
  append-only approval/evidence ledgers, revision diffs, and scoped execution
  authorizations.
- Adds a machine-readable capability registry and a gated client for only the
  officially documented login, status, download, and Quick Bilayer APIs; full
  interactive builders remain Browser-Assisted.
- Adds optional macOS Keychain/system-keyring Credential Broker support with
  memory-only API tokens, separate signing keys, one-submission limits, and no
  plaintext credential path.
- Adds v2.1 run state, duplicate-submission protection,
  `submission_uncertain`, non-destructive v1.1.1 migration, and
  contract-derived GROMACS component/ligand-charge validation.
- Adds versioned PDB Reader, Ligand Reader, Membrane Builder, Solution Builder,
  Quick Bilayer, and GROMACS rule packs.
- Adds module maturity, community validation, rule-change proposal, API scope,
  credential security, and cross-agent documentation.
- Preserves legacy v1.1.1 validator/CLI behavior when no v2.1 build contract is
  supplied. All technical outputs keep `production_ready=false` and
  `no_mdrun=true`.

## 1.1.1 - 2026-07-20

- Consolidates duplicate optional JSON metadata loading in the Skill package
  validator without changing its public output or validation behavior.
- Adds regression coverage for malformed compatibility and provenance JSON.
- Keeps all scientific gates unchanged, including `production_ready=false`
  and `no_mdrun=true`.

## 1.1.0 - 2026-07-18

- Establishes `v1.1.0` as the Cross-Agent Edition following the initial
  `v1.0.0` release.

- Adds Cross-Agent Edition adapters for Codex, Claude Code, OpenClaw, Hermes
  Agent, and generic Agent Skills clients while retaining one core `SKILL.md`.
- Adds platform installation guides, a capability matrix, and explicit
  capability-gated browser handoff rules.
- Adds Agent Skills frontmatter metadata, a standard-library package validator,
  compatibility metadata, and cross-agent regression tests.
- Adds official `skills-ref` validation to CI using a pinned upstream revision.

## 1.0.0 - 2026-07-18

- Initial public release.
- Separates backend, page, download, archive, package, custom-parameter,
  preprocessing, and scientific approval states.
- Adds content-based tar/tar.gz/HTML/partial classification and archive safety
  checks.
- Adds GROMACS component, ligand charge, and custom dihedraltype validation.
- Adds synthetic tests for interrupted downloads, unsafe archives, intermediate
  packages, and alternate custom-ligand layouts.

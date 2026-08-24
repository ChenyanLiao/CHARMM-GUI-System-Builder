# CHARMM-GUI System Builder

An auditable cross-agent skill for planning, building, recovering, and
validating CHARMM-GUI PDB Reader, Ligand Reader, Membrane Builder, Solution
Builder, Quick Bilayer, and GROMACS workflows. Version 2.2.0 retains the guided
parameter inventory, risk-ranked recommendations, immutable build contracts,
documented official-API routing, opt-in OS-vault credentials, and
contract-derived output validation, then adds evidence freshness, semantic
topology checks, strict preprocessing/TPR readback, and immutable Stage 2
Receipt 2.0 closure. It also records structural-environment parity, pose
preservation, and restraint handoff while retaining one Agent Skills-compatible
core for Codex, Claude Code, OpenClaw, Hermes Agent, and generic clients.

> **Unofficial project:** this repository is not affiliated with or endorsed by
> the CHARMM-GUI team, Im Lab, or Lehigh University.

## Why This Exists

CHARMM-GUI workflows cross several independent failure boundaries: dynamic
browser forms, asynchronous backend jobs, browser downloads, archive formats,
force-field conversion, topology integrity, and scientific approval. They also
contain many linked scientific choices that should not be silently inherited
from a page default. This skill explains and freezes those choices before it
acts, then keeps each execution and validation boundary separate.

It is designed to prevent common false positives such as:

- treating a visible Step 6 page as a validated package;
- asking for only one salt number while ignoring species, internal ion names,
  neutralization, and experimental conditions;
- silently using a default for ligand identity, protein segmentation, or
  membrane orientation;
- inventing full-builder API support from undocumented page requests;
- duplicating a job after an uncertain POST or stale browser response;
- treating an HTML response named `.tgz` as an archive;
- assuming Safari's `.tar` output is corrupt because the page said `.tgz`;
- advancing before required PSF/CRD products exist;
- overlooking reset form controls after a dynamic selection;
- accepting a custom ligand without checking the converted GROMACS
  `dihedraltypes`;
- calling a technical package pass production approval;
- bypassing topology warnings with `gmx grompp -maxwarn`.

## Capabilities

- audited PDB and ligand input preparation;
- system-specific parameter dependency expansion;
- Routine, Contextual, and Critical decision records with evidence and
  conflict escalation;
- immutable, hashed build contracts and append-only approval/evidence ledgers;
- registry-backed official API routing for documented login, status, download,
  and Quick Bilayer capabilities;
- audited-browser fallback for full interactive builders;
- optional macOS Keychain or system-keyring Credential Broker with separate,
  expiring, one-submission authorization;
- explicit protein segmentation and submission-PDB checks;
- browser and backend state separation;
- low-frequency job recovery without duplicate submissions;
- content-based tar/tar.gz/HTML/partial download inspection;
- safe archive-member validation;
- GROMACS package and component validation;
- custom ligand RTF/PRM/ITP injection verification;
- strict, non-production status vocabulary;
- reusable checklists, templates, synthetic fixtures, and failure records.
- vendored `simulation-stage-contracts` v1.0.0 with deterministic integrity checks;
- read-only closure audit plus separately authorized, hash-chained Receipt 2.0 locking.
- structural-environment ledger validation that distinguishes bulk membrane
  lipids from structure-resolved pocket components;
- pose-preservation and restraint-handoff evidence that remains separate from
  binding-site or production approval.

Most scripts remain read-only. The official API client can log in, query,
download, or submit Quick Bilayer only behind explicit live-action and
authorization gates. No script extracts browser credentials, supports
undocumented builder endpoints, runs production MD, or runs `gmx mdrun`.

## What Changed In v2.2.0

v2.2.0 is the **Audit Closure and Stage Handoff Edition**. It does not replace
the guided decision workflow introduced in v2.1.0. It adds a fail-closed,
evidence-bound closure layer between a completed CHARMM-GUI build and any later
MD execution workflow.

| Area | v2.2.0 behavior | Why it matters |
|---|---|---|
| Shared contracts | Vendors `simulation-stage-contracts` v1.0.0 with per-file hashes and a deterministic tree hash | Every consuming Skill evaluates the same contract and receipt rules without a network install |
| Build contracts | Introduces contract schema 2.2; schema 2.1 remains readable but is never silently rewritten | Historical evidence stays immutable while new runs gain stronger gates |
| Evidence freshness | Records upstream dependencies and invalidates downstream evidence after material input changes | A report cannot remain green after the package, topology, contract, or parameters change |
| Topology validation | Compares molecule identity, atom metadata, connectivity, charges, parameters, and segment reconciliation semantically | Format conversion or segment coalescence is not confused with chemical change |
| GROMACS closure | Probes local capabilities, requires strict `grompp` without `-maxwarn`, and reads the resulting TPR back | File presence alone is no longer accepted as preprocessing proof |
| Structural environment | Classifies bulk membrane material separately from structure-resolved lipids, ions, cofactors, and pocket components | A directly interacting component cannot be silently removed as generic HETATM cleanup |
| Pose preservation | Tracks ligand pose across cleaning, orientation, assembly, and final conversion using an explicit protein or pocket alignment scope | Whole-system movement is separated from ligand displacement relative to the binding environment |
| Restraint handoff | Verifies restraint files, macros, equilibration release schedules, and the expected production define | Restraints cannot disappear, remain active, or be released without an auditable downstream requirement |
| Receipt 2.0 | Separates read-only audit, explicit receipt locking, and independent verification; supports hash-chained supersession | Technical closure becomes immutable without granting MD or production permission |

### Structural-Environment Parity

Each non-protein structural component is assigned a role and disposition. The
validator distinguishes `bulk_membrane_component`,
`structure_resolved_lipid`, `structural_ion_or_cofactor`,
`unrelated_or_obsolete_component`, and `unknown_requires_review`. Its
disposition must be `retain`, `replace`, `remove`, or `unresolved` and must be
supported by the locked build contract.

A component with direct ligand or pocket context, including coordination,
hydrogen bonding, salt bridging, pocket filling, or a claimed local
microenvironment, cannot be removed silently. For a test-only candidate, an
approved alteration produces `ALTERED_APPROVED_CANDIDATE`, forces
`environmental_equivalence=false`, and requires a named downstream sensitivity
branch. In production mode, unresolved or unapproved structural removal blocks
closure.

### Pose-Preservation Evidence

Pose checks use stable atom mapping and an explicit alignment scope of
`protein` or `pocket`. The record distinguishes a rigid transform of the whole
system from displacement of the ligand relative to its environment. Required
metrics and thresholds come from the contract; a missing required metric is
`UNRESOLVED_BLOCKING`, never an implicit pass. This is provenance and geometry
evidence only. It does not establish that a docking pose is experimentally
correct or that a binding site is biologically causal.

### Restraint Handoff

The restraint handoff checks that referenced files exist, required macros are
defined, the equilibration schedule identifies how restraints change, and the
expected production define is explicit. If ligand restraints are intended to
be released before production, the receipt must carry a downstream release
validation requirement. Stage 2 records that obligation but never executes the
release test or any MD.

### Immutable Stage 2 Closure

Closure is intentionally split into three operations:

1. `audit_system_build_closure.py` performs a read-only audit and writes a
   closure draft containing satisfied, missing, stale, and conflicting
   evidence.
2. `lock_system_build_receipt.py` performs the separately authorized atomic
   lock and creates Receipt 2.0 bound to the contract and evidence hashes.
3. `verify_system_build_receipt.py` independently verifies integrity,
   provenance, status invariants, and any supersession chain.

Every receipt remains Stage 2 technical evidence. It always records
`production_ready=false`, `md_execution_allowed=false`, and `no_mdrun=true`.
Only a later, independently governed stage may consider MD authorization.

## v2.1.0 To v2.2.0 Migration

- Existing v2.1 build contracts remain readable, immutable legacy inputs.
- New runs should generate contract schema 2.2 and Receipt 2.0 records.
- Migration creates a new artifact; it never edits a historical contract in
  place and never allows two active contract authorities for one run.
- Existing download, package, and custom-ligand commands retain their public
  behavior. New closure commands are additive.
- The vendored shared core is verified locally before closure. Hash drift
  fails with `E_VENDOR_INTEGRITY_FAILED`; the Skill does not repair or fetch
  vendored code automatically.
- The first shared-core release supports CHARMM-GUI packages and GROMACS
  outputs. Unsupported engines fail closed instead of being treated as
  partially validated.

The synthetic examples
[`synthetic_membrane_build_case.md`](examples/synthetic_membrane_build_case.md)
and
[`synthetic_structural_environment_case.yaml`](examples/synthetic_structural_environment_case.yaml)
demonstrate the public workflow without publishing private molecular systems or
licensed CHARMM-GUI artifacts.

## Cross-Agent Support

The same root [`SKILL.md`](SKILL.md) is installed everywhere. Adapters map the
available terminal, browser, screenshot, download, and native-dialog tools; they
do not duplicate or weaken the scientific gates.

| Runtime | Core skill and validators | Authenticated website workflow |
|---|---|---|
| Codex | Supported | Supported when browser/computer tools are enabled |
| Claude Code | Supported | Requires a configured browser MCP, Playwright, or operator handoff |
| OpenClaw | Supported | Supported when terminal and browser capabilities are enabled |
| Hermes Agent | Supported | Supported when terminal and browser toolsets are enabled |
| Other Agent Skills clients | Supported for instruction loading and local validation | Capability-dependent |

See the full [capability matrix](docs/CAPABILITY_MATRIX.md) and
[cross-agent architecture](docs/CROSS_AGENT_ARCHITECTURE.md). API scope,
credential safety, and maturity evidence are documented separately in
[API_CAPABILITY_REGISTRY.md](docs/API_CAPABILITY_REGISTRY.md),
[CREDENTIAL_SECURITY.md](docs/CREDENTIAL_SECURITY.md), and
[COMMUNITY_VALIDATION.md](docs/COMMUNITY_VALIDATION.md).

The distribution follows the [Agent Skills specification](https://agentskills.io/specification).
Runtime behavior is documented against the official
[Claude Code](https://code.claude.com/docs/en/slash-commands),
[OpenClaw](https://docs.openclaw.ai/skills), and
[Hermes Agent](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md)
skill documentation.

## Installation

- [Codex](docs/INSTALL_CODEX.md)
- [Claude Code](docs/INSTALL_CLAUDE.md)
- [OpenClaw](docs/INSTALL_OPENCLAW.md)
- [Hermes Agent](docs/INSTALL_HERMES.md)

Quick Codex install:

```bash
git clone --branch v2.2.0 --depth 1 \
  https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder.git \
  ~/.codex/skills/charmm-gui-system-builder
```

Restart or reload Codex skill discovery after installation. The entry point is
[`SKILL.md`](SKILL.md).

## Run The Tests

Python 3.10 or newer is recommended. v2.2.0 uses PyYAML to read and lock the
versioned YAML contracts and receipts, and `jsonschema` to validate versioned
records. Install the declared runtime dependencies before running the
validators or tests.

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
python3 -m compileall -q core scripts vendor/simulation_stage_contracts/simulation_stage_contracts
python3 scripts/validate_skill_package.py .
```

The repository display name contains uppercase characters. Installed skill
directories must use the lowercase canonical name
`charmm-gui-system-builder`; run the validator with `--strict-directory-name`
against an installed copy.

## Command-Line Examples

```bash
python3 scripts/inspect_charmmgui_download.py /path/to/download \
  --json-out /path/to/download_inspection.json

python3 scripts/prepare_build_contract.py /path/to/RUN_REQUEST.yaml \
  --target-profile /path/to/TARGET_PROFILE.yaml \
  --input-audit /path/to/INPUT_AUDIT.json \
  --answers /path/to/DECISION_ANSWERS.json \
  --outdir /path/to/contract_review --lock-if-ready

python3 scripts/charmmgui_api_client.py capabilities

python3 scripts/validate_charmmgui_package.py /path/to/archive \
  --outdir /path/to/reports \
  --build-contract /path/to/APPROVED_BUILD_CONTRACT.json

python3 scripts/verify_custom_ligand_injection.py \
  --frozen-dir /path/to/frozen_ligand_parameters \
  --package /path/to/archive \
  --output /path/to/custom_ligand_validation

python3 scripts/audit_system_build_closure.py --help
python3 scripts/lock_system_build_receipt.py --help
python3 scripts/verify_system_build_receipt.py --help
python3 scripts/validate_stage2_scientific_context.py --help
```

## Status Boundary

A package-validator pass means only `Candidate_Package_Validated`. The later
`Technical_Pass_Not_Production_Approval` state additionally requires strict
`grompp` and any applicable custom-ligand injection gate. Production still
requires reviewed molecular identity, protonation, ligand
parameters, protein segmentation, orientation, topology preprocessing, and
explicit expert approval. Environment-altered candidate receipts additionally
require a named downstream sensitivity branch. A saved credential or signed test-only authorization
does not clear those gates. A prepared structure is not binding-site evidence.
Receipt 2.0 is Stage 2 technical evidence only and always denies MD execution
and production approval.

## Authorship And Canonical Source

- Original author and project founder: **Liao Chenyan**
- Canonical repository:
  <https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder>
- Machine-readable origin ID:
  `io.github.ChenyanLiao.charmm-gui-system-builder`

See [`NOTICE`](NOTICE), [`ADDITIONAL_TERMS.md`](ADDITIONAL_TERMS.md),
[`AUTHORS.md`](AUTHORS.md), and [`CITATION.cff`](CITATION.cff). Official releases
are releases published from the canonical repository according to
[`GOVERNANCE.md`](GOVERNANCE.md).

## License

GNU Affero General Public License v3.0, with the permitted attribution and
origin notices described in `ADDITIONAL_TERMS.md` under AGPLv3 section 7.

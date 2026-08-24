# CHARMM-GUI System Builder v2.2.0 Design Specification

Status: Draft for final written-specification review; all design sections approved
Date: 2026-07-30
Last amended: 2026-08-24
Target release: v2.2.0
Project: CHARMM-GUI System Builder
Edition: Audit Closure and Stage Handoff Edition
Canonical repository: https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder
Original author and project creator: Liao Chenyan

## 1. Executive Summary

CHARMM-GUI System Builder v2.2.0 adds a formal, evidence-bound closure for
system-building work. It keeps the guided contract and API/browser execution
architecture introduced in v2.1.0, then closes the remaining gap between a
technically generated CHARMM-GUI package and a trustworthy handoff to a later
molecular-dynamics validation stage.

The release introduces an independent, non-user-facing shared library named
`simulation-stage-contracts`. The library standardizes stage contracts,
evidence dependency graphs, immutable receipts, semantic topology comparison,
GROMACS capability probing, strict preprocessing, and TPR readback. It is
vendored into each consuming Skill with exact version and SHA-256 pinning so
runtime use requires neither network access nor package installation.

The central output is an immutable Stage 2 system-build receipt. A successful
receipt proves only that the package and its recorded technical validations
match the locked build contract. Every Stage 2 receipt explicitly denies MD
execution and production approval. A later stage must validate the receipt and
issue a separate authorization before any MD command may run.

The release also adds a structural-environment parity gate. It distinguishes
bulk membrane components from structure-resolved lipids, structural ions,
cofactors, and other pocket components. Any retention, replacement, or removal
is recorded explicitly, and a technically valid package may still carry an
environment-altered scientific scope that requires a downstream sensitivity
branch.

This design is informed by an external private system-build closure, where literal topology
comparison produced false negatives, GROMACS command compatibility required
capability-aware handling, segment identities changed through validated
disulfide-driven coalescence, and an initially incomplete `no_mdrun` evidence
chain had to fail closed.

## 2. Release and Compatibility Position

- The currently released Skill remains v2.1.0 Guided Contract Edition.
- This specification targets v2.2.0.
- The shared library starts at `simulation-stage-contracts` v1.0.0.
- Existing v2.1.0 tags and releases remain intact; no Git history rewrite is
  part of this release.
- Existing schema 1.0 and 1.1 handoffs and receipts remain readable.
- New records use the v2 schema defined by this design.
- Migration is non-destructive and never overwrites historical evidence.
- The first shared-core release officially supports CHARMM-GUI packages and
  GROMACS outputs only. Other engines fail closed with
  `E_UNSUPPORTED_ENGINE`.

The v2.2.0 number is appropriate because the Skill's existing user-facing
workflow remains compatible while substantial new closure capabilities are
added. A future incompatible command or contract redesign would require a
major version.

## 3. Goals

### 3.1 Product Goals

- Turn an approved v2.1.0 build contract into a verifiable Stage 2 handoff.
- Separate backend completion, web-page progression, and download transfer
  state.
- Derive required evidence from the locked contract rather than from a single
  hard-coded example.
- Detect stale downstream evidence whenever an upstream artifact changes.
- Compare topology semantics instead of relying on literal file equality.
- Track biological segments, PDB boundaries, CHARMM segments, PSF segments,
  and GROMACS molecule types without conflating them.
- Probe the installed GROMACS capabilities before selecting commands.
- Require strict `grompp` and a successful TPR readback without `-maxwarn`.
- Produce an immutable, hash-bound system-build receipt.
- Preserve a strict boundary between technical validation and scientific or
  production approval.

### 3.2 Engineering Goals

- Reuse one exact shared implementation across stage-related Skills.
- Run without network access or runtime package installation.
- Pin vendored code by version, source revision, file hashes, and tree hash.
- Provide stable machine-readable errors and predictable exit codes.
- Make audit read-only and receipt locking separately authorized and atomic.
- Keep credentials and browser session data outside the shared core and all
  evidence products.
- Preserve historical receipts through immutable revision chains.
- Support deterministic local and CI tests with redistributable fixtures.

### 3.3 Scientific Goals

- Fail when chemical identity, charge, connectivity, key ions, or required
  custom parameters change unexpectedly.
- Distinguish acceptable format conversion from chemically meaningful change.
- Require explicit explanations for protein segment coalescence.
- Distinguish bulk membrane composition from structure-resolved pocket lipids,
  structural ions, and cofactors.
- Preserve coordinate-pose provenance across cleaning, PDB Reader,
  orientation, assembly, and final GROMACS conversion.
- Bind structural-component omissions and restraint assumptions to explicit
  downstream scientific scope and sensitivity requirements.
- Preserve parameter-quality, protonation, orientation, pose, and mechanism
  questions as unresolved scientific gates when they are not independently
  established.

## 4. Non-Goals

v2.2.0 will not:

- run `gmx mdrun` or any production MD;
- grant MD execution or production permission;
- submit a new CHARMM-GUI job as part of closure validation;
- replace the v2.1.0 guided build-contract workflow;
- read passwords, cookies, tokens, browser profiles, or authorization headers;
- reverse engineer or invent undocumented CHARMM-GUI endpoints;
- claim that semantic equivalence proves force-field accuracy;
- claim that removal or generic replacement of a structure-resolved lipid is
  environmentally equivalent without evidence;
- claim that package completeness proves ligand protonation, membrane
  orientation, binding-site identity, pharmacology, or biological mechanism;
- support AMBER, NAMD, OpenMM, CHARMM, GENESIS, LAMMPS, Desmond, or Tinker in
  the shared-core v1.0.0 engine implementation;
- publish full licensed CHARMM-GUI or CHARMM force-field packages as fixtures;
- overwrite or silently mutate an existing handoff, contract, evidence report,
  or receipt;
- add cryptographic signing or remote trust infrastructure in this release.
- execute a restraint-release test or structural-component sensitivity MD
  branch; Stage 2 records those requirements but never runs them.

## 5. Approved Architecture

### 5.1 Independent Shared Core

The canonical local source layout is:

```text
<shared-core-source-root>/
  Repository/
    simulation_stage_contracts/
    schemas/
    engines/
      charmm_gui/
      gromacs/
    tests/
    tools/
    README.md
    AUTHORS.md
    NOTICE
    CITATION.cff
    LICENSE
    GOVERNANCE.md
    CHANGELOG.md
```

The shared core is a bottom-layer library, not a fourth user-callable Skill.
It owns:

- contract and receipt schemas;
- evidence graphs and stale detection;
- CHARMM-GUI package inspection;
- semantic topology comparison;
- segment identity reconciliation;
- GROMACS capability probing;
- strict GROMACS preprocessing and TPR readback;
- closure auditing, immutable receipt creation, and receipt verification;
- stable errors and exit statuses.

It does not own:

- user interaction;
- scientific recommendation rules;
- credentials;
- browser automation;
- API login or submission;
- CHARMM-GUI job creation;
- MD execution.

### 5.2 Vendored Distribution

Each consuming Skill contains:

```text
vendor/simulation_stage_contracts/
VENDOR_MANIFEST.json
```

`VENDOR_MANIFEST.json` records:

- shared-core package version;
- canonical source repository;
- source tag and commit;
- every vendored file's SHA-256;
- a deterministic tree hash;
- supported contract and receipt schema versions;
- license, author, and provenance file requirements.

Runtime startup validates all fields. Any mismatch returns
`E_VENDOR_INTEGRITY_FAILED` and blocks closure. The runtime never fetches or
repairs vendored code over the network.

### 5.3 Consumer Boundaries

The initial consumers are:

- CHARMM-GUI System Builder;
- Protein-Ligand Complex Readiness;
- Protein-Ligand Simulation Suite and its MD validation handoff.

Each consumer retains its own domain policy and user experience. Shared-core
behavior must not be copied and independently modified in multiple Skills.
Compatible consumer releases vendor exactly the same shared-core v1.0.0 tree.

For structural-environment parity, the shared core owns the record schema,
hashing, dependency graph, status invariants, and receipt validation. CHARMM-GUI
System Builder owns Stage 2 component classification, coordinate-distance and
pose calculations, builder-specific restraint parsing, and scientific decision
policy. The shared core must not acquire target-specific residue rules or
interpret a lipid contact as biologically causal.

### 5.4 Execution Transport Independence

The build adapter records one of:

```yaml
submission_transport: api | browser | manual
```

Official API, audited browser, and manual download paths feed the same evidence
model and closure gates. Transport choice cannot weaken package validation or
receipt requirements.

## 6. Core Records

### 6.1 Stage Handoff

`STAGE_HANDOFF.yaml` imports the preceding stage's input identities,
provenance, assumptions, artifact hashes, unresolved gates, and permissions.
Legacy schema 1.0 and 1.1 records are read-only inputs.

### 6.2 System Build Contract

`SYSTEM_BUILD_CONTRACT.yaml` freezes before execution:

- target, system, run, and builder identity;
- all input roles, paths, sizes, and hashes;
- protein chain, segment, gap, terminus, and disulfide strategy;
- ligand identity, protonation assumption, total charge, atom mapping, and
  parameter source;
- retained structural ions and removed old solvent or bulk ions;
- every non-protein structural component classified by role, interaction
  context, disposition, and parameter availability;
- membrane composition, orientation state, system dimensions, water model,
  salt type and concentration;
- protein, lipid, ligand, water, and ion force-field selections;
- requested output engine;
- Routine, Contextual, and Critical decisions;
- temporary assumptions and scientific blockers;
- derived evidence requirements;
- canonical contract hash.

The contract references a locked `STRUCTURAL_ENVIRONMENT_LEDGER.yaml` and a
pose-preservation specification. Missing or unresolved direct-contact
components cannot be silently treated as bulk hetero residues.

Material changes create a new contract revision and invalidate downstream
authorization and evidence. A locked contract is never edited in place.

### 6.3 Build Run Manifest

`BUILD_RUN_MANIFEST.json` records execution without credentials. It keeps these
states independent:

- CHARMM-GUI backend state;
- page or workflow state;
- download transport state;
- local artifact collection state.

It also records sanitized job IDs, steps, warnings, errors, timestamps, and
artifact identifiers. A browser download failure cannot automatically mark the
backend job as failed.

### 6.4 Evidence Index

`EVIDENCE_INDEX.json` records for every artifact:

- stable artifact ID;
- run-relative path;
- SHA-256 and size;
- producer and tool version;
- input dependencies;
- validation status;
- stable error codes;
- generation timestamp;
- schema and validator version.

Absolute local paths may be retained only in private run metadata. Public
reports use run-relative paths.

### 6.5 Closure Draft

`SYSTEM_BUILD_CLOSURE_DRAFT.json` and its Markdown rendering are produced by a
read-only audit. They report:

- satisfied evidence;
- missing evidence;
- stale evidence;
- conflicting parameters;
- unresolved Routine, Contextual, and Critical risks;
- technical result;
- scientific and permission boundaries;
- the exact contract and evidence hashes used by the audit.

A closure draft is not a receipt and grants no permission.

### 6.6 Immutable Receipt

`SYSTEM_BUILD_RECEIPT.vNNN.yaml` is created only by the separately authorized
lock operation. Every Stage 2 receipt contains:

```yaml
technical_status: Technical_Pass_Not_Production_Approval
md_execution_allowed: false
production_allowed: false
production_ready: false
no_mdrun: true
```

The closure draft and every passing receipt carry an orthogonal environment
assessment:

```yaml
environmental_parity_status: PRESERVED | ALTERED_APPROVED_CANDIDATE | UNRESOLVED_BLOCKING | NOT_APPLICABLE
environmental_equivalence: true | false | null
downstream_sensitivity_required: true | false
scientific_scope_constraints: []
```

These fields do not replace `technical_status`. `UNRESOLVED_BLOCKING` appears
only in a blocked closure draft; it cannot appear in a passing receipt.
`environmental_equivalence` is `null` for unresolved or non-applicable cases.
An explicitly approved
candidate build may be technically valid while its environment is altered. It
still has `production_ready: false` and preserves the required downstream
comparison. An unresolved direct-contact component yields no passing receipt.

If technical validation does not pass, no passing receipt is created. A
blocked closure report may still be written for diagnosis.

`SYSTEM_BUILD_RECEIPT_LATEST.json` is a discovery pointer only. It is not
scientific evidence and does not replace historical receipts.

## 7. Evidence Dependency Graph

The canonical dependency order is:

```text
Stage 1 Handoff
  -> Locked Build Contract
  -> Structural Environment Ledger
  -> Pose-Preservation Baseline
  -> CHARMM-GUI Build Artifacts
  -> Download Inspection
  -> Package Validation
  -> Semantic Topology Validation
  -> Strict GROMACS Preflight
  -> TPR Readback
  -> Closure Audit
  -> Immutable Stage 2 Receipt
```

Each evidence node stores the hashes of its direct ancestors. If an ancestor's
content changes, every dependent node becomes `STALE`. Timestamp changes alone
do not establish content change, and recent timestamps do not rescue a hash
mismatch.

Replacing a ligand topology therefore invalidates the custom-parameter
validation, `grompp` report, TPR readback, closure draft, and any receipt
candidate derived from the previous topology.

Changing a structural-component disposition, coordinate mapping, reference
pose, or restraint expectation likewise invalidates every dependent parity,
pose-preservation, package, closure, and receipt artifact.

Validator or schema upgrades preserve historical receipts but may mark them as
requiring current revalidation before a new stage accepts them.

## 8. State Model

The Stage 2 closure state machine is:

```text
IMPORTED
  -> CONTRACT_DRAFT
  -> CONTRACT_LOCKED
  -> BUILDING
  -> ARTIFACTS_COLLECTED
  -> AUDIT_PASS | AUDIT_FAIL
  -> RECEIPT_LOCKED
  -> SUPERSEDED
```

API, browser, and manual workflows use the same state model. A job ID, page
URL, or successful HTTP response cannot bypass a missing state transition or
required artifact.

### 8.1 Audit Operation

`audit-system-build` is read-only. It:

1. validates the vendored core;
2. loads and validates the locked contract;
3. recomputes all artifact hashes;
4. resolves contract-derived evidence requirements;
5. validates the evidence dependency graph;
6. runs package, topology, segment, and GROMACS checks;
7. emits a closure draft and event records;
8. creates no receipt and grants no permission.

### 8.2 Lock Operation

`lock-system-build` is a separately authorized write operation. It:

1. acquires a run-directory lock;
2. verifies the shared-core version and vendored hashes;
3. reloads the contract and recomputes all evidence hashes;
4. verifies that the approved audit is still current;
5. enforces the fixed Stage 2 permission fields;
6. writes a temporary receipt;
7. flushes and atomically renames the receipt;
8. updates the non-evidentiary latest pointer;
9. releases the lock.

Any change between audit and lock returns `E_AUDIT_STALE`.

### 8.3 Receipt Revision Chain

Existing receipts are never overwritten. A new revision requires:

```yaml
receipt_revision: 2
supersedes_receipt_sha256: "d4d760f4f5dfe21f7a02107c2d26584814ed47ba52c3c8b944be1046a44c1d7f"
change_reason: "Revalidated after replacing stale strict-preflight evidence."
evidence_diff: []
```

`supersedes_receipt_sha256` must be the exact 64-character SHA-256 of the prior
receipt; the value above is an illustrative, non-project hash. `change_reason`
must be a non-empty human-readable explanation supplied at lock authorization.
The new receipt records the timestamp, shared-core version, validator versions,
and current evidence root. The superseded receipt remains verifiable.

## 9. Contract-Derived Evidence Requirements

Evidence requirements are selected from the locked contract:

- A custom-ligand system requires ligand identity, atom mapping, total charge,
  parameter provenance, custom-parameter injection, and semantic effective-
  parameter validation.
- A protein-only system does not require ligand evidence.
- A membrane-only Quick Bilayer system does not require protein or ligand
  evidence.
- A membrane-protein system requires orientation, segment, lipid, solvent,
  ion, package, and engine evidence.
- A structure containing non-protein HETATM components requires a complete
  structural-environment ledger. Components in a direct-contact or
  coordination context require an explicit disposition and review decision.
- A protein-ligand system requires pose-preservation evidence from the frozen
  input through the final engine coordinates.
- A workflow that introduces equilibration restraints requires a restraint
  handoff record defining files, selection macros, schedule, and expected
  unrestrained production state.
- Every GROMACS output requires package validation, strict `grompp`, TPR
  readback, and the actual GROMACS binary path and version.

Missing required evidence returns `E_REQUIRED_EVIDENCE_MISSING`. Evidence that
is not applicable is recorded as `NOT_APPLICABLE`, not `PASS`.

## 10. Semantic Topology Validation

### 10.1 Critical Chemical Identity

The following invariants must match the locked contract and frozen parameter
source:

- atom count;
- atom names and order;
- elements;
- residue and ligand identity;
- total charge within the declared numeric tolerance;
- bond connectivity;
- required key ions;
- ligand formal charge.

Unexpected changes are Critical failures. Representative errors include:

- `E_TOPOLOGY_ATOM_IDENTITY_CHANGED`;
- `E_TOPOLOGY_TOTAL_CHARGE_CHANGED`;
- `E_TOPOLOGY_CONNECTIVITY_CHANGED`;
- `E_REQUIRED_COMPONENT_MISSING`.

### 10.2 Routine Canonicalization

The comparator accepts and explains these representation changes when chemical
identity and effective parameters are preserved:

- residue renumbering;
- reversed bond direction;
- forward or reversed angle and dihedral atom order;
- phase comparison modulo 360 degrees;
- kcal/mol to kJ/mol conversion using exactly 4.184;
- relocation of parameter values from local `LIG.itp` entries to global
  `forcefield.itp` `dihedraltypes`;
- function-9 connectivity in `LIG.itp` combined with numeric parameters in
  `dihedraltypes`;
- legitimate term reordering or duplication that leaves the effective
  parameter set unchanged;
- position-restraint additions that do not alter the unrestrained chemical
  topology.

Successful normalization returns `PASS_SEMANTIC_EQUIVALENCE` and a human-
readable explanation. It does not suppress the normalized diff.

### 10.3 Custom Ligand Parameters

The validator checks:

1. atom names, order, types, and charges;
2. bonded connectivity;
3. every contract-required changed parameter term in the effective final
   parameter space;
4. function, multiplicity, phase, and force constant;
5. forward and reverse atom-type matching;
6. the accepted CHARMM source layouts `lig.str` or `lig.rtf + lig.prm`;
7. the combined GROMACS connectivity and global parameter resolution.

Private parameter-injection counts are conformance inputs, not hard-coded
requirements for unrelated ligands. Each contract supplies its own expected
term inventory.

## 11. Segment Identity Reconciliation

The validator generates `SEGMENT_IDENTITY_MATRIX.tsv` with these distinct
layers:

| Layer | Meaning |
|---|---|
| Biological segment | Scientific or structural unit expected by the model |
| Original PDB chain and TER | Input coordinate boundaries |
| CHARMM segid | Segment identity used during CHARMM-GUI processing |
| PSF segment | Segment encoded in the assembled PSF |
| GROMACS moleculetype | Final topology component identity |

Disulfide-driven segment coalescence is Contextual rather than automatically
wrong. It may pass only when:

- it matches the contract's expected disulfide and segment map;
- no atoms or residues are lost;
- protein connectivity remains consistent;
- no large coordinate gap is converted into an unintended peptide bond.

Unexplained coalescence returns `E_SEGMENT_MAPPING_UNEXPLAINED` and blocks the
receipt.

## 12. Structural Environment Parity

### 12.1 Component Classification

Before cleaning or builder submission, every non-protein component is assigned
exactly one role:

```text
bulk_membrane_component
structure_resolved_lipid
structural_ion_or_cofactor
unrelated_or_obsolete_component
unknown_requires_review
```

Classification uses coordinate provenance, atom completeness, residue
identity, distances to protein and ligand, coordination or hydrogen-bond
geometry, and available experimental interpretation. Residue name alone is
insufficient. A lipid-like HETATM in direct contact with the ligand is not
automatically a disposable bulk lipid.

### 12.2 Structural Environment Ledger

`STRUCTURAL_ENVIRONMENT_LEDGER.yaml` records for every component:

- source residue name, chain or segment, residue number, atom inventory, and
  coordinate hash;
- completeness and parameter availability;
- nearest protein and ligand atoms and distances;
- detected contact, coordination, hydrogen-bond, salt-bridge, or pocket-filling
  roles;
- classification confidence and evidence;
- disposition: `retain`, `replace`, `remove`, or `unresolved`;
- replacement mapping when applicable;
- rationale, reviewer, and approval scope;
- scientific consequence and required downstream sensitivity branch.

The ledger is locked with the build contract. Cleaning scripts and builder
artifacts must reconcile against it atom-by-atom or component-by-component.

### 12.3 Critical Gate

Removing or replacing a component is Critical when it directly contacts the
ligand, coordinates a protein or ion, participates in an interpreted hydrogen
bond or salt bridge, fills the modeled pocket, or is otherwise part of the
claimed starting microenvironment.

- Silent removal is forbidden.
- `unknown_requires_review` or an unresolved Critical disposition blocks the
  closure with `E_STRUCTURAL_COMPONENT_UNRESOLVED`.
- An explicitly approved `test_only` or `Candidate_Not_For_MD` omission may
  proceed as `ALTERED_APPROVED_CANDIDATE`, with
  `environmental_equivalence: false` and
  `downstream_sensitivity_required: true`.
- A generic bulk-lipid replacement does not restore environmental parity unless
  the contract provides an atom-level identity and interaction-preservation
  justification.

This gate records the modeled branch. It does not claim that the omitted
component caused any later trajectory behavior.

### 12.4 Pose-Preservation Ladder

For protein-ligand builds, Stage 2 records a coordinate lineage across:

```text
raw complex
  -> cleaned submission PDB
  -> PDB Reader output
  -> oriented PDB
  -> assembled system
  -> final GROMACS coordinates
```

Each transition records atom mapping coverage, ligand internal RMSD, ligand
pose RMSD after the contract-selected protein or pocket alignment, ligand COM
shift, and the disposition of neighboring structural components. Thresholds
are declared by the contract and test fixture rather than hard-coded for one
ligand. Rigid membrane orientation or box recentering is separated from
ligand-relative movement.

Unexpected identity loss, atom-order drift, or pose displacement beyond the
contract threshold returns `E_POSE_PRESERVATION_FAILED`. Passing this ladder
proves conversion fidelity only; it does not prove a binding site or pose is
experimentally correct.

### 12.5 Restraint Handoff

Stage 2 parses and records:

- protein and ligand restraint files;
- atom selections and preprocessing macros;
- equilibration restraint schedule;
- expected production `define` state;
- whether ligand heavy atoms remain restrained at each generated stage;
- a downstream requirement for short restraint-release validation when
  restraints are removed before production.

An undefined or contradictory restraint macro returns
`E_RESTRAINT_HANDOFF_UNRESOLVED`. Stage 2 does not run the release test and does
not authorize MD; it only binds the requirement into the receipt for a later
stage.

## 13. CHARMM-GUI Package Inspection

Package validation retains the v2.1.0 download-recovery behavior and feeds its
results into the evidence graph. It must:

- identify gzip tar, plain tar, HTML, partial download, damaged archive,
  unsafe archive, and intermediate package by content rather than extension;
- report size, SHA-256, compression, member counts, required extension counts,
  and recommended next action;
- reject absolute or path-traversal members;
- distinguish backend completion from download transfer failure;
- verify the required `.gro`, `.top`, `.itp`, and `.mdp` artifacts;
- check `step5_input.out` for normal and abnormal termination;
- parse expected protein, ligand, lipid, water, ion, cofactor, and structural-
  ion components from the contract;
- reconcile every retained, replaced, and removed structural component against
  `STRUCTURAL_ENVIRONMENT_LEDGER.yaml`;
- preserve pose-ladder and restraint-handoff artifacts as contract-derived
  evidence;
- retain `production_ready: false` regardless of technical package success.

## 14. GROMACS Engine Behavior

### 14.1 Capability Probe

The engine records:

- resolved `gmx` binary path;
- reported version;
- available subcommands;
- supported options for the selected subcommands;
- `grompp` capability;
- available TPR readback method.

Command selection is based on observed capabilities, not on a hard-coded
version guess. TPR readback prefers a confirmed `gmx dump -s` path. Another
method may be used only after the probe confirms support.

### 14.2 Strict Preflight

The only permitted GROMACS execution in Stage 2 is strict preprocessing and
readback. Passing requires:

- `gmx grompp` exit code 0;
- no fatal errors;
- no warnings;
- no `-maxwarn`;
- every NOTE preserved and classified;
- a real `.tpr` file;
- successful TPR readback by the probed method;
- input and output hashes recorded in the evidence graph.

The command allowlist rejects `mdrun`. Tests fail immediately if `mdrun` or
`-maxwarn` appears in an invoked command.

## 15. Internal Interfaces

The shared core exposes stable internal operations:

```text
verify-vendor
migrate-contract
probe-gromacs
compare-topology
audit-system-build
lock-system-build
verify-receipt
```

Each operation emits machine-readable JSON and a Markdown summary. The Skills
wrap these interfaces for users; the shared core is not advertised as an
independent interactive workflow.

## 16. Stable Errors and Exit Codes

An error record has this shape:

```json
{
  "code": "E_REQUIRED_EVIDENCE_MISSING",
  "severity": "BLOCKING",
  "artifact_id": "strict_grompp_report",
  "message": "Required evidence is missing.",
  "recommended_action": "Run the strict GROMACS preflight."
}
```

Error families include:

| Family | Representative codes |
|---|---|
| Input | `E_INPUT_HASH_MISMATCH` |
| Vendor | `E_VENDOR_INTEGRITY_FAILED` |
| Evidence | `E_REQUIRED_EVIDENCE_MISSING`, `E_EVIDENCE_STALE` |
| Topology | `E_TOPOLOGY_CONNECTIVITY_CHANGED` |
| Segment | `E_SEGMENT_MAPPING_UNEXPLAINED` |
| Environment | `E_STRUCTURAL_COMPONENT_UNRESOLVED`, `E_ENVIRONMENT_LEDGER_MISMATCH` |
| Pose | `E_POSE_PRESERVATION_FAILED` |
| Restraint | `E_RESTRAINT_HANDOFF_UNRESOLVED` |
| GROMACS | `E_GROMPP_WARNING`, `E_TPR_READBACK_FAILED` |
| Receipt | `E_AUDIT_STALE`, `E_RECEIPT_REVISION_CONFLICT` |
| Engine | `E_UNSUPPORTED_ENGINE` |
| Security | `E_SECRET_DETECTED` |

Unknown states never become a pass. The exit codes are:

```text
0  Technical checks passed
2  Evidence incomplete or blocked by a scientific or process gate
3  Invalid input, schema, or contract
4  Integrity or security failure
5  Unsupported engine, version, or required capability
```

Unsupported capability and invalid scientific content remain distinguishable.

## 17. Security and Privacy

The shared core does not read or store:

- passwords;
- cookies;
- API or session tokens;
- browser profiles;
- HTTP authorization headers;
- complete shell environments;
- credential-vault contents.

Evidence records are generated from allowlisted fields. The system does not
collect arbitrary data and attempt to redact it afterward. Public exports use
run-relative paths and omit user-home paths, credential locations, and browser
session information.

If a sensitive field or value category is detected, public export returns
`E_SECRET_DETECTED` without printing the detected value.

`audit_events.jsonl` is append-only and records only timestamp, operation,
artifact ID, result, stable error code, core or validator version, and relevant
hashes.

## 18. API and Browser Boundary

An official CHARMM-GUI API may be implemented by the Skill's transport adapter
only when its endpoint and parameters are confirmed by official documentation
or an approved capability record. The shared core does not discover private
endpoints.

Regardless of transport:

- backend completion does not prove local download completion;
- download completion does not prove a valid final archive;
- a page's Step 6 display does not replace output validation;
- API and browser artifacts pass through identical closure checks;
- an unsupported API builder may fall back to the audited browser without
  weakening the contract;
- credentials never enter the core, evidence, report, fixture, or receipt.

## 19. Legacy Migration

Legacy handoffs, receipts, and reports remain read-only. Migration writes:

```text
migration/
  migrated_contract.yaml
  migrated_receipt_candidate.yaml
  migration_diff.json
  migration_report.md
```

Migration rules are:

- preserve every original file and hash;
- map only facts actually present in the legacy record;
- never infer a historical validation that was not recorded;
- treat absent permission fields as not granted;
- require current revalidation when explicit `no_mdrun: true` evidence is
  absent;
- record schema, field, and evidence differences;
- never overwrite the historical source or replace its timestamp.

## 20. Testing Strategy

### 20.1 Unit Tests

Unit tests cover:

- schema parsing and legacy compatibility;
- file and tree hashing;
- vendor integrity;
- contract-derived evidence selection;
- evidence DAG traversal and stale propagation;
- stable errors and exit codes;
- receipt immutability and revisions;
- atomic lock conflict handling;
- sensitive-field blocking;
- unsupported engines;
- structural-component classification and ledger reconciliation;
- pose-lineage stale propagation;
- restraint-handoff parsing and unresolved-macro failure.

### 20.2 Redistributable Semantic Fixtures

Public fixtures cover:

- equivalent residue renumbering;
- reversed bond and dihedral order;
- phase values separated by 360 degrees;
- kcal/mol to kJ/mol conversion;
- parameter relocation into global `dihedraltypes`;
- function-9 connectivity;
- a missing optimized dihedral type;
- changed atom order;
- changed total charge;
- changed bond connectivity;
- expected disulfide-driven segment coalescence;
- unexplained segment coalescence;
- plain tar, gzip tar, HTML masquerading as an archive, partial download,
  damaged archive, unsafe archive, and intermediate package;
- a retained structure-resolved lipid;
- removal of an irrelevant bulk lipid;
- approved candidate removal of a direct-contact structural lipid;
- unresolved missing structural component;
- pose preservation across rigid orientation and recentering;
- true ligand-relative pose displacement;
- valid and unresolved restraint macros;
- an attempted false environmental-parity claim.

Fixtures must be synthetic or demonstrably redistributable. They must not
publish full licensed force fields or private research systems.

### 20.3 Private Local Conformance Replay

A private, read-only local integration test replays validated evidence outside
Git and checks:

- 46/46 changed custom parameters;
- 5/5 primary optimized terms;
- ligand atom count 95 and total charge +1;
- validated segment and disulfide reconciliation;
- strict `grompp` exit code 0;
- zero warnings and fatal errors;
- TPR readback with the supported `gmx dump -s` capability;
- explicit `no_mdrun: true`;
- `production_ready: false` and `md_execution_allowed: false`;
- a structure-resolved pocket-component case proving that removal is recorded
  as environment-altering rather than silently normalized as bulk lipid.

The public repository contains only independently generated synthetic
conformance fixtures, not a complete research system.

### 20.4 Receipt Tests

Tests verify that:

1. audit never writes a formal receipt;
2. changes after audit cause `E_AUDIT_STALE`;
3. concurrent locks cannot create conflicting receipts;
4. an existing receipt cannot be overwritten;
5. a revision references the prior receipt hash;
6. missing `no_mdrun: true` fails closed;
7. Stage 2 cannot set MD or production permissions to true;
8. a damaged latest pointer does not invalidate historical receipts;
9. environment-altered candidates cannot set environmental equivalence true;
10. unresolved Critical structural components cannot produce a passing receipt;
11. restraint-release requirements survive receipt locking unchanged.

### 20.5 GROMACS Tests

Recorded, redacted help output tests capability detection across versions.
When a compatible local GROMACS is available, an optional integration test
runs a redistributable minimal `grompp` and TPR readback. The test harness
audits every launched command and fails if it sees `mdrun` or `-maxwarn`.

### 20.6 Cross-Skill Conformance

All consumers run a common conformance suite proving:

- identical vendored version and tree hash;
- identical receipt-schema interpretation;
- identical stable error behavior;
- Stage 2 never authorizes MD;
- Stage 3 requires a separate authorization decision.

## 21. Release Strategy

The release order is:

1. create the independent shared-core repository;
2. publish `simulation-stage-contracts` v1.0.0;
3. vendor the exact release into CHARMM-GUI System Builder;
4. run unit, fixture, vendor-integrity, and private replay tests;
5. vendor the same core into the other consuming Skills;
6. run cross-Skill conformance tests;
7. update README, CHANGELOG, architecture, migration, and security documents;
8. publish CHARMM-GUI System Builder v2.2.0;
9. publish compatible consumer releases under their own semantic-versioning
   policies.

No v2.2.0 tag or release is created until all mandatory acceptance gates pass.
The v2.1.0 tag and release remain unchanged.

### 21.1 Implementation Decomposition

Implementation is divided into four reviewable milestones rather than one
cross-repository change:

1. Shared-core schemas, errors, vendor integrity, evidence graph, and receipt
   audit or lock primitives.
2. Semantic topology, segment reconciliation, CHARMM-GUI package inspection,
   and GROMACS capability or strict-preflight engines.
3. CHARMM-GUI System Builder v2.2.0 vendoring, workflow integration,
   structural-environment parity, pose preservation, restraint handoff,
   migration, documentation, and private conformance replay.
4. Remaining consumer vendoring, cross-Skill conformance, and compatible
   consumer releases.

Each milestone must pass its own tests and review before the next begins. A
failure in later consumer integration cannot rewrite or silently replace the
already tagged shared-core release.

## 22. Authorship, License, and Provenance

The shared core and consuming Skill use the AGPL-3.0 license.
Every canonical and vendored copy retains:

- `Copyright (C) 2026 Liao Chenyan`;
- Liao Chenyan as original author and project creator;
- the fact that Liao Chenyan is the sole creator and modifier through the
  current initial release lineage covered by this specification;
- `AUTHORS.md`;
- `NOTICE`;
- `CITATION.cff`;
- license text;
- canonical source and release provenance;
- source tag, commit, and content hashes in the vendor manifest.

Future contributors may be appended transparently. They must not replace or
remove the original-author attribution. Attribution is public and legally
appropriate; the project uses no hidden watermark or concealed signature.

## 23. Acceptance Criteria

v2.2.0 is eligible for release only when:

1. all existing v2.1.0 tests pass;
2. all shared-core unit and fixture tests pass;
3. all consumer vendor manifests pass exact integrity validation;
4. schema 1.0 and 1.1 migration fixtures pass without source modification;
5. the private read-only replay passes;
6. semantic topology tests distinguish Routine representation changes from
   Critical chemical changes;
7. segment reconciliation accepts only contract-supported coalescence;
8. strict GROMACS preprocessing and TPR readback pass on the supported test
   environment;
9. no test or runtime closure command invokes `gmx mdrun` or `-maxwarn`;
10. public fixtures contain no credentials, private browser data, private
    research systems, or restricted full force-field packages;
11. every passing receipt has `production_ready: false`,
    `md_execution_allowed: false`, `production_allowed: false`, and
    `no_mdrun: true`;
12. v2.1.0 history, tag, and release remain intact;
13. author, license, citation, and provenance files are present and validated;
14. every non-protein structural component is classified and reconciled;
15. environment-altered candidate receipts set
    `environmental_equivalence: false` and preserve a downstream sensitivity
    requirement;
16. unresolved Critical components cannot produce a passing receipt;
17. pose-preservation fixtures separate rigid system transforms from
    ligand-relative displacement;
18. restraint files, macros, schedules, and expected production state are
    represented without Stage 2 running a restraint-release test.

## 24. Scientific Boundary

A v2.2.0 technical pass establishes only that:

- the collected package matches the locked contract and evidence chain;
- the final effective topology preserves the validated chemical identity and
  expected parameter mapping;
- protein segment changes are explained by the approved map;
- GROMACS can strictly preprocess and read the resulting TPR;
- structural-component dispositions, coordinate-pose lineage, and generated
  restraint assumptions are explicit and hash-bound;
- no MD command was run during Stage 2.

It does not establish ligand parameter accuracy, protonation correctness,
binding-pose validity, membrane-orientation validity, production suitability,
environmental causality, restraint-release stability, or biological mechanism.
An environment-altered receipt describes the simulated branch only; it does
not establish that an omitted component caused later pose reorientation.
Those questions remain explicit inputs to later scientific review and Stage 3
authorization.

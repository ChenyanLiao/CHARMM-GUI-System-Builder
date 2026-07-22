---
name: charmm-gui-system-builder
description: Plan, build, recover, and validate auditable CHARMM-GUI PDB Reader, Ligand Reader, Membrane Builder, Solution Builder, Quick Bilayer, and GROMACS workflows. Use when a user needs a complete parameter inventory with risk-ranked recommendations, an immutable approved build contract, official-API or audited-browser routing, safe job recovery, custom CGenFF/ffTK checks, or strict pre-MD package validation. Default to dry_run or Candidate_Not_For_MD and block production until scientific and expert gates pass.
license: AGPL-3.0-only
compatibility: Agent Skills compatible. Bundled tooling requires Python 3.10+. Interactive builders need an audited browser; documented API actions need network access. Login is manual by default, with optional OS-vault credentials and signed authorization. MFA, CAPTCHA, terms changes, and native-dialog fallback remain operator actions.
metadata:
  author: Liao Chenyan
  version: "2.1.0"
  canonical_repository: https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder
  origin_id: io.github.ChenyanLiao.charmm-gui-system-builder
---

# CHARMM-GUI System Builder

## Authorship And Provenance

- Original author and project founder: **Liao Chenyan**.
- Canonical repository:
  `https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder`.
- License: GNU Affero General Public License v3.0.
- Origin ID: `io.github.ChenyanLiao.charmm-gui-system-builder`.

This is an unofficial community project. It is not affiliated with or endorsed
by the CHARMM-GUI team, Im Lab, or Lehigh University. Preserve the reasonable
authorship and provenance notices described in `NOTICE` and
`ADDITIONAL_TERMS.md`. Modified versions must identify themselves as modified
and must not be represented as canonical releases.

## Version

Use release 2.1.0 Guided Contract Edition. Before any builder action, expand the
requested system into a complete parameter inventory, explain the available
choices, classify risk, obtain the required confirmations, and lock a hashed
build contract. Route that same contract through only a documented official API
or an audited browser. Keep page completion, backend completion, transfer,
archive, package, custom-parameter, preprocessing, and scientific approval as
separate gates. Runtime adapters must not fork or weaken this core workflow.

## Select A Runtime Adapter

Read exactly one runtime adapter before using browser or terminal tools:

- [Codex](adapters/codex.md)
- [Claude Code](adapters/claude-code.md)
- [OpenClaw](adapters/openclaw.md)
- [Hermes Agent](adapters/hermes.md)
- [Generic Agent Skills client](adapters/generic-agent-skills.md)

At run startup, copy
[`RUNTIME_CAPABILITY_MANIFEST_TEMPLATE.json`](templates/RUNTIME_CAPABILITY_MANIFEST_TEMPLATE.json)
into the run directory and record each capability as `available`,
`operator_required`, or `unavailable` with concrete evidence. Do not infer a
browser, network, vault, upload, download, or native-dialog capability from the
agent name. Select the execution route only after this manifest is complete.

Before acting, record whether the runtime has file read/write, local command
execution, an authenticated browser path, screenshot/page-state capture,
download control, and native-dialog handling. Missing browser capabilities do
not block local audits and archive validation, but they do block autonomous
website submission. Fall back to a redacted operator checklist instead of
inventing tool names or claiming an action occurred.

## Load The Relevant References

- Read [continuous_execution.md](references/continuous_execution.md) before an
  unattended browser run or a resumed job.
- Read
  [browser_form_and_download_recovery.md](references/browser_form_and_download_recovery.md)
  before changing dynamic form controls, handling a native save panel, or
  recovering a download.
- Search [known_failure_modes.md](examples/known_failure_modes.md) by job ID,
  step, or error excerpt before retrying a failed step.
- Use the matching checklist under `checklists/` before each irreversible page
  submission and before declaring a package valid.
- Read [API_CAPABILITY_REGISTRY.md](docs/API_CAPABILITY_REGISTRY.md) before any
  API action and [CREDENTIAL_SECURITY.md](docs/CREDENTIAL_SECURITY.md) before
  enabling saved credentials or unattended execution.

## Enforce The Safety Boundary

- Never record, print, copy, export, or place passwords, cookies, tokens, JWTs,
  CSRF values, CAPTCHA responses, or MFA codes in project files, screenshots,
  reports, command history, environment files, skills, examples, or chat.
- Login is manual by default. An explicit opt-in may store a credential only in
  macOS Keychain or a supported OS secret service; run files contain only an
  opaque provider reference. Plaintext credential files are forbidden.
- Retrieve a saved secret and consume it inside the same controlled login
  process. Keep API tokens memory-only. Never inspect or export browser cookies.
- Saved credentials authenticate an account; they do not authorize submission.
  Side effects require a content-bound, expiring authorization for the exact
  locked contract. MFA, CAPTCHA, terms acceptance, Touch ID, and account
  challenges always stop for the operator.
- Do not bypass anti-automation controls or fabricate unsupported API requests.
- Do not run production MD or `gmx mdrun` unless the project owner separately
  authorizes the exact action.
- Do not use `gmx grompp -maxwarn` to turn a warning into a pass.
- Treat `param penalty > 50`, unresolved protonation, unverified custom
  parameters, bad protein segmentation, or missing expert approval as
  production blockers.
- Preserve original PDB, SDF/MOL2, parameter files, and downloaded archives.
  Work in a timestamped run directory.

## Use Precise Status Vocabulary

Report the narrowest status supported by evidence:

| Status | Required evidence |
|---|---|
| `Candidate_Not_For_MD` | Input or website workflow exists, but one or more technical/scientific gates remain open. |
| `Builder_Backend_Complete_Package_Unverified` | Final backend output terminated normally, but no real final archive has passed inspection. |
| `Candidate_Package_Validated` | A real archive lists successfully and contains the required GROMACS payload and components. |
| `Technical_Pass_Not_Production_Approval` | Package, custom-parameter injection, and strict `grompp` gates pass; scientific approvals may remain open. |
| `Technical_Fail` | A contract-derived technical gate failed and the failed evidence is preserved. |
| `Incomplete_Or_Unknown` | Evidence is insufficient to classify the run safely. |

Never call a visible `download.tgz` link, a Step 6 page, or
`step5_input.out NORMAL TERMINATION` a validated GROMACS package.

## Follow The Evidence Hierarchy

Use independent evidence layers:

1. Immutable local input manifests, hashes, and input audits.
2. CHARMM-GUI backend step files and their termination markers.
3. A locally saved archive that is proven to be a tar/tar.gz and not HTML.
4. Parsed GROMACS files, topology components, and custom-ligand payload.
5. Strict `gmx grompp` without `-maxwarn`.
6. Explicit scientific and production approvals.

Use backend files over a stale running banner. Use archive contents over a
filename or page link. Use strict preprocessing over a superficial file count.
Do not infer a higher layer from a lower one.

## Run The Guided Decision Protocol

Before submitting or filling a builder page:

1. Create `TARGET_PROFILE.yaml` for reusable reviewed facts and
   `RUN_REQUEST.yaml` for this run's intent. Never treat either as execution
   approval.
2. Audit the actual PDB, ligand, parameters, and requested output, then run
   `prepare_build_contract.py` to activate only the relevant versioned rule
   packs.
3. For every active parameter, show the available options or fill-in range,
   the recommended value, reason, evidence, confidence, dependencies, and any
   conflict. Do not ask only for a salt concentration; include salt species,
   internal ion names, neutralization, and experimental-condition conflicts.
4. `Routine` values may adopt the recommendation automatically but remain
   visible in the decision register. `Contextual` values require one informed
   confirmation. `Critical` values require options plus a recommended path and
   cannot use a silent default.
5. A Critical temporary assumption is allowed only for `test_only` or
   `Candidate_Not_For_MD` and keeps production blocked. Never use one to bypass
   ligand identity, protein connectivity/segmentation, or membrane orientation.
6. Freeze all accepted values, input hashes, expected components, module
   maturity, and execution route in `APPROVED_BUILD_CONTRACT.json`. Lock it and
   record its SHA-256 before any side-effecting action. A material change creates
   a new revision and invalidates the previous execution authorization.

Evidence priority is experimental conditions, approved expert/target profile,
current input audit, official CHARMM-GUI documentation, versioned rules and
reliable literature, then agent inference. Any material conflict escalates to
Critical even if one source ranks higher.

## Prepare And Freeze Inputs

Create a timestamped run directory and copy only required inputs. Record source
paths, sizes, hashes, mode, intended builder, and do-not-modify paths in a run
manifest.

Audit the input PDB before upload:

1. Record chains, segment boundaries, residue ranges, ATOM/HETATM counts,
   altlocs, missing coordinates, duplicate atoms, waters, ions, cofactors, and
   non-standard residues.
2. Keep the intended protein, ligand, and explicitly justified key ions.
3. Remove old bulk water, old bulk ions, and unrelated ligands only in a new
   cleaned copy.
4. Preserve ligand coordinates, atom order, stereochemistry, formal charge,
   residue name, and chemical identity.
5. Never overwrite the original PDB.

For proteins with large unresolved sequence gaps, prepare explicit segments.
Do not let CHARMM-GUI bond across a large gap as one continuous protein
segment. Run `build_segmented_submission_pdb.py` and
`audit_submission_pdb.py`, then block upload if any coordinate, TER boundary,
ligand-name, or key-ion invariant fails.

For a representative nine-segment channel, use `PROA` through `PROI`, but take
the residue ranges from the reviewed project profile. Never reuse segment
boundaries from an unrelated target.

## Validate Ligand And Custom Parameters

Audit each SDF/MOL2 for explicit hydrogen count, heavy-atom count, total atom
count, bond orders, formal charge, atom names/order, and residue name.

- Treat automatic CGenFF as compatible in principle with CHARMM36 protein,
  lipid, and water, not as proof of parameter quality.
- Block production when `param penalty > 50`; review high charge penalties and
  protonation separately.
- Freeze approved or optimized RTF, PRM, optional STR, validation ITP, changed-term TSV,
  provenance manifest, and hashes before opening CHARMM-GUI.
- Upload custom RTF/PRM only through a website-supported control. Do not emulate
  support through hidden-field edits or fabricated requests.
- Stop if the website offers only a fresh automatic CGenFF route.
- Keep `custom_ligand_verified=false` until the final downloaded package passes
  `verify_custom_ligand_injection.py`. A Step 1 log that merely appends a PRM is
  insufficient. A final package may validly contain `lig.rtf + lig.prm` without
  a standalone `lig.str`; verify the GROMACS conversion through function-9
  connectivity in `LIG.itp` and converted dihedral values in
  `toppar/forcefield.itp`.

## Use The Correct Builder And Scientific Defaults

Use `Input Generator -> Membrane Builder -> Protein/Membrane System` for a
transmembrane protein. Do not substitute Solution Builder or an ordinary water
box.

For a large eukaryotic channel candidate build, derive recommendations from the
reviewed target profile and current audit rather than memory. A common
test-only starting profile, still requiring contract review, is:

- CHARMM36m/CHARMM36 protein and CHARMM36 lipid;
- approved custom ligand parameters, or CGenFF only for test-only work;
- TIP3P water;
- symmetric POPC:cholesterol 70:30 leaflets;
- 0.15 M NaCl with `SOD`/`CLA`;
- GROMACS output;
- later semi-isotropic pressure coupling.

Treat PPM/OPM orientation as a review gate. Require `step2_orient.pdb`, nonzero
plausible top/bottom areas, a sensible protein Z span, and preserved ligand
pose/internal geometry. Stop on empty PPM output, zero top/bottom area, or an
unreviewed fallback to `Use PDB orientation`.

## Route Only Through Confirmed Capabilities

Read `rules/capabilities/official_api.json` and route by capability, not by
convenience. v2.1 recognizes only the officially documented login, status,
download, and Quick Bilayer endpoints. Full PDB Reader, Ligand Reader,
Protein/Membrane Builder, and Solution Builder submission remain audited-browser
workflows unless official documentation is added and the registry is reviewed.
Never infer endpoints from page forms, replay captured session requests, or
label an undocumented request as official API support.

Before one side-effecting submission, verify the locked contract hash,
authorization scope and expiry, approved input hashes, mode, and remaining
submission count. Persist a returned job ID immediately and reuse it for status,
recovery, and download. If a POST may have succeeded but no job ID was captured,
set `submission_state=submission_uncertain`; inspect Job Retriever or available
evidence before any retry. Never create a replacement job automatically.

## Mutate Browser Forms Surgically

Use an existing authenticated browser session supported by the selected runtime
adapter, or an approved Credential Broker path. Suppress screenshots and DOM
evidence capture during login. Use native computer control only when the adapter
explicitly provides it and the browser interface cannot handle an upload or save
panel; otherwise stop for an operator action.

Before every submission:

1. Confirm the exact job ID, project, step, URL, and page title.
2. Capture a screenshot and a redacted parameter JSON.
3. Record visible controls, selected values, warnings, intended action, and
   safe hidden scientific fields. Exclude every credential/auth/session field.
4. Change only the controls that differ from the approved project profile.
5. After each dependency-changing control, re-read all dependent fields.
6. Capture the final pre-submit state and click the intended action once.
7. Record the post-submit URL and set the submitted-action lock immediately.

Do not re-select an already selected force field just to “confirm” it; CHARMM-GUI
can reset dynamically generated controls. Do not treat a preview/calculation as
a submission. For system size, require nonzero lipid counts before submitting.
For final input generation, verify the actual GROMACS checkbox state; visible
text is not enough.

## Enforce Step Gates

Run `verify_step_gate.py` where applicable and apply these gates:

| Stage | Required gate before advancing |
|---|---|
| PDB Reader | `step1_pdbreader.out` normal and PDB/PSF/CRD products present. |
| Orientation | Oriented PDB plus area evidence; human/scientific review recorded. |
| System size | `step3_size.str` or documented equivalent; intended lipid counts recorded. |
| Packing | `step3_packing_head.psf` and `.crd` present; no fatal marker. |
| Components/solvent/ions | Lipid, waterbox, and ion outputs normal; visible and backend ion identities agree. |
| Assembly | `step5_assembly.psf`, `.crd`, and `.pdb` present; output normal. |
| Input generation | `step5_input.out` contains normal termination and no fatal marker. |
| Download | Saved artifact passes `inspect_charmmgui_download.py`; HTML is a failed download. |
| Package | `.gro/.top/.itp/.mdp`, `topol.top`, ligand, protein, lipid, water, and ions validate. |
| Custom ligand | Frozen custom payload and required changed terms match the final package. |
| GROMACS preflight | Strict `gmx grompp` passes without `-maxwarn`; segmentation remains valid. |

Without both packing head files, never enter Step 4. Without all assembly files,
never submit final input generation.

## Maintain v2.1 Run State

Create `RUN_STATE.json` from `templates/RUN_STATE_TEMPLATE.json` and append
sanitized actions to `EVIDENCE_LEDGER.jsonl`. Keep these axes independent:

- `auth_state`: authentication state;
- `browser_state`: connection/native-dialog state;
- `page_state`: visible page state;
- `backend_state`: backend scientific state;
- `download_state`: artifact acquisition state;
- `submission_state`: not submitted, submitted, or submission uncertain;
- `closure_gates`: archive, package, custom ligand, and strict preprocessing;
- `approval_stages`: contract, orientation, exception/drift, and final technical.

Use `classify_charmmgui_state.py` after every page observation or backend probe.
Use `continuation_guard.py` before yielding. Exit code `20` means continue; it
is not a failed test.

For any v2.1 browser or API side effect, invoke these tools with the locked
contract, signed authorization, OS-vault provider, and signing reference. Never
trust editable `authorization_state` or `authorized_actions` fields in
`RUN_STATE.json` as cryptographic proof. The actual executor must reverify the
same authorization immediately before the side effect.

Treat backend values beginning with `complete` as backend-complete, but do not
set `workflow_complete` until backend completion, archive inspection, package
validation, and strict `grompp` closure gates pass. For a custom ligand, also
require custom injection verification. A false completion flag must not override
failed v2.1 closure gates. Migrate an older V6 state only
with `migrate_v1_state.py`; keep the source unchanged and reconfirm every
Critical unknown before creating a locked contract.

## Recover Without Duplicate Submission

For `ERR_EMPTY_RESPONSE`, timeout, stale page, or controller disconnection:

1. Preserve job ID, exact submitted action, timestamp, resume URL, and artifact
   evidence.
2. Do not repeat the click merely because navigation failed.
3. Probe the expected backend output at a low frequency.
4. If the backend grows, wait. If it finishes normally, reopen the same job by
   bookmark or Job Retriever and continue from the next gate.
5. Retry transient page recovery at most three times with increasing cooldown.
6. Stop on fatal output or a documented stall; never silently start a new job.

Use 10-30 minute checks for ordinary running steps and 30-60 minute checks for
packing, assembly, or input generation. Record size, tail digest, required
products, and whether progress changed. Two unchanged checks with missing
required products support a stalled classification.

## Acquire And Validate The Final Archive

Treat final download as a separate state transition:

1. Record page/backend completion independently from browser transfer state.
2. Open the authenticated final page for the exact job.
3. Click the download link once. On the macOS Chrome path, resume only the
   newest interrupted download record; do not click the webpage link again and
   create duplicates.
4. When the selected adapter supports Safari, repeated Chrome transport failures
   may be recovered by reopening the same completed job in Safari. Otherwise
   hand the exact same-job download action to the operator. Do not rerun Step
   5/6 or start a new job.
5. Safari may automatically expand `download.tgz` into `charmm-gui.tar`.
   Browser-reported transfer size, suffix, and on-disk size are not equivalent.
6. Save to the run download directory, or finish in the default Downloads
   directory and move the artifact only after its real type is validated.
7. Record the browser source path, destination, size, timestamp, and SHA-256.
8. Run `inspect_charmmgui_download.py` before `tar`, extraction, package
   validation, or custom-injection validation.
9. If the file is HTML, a login page, zero/truncated data, partial, or non-tar,
   set `download_state=invalid_html` or `invalid_artifact`. Preserve it as
   evidence and re-download from the same authenticated job; do not rebuild.
10. Accept `.tar`, `.tar.gz`, or `.tgz` based on content, not suffix. Detect
    compression programmatically; never choose `tar -tf` versus `tar -tzf`
    from the filename alone.
11. Reject unsafe member paths, links, special files, corrupt archives,
    intermediates without GROMACS payload, and `.crdownload`/partial files.
12. Never expose or save HTML response contents because they may contain account
   context; record only classification, size, hash, and safe indicators.

A final page can be complete while the local download is invalid. Report this
as `Builder_Backend_Complete_Package_Unverified`.

## Validate The Package And Technical Preflight

Run, in order:

1. `inspect_charmmgui_download.py`;
2. `validate_charmmgui_package.py`;
3. `verify_custom_ligand_injection.py` when custom parameters are expected;
4. component and charge/lipid/ion summaries;
5. strict `gmx grompp` on copied/preflight inputs, never `gmx mdrun`.

Check archive readability, member path safety, `.gro/.top/.itp/.mdp`,
`topol.top`, protein, ligand, lipids, TIP3/water, intended ions, ligand total charge, lipid ratio,
semi-isotropic pressure-coupling settings, and CHARMM warnings. Preserve
original MDP files before any edits.

For custom GROMACS ligand parameters, do not require byte-for-byte equality
between the frozen validation ITP and the final package ITP. Verify atom names,
order, types, charges, and function-9 atom-index connectivity in `LIG.itp`;
then match every changed term against `[ dihedraltypes ]` in
`toppar/forcefield.itp`. Convert CHARMM kcal/mol to GROMACS kJ/mol using 4.184,
allow forward/reverse atom-type order, and compare phases modulo 360 degrees.
Absence of `lig.str` is non-blocking when `lig.rtf`, `lig.prm`, and the converted
GROMACS parameter payload all pass.

Do not promote a package that fails `grompp` because of cross-gap bonds. Repair
the segment strategy and regenerate the CHARMM-GUI package instead of using
`-maxwarn`.

## Apply Staged Approval

Append approval records to `APPROVAL_LEDGER.jsonl`, bound to the current
contract and evidence hashes. Leave every unapproved item pending.

1. Pre-submit approval: ligand state, optimized candidate, segmentation,
   missing-residue strategy, key ions, and membrane composition.
2. Orientation approval: only after oriented coordinates and membrane placement
   are reviewed.
3. Final technical approval: only after real archive, package, custom injection,
   and strict preprocessing gates pass.
4. Production policy: remains outside automatic technical validation and
   requires a separately authorized expert decision.

Even a technical pass is not binding-site evidence. A starting pose and one
membrane build do not prove the real binding site.

## Hand Off To Another Agent Safely

Provide the contract hash, exact job ID, step, route, maturity, resume URL, one
allowed action, forbidden actions, artifact gate, screenshot/JSON requirement,
wait interval, and stop conditions. Never provide credentials. Require the
other agent to preserve the submission lock, authorization scope, and production
blockers.

## Maintain The Skill

Before updating this skill, make a complete timestamped backup. Keep the core
`SKILL.md` platform-neutral and update adapters instead of creating divergent
platform copies. Record new
failure modes in `examples/known_failure_modes.md` and new cases in
`examples/case_index.md`. Community reports may propose a rule change but never
change recommendations automatically; use the templates under `community/` and
the maturity gates in `docs/COMMUNITY_VALIDATION.md`. Do not store credentials,
browser state, cookies, tokens, authentication HTML, or unauthorized private
structures. Validate scripts, unit tests, positive/negative archive fixtures,
`scripts/validate_skill_package.py`, and the official `skills-ref` validator
before considering an update complete.

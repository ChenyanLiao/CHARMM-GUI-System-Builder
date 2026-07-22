# CHARMM-GUI System Builder Scripts

Most scripts are read-only with respect to CHARMM-GUI. v2.1.0 also includes a
gated official API client and an opt-in OS-vault Credential Broker. Those paths
perform no live action unless the caller supplies `--allow-live`, a documented
capability, a locked test-only contract where required, and a valid scoped
authorization. No script runs MD or `gmx mdrun`.

## Scripts

- `validate_charmmgui_package.py`: validate a CHARMM-GUI tar/tgz package, Step 5 termination, GROMACS payload, topology components, and ligand charge. With a v2.1 contract, a pass is only `Candidate_Package_Validated`; strict `grompp` and any custom-ligand gate remain separate.
- `prepare_build_contract.py`: expand a run request and optional target/input
  evidence into a risk-ranked decision register and immutable contract draft.
- `migrate_v1_state.py`: create non-destructive v2.1 state plus JSON/Markdown
  migration reports from a legacy state without inferring approvals.
- `credential_broker.py`: interactively store, probe, or delete an opaque
  credential/signing-key reference in macOS Keychain or a supported keyring;
  never prints stored values.
- `mint_execution_authorization.py` and
  `verify_execution_authorization.py`: create and verify a signed, expiring,
  content-bound action scope.
- `charmmgui_api_client.py`: summarize or execute only registry-backed official
  login/status/download/Quick Bilayer API actions. Quick Bilayer submission is
  limited to authorized test-only contracts; live POST fields must equal the
  locked contract, and status/download are bound to its recorded job ID.
- `inspect_charmmgui_download.py`: detect content-defined compression and classify a saved download as `valid_final_candidate`, `intermediate`, `invalid_html`, `partial`, `unsafe_archive`, or another invalid artifact without recording HTML content.
- `probe_charmmgui_job_files.py`: read-only HTTP probe for expected CHARMM-GUI uploaded job files.
- `classify_charmmgui_state.py`: classify authentication, browser, page, and backend state from `RUN_STATE.json` plus optional consecutive probe reports; it never submits or modifies a CHARMM-GUI job.
- `summarize_topol_components.py`: summarize molecule counts from a `topol.top` file or a CHARMM-GUI archive.
- `build_segmented_submission_pdb.py`: create a derived segmented PDB by replacing only the selected ligand atom-name fields.
- `audit_submission_pdb.py`: prove segment ranges, TER boundaries, coordinates, ligand naming, key-ion retention, and absence of old solvent/unrelated hetero residues.
- `verify_step_gate.py`: verify local products required before advancing a CHARMM-GUI page.
- `verify_custom_ligand_injection.py`: compare a downloaded package against frozen optimized RTF/PRM/optional STR/ITP and changed-term provenance. It validates function-9 connectivity in `LIG.itp` plus converted `[ dihedraltypes ]` in `forcefield.itp` rather than requiring ITP text identity.
- `validate_skill_package.py`: validate Agent Skills frontmatter, canonical
  metadata/version consistency, required cross-agent adapters and docs, local
  links, and the 500-line progressive-disclosure limit without modifying the
  skill.

## Rules

- Do not store passwords, cookies, tokens, or session data.
- Do not run `gmx mdrun`.
- Do not use these scripts as production approval.
- Never overwrite source structures or frozen parameter files.
- A failed audit or gate exits nonzero and sets the next action to stop/review.
- Use the v2.1 decision inventory and locked contract before any side effect;
  use the state machine before deciding whether to wait, recover with Job
  Retriever, resume a download, validate locally, advance once, or request
  attention.
- For v2.1 browser/API side effects, pass `--contract`, `--authorization`,
  `--provider`, and `--signing-ref` to the classifier/guard. Editable state
  fields alone never authorize an action; the executor must verify again.
- Run `continuation_guard.py RUN_STATE.json` before ending an unattended task. Exit code `20` means a routine action, recovery, inspection, download validation, or poll is still required.

## Final Package Examples

```bash
python3 scripts/inspect_charmmgui_download.py /path/to/archive \
  --json-out /path/to/download_inspection.json

python3 scripts/validate_charmmgui_package.py /path/to/archive \
  --outdir /path/to/reports \
  --build-contract /path/to/APPROVED_BUILD_CONTRACT.json

python3 scripts/prepare_build_contract.py /path/to/RUN_REQUEST.yaml \
  --target-profile /path/to/TARGET_PROFILE.yaml \
  --input-audit /path/to/INPUT_AUDIT.json \
  --answers /path/to/DECISION_ANSWERS.json \
  --outdir /path/to/contract_review --lock-if-ready

python3 scripts/charmmgui_api_client.py capabilities

# A live Quick Bilayer submission also requires --allow-live, --contract,
# --authorization, --run-state, --signing-ref, and --json-out. Review the
# complete command locally; never place a password or token on the command line.
# Live status and download commands require the same contract, authorization,
# run-state, and signing-reference gate and cannot target an arbitrary job ID.

python3 scripts/verify_custom_ligand_injection.py \
  --frozen-dir /path/to/00_Inputs/Ligand \
  --package /path/to/archive \
  --output /path/to/custom_ligand_validation

python3 scripts/validate_skill_package.py /path/to/skill \
  --json-out /path/to/skill_validation.json
```

Do not infer compression from the suffix. Safari can save a normal POSIX tar
after automatically expanding `download.tgz`; Chrome can leave an interrupted
`.crdownload`; and a small `.tgz` can be HTML.

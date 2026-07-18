# CHARMM-GUI System Builder Scripts

These scripts are read-only with respect to CHARMM-GUI packages and job outputs. They do not submit CHARMM-GUI jobs, do not log in, do not read browser credentials, and do not run MD.

## Scripts

- `validate_charmmgui_package.py`: validate a CHARMM-GUI tar/tgz package, Step 5 termination, GROMACS payload, topology components, and ligand charge; a pass is always `Technical_Pass_Not_Production_Approval`.
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
- Use the V6 workflow before deciding whether to wait, recover with Job Retriever, resume a browser download, validate locally, advance once, or request human attention.
- Run `continuation_guard.py RUN_STATE.json` before ending an unattended task. Exit code `20` means a routine action, recovery, inspection, download validation, or poll is still required.

## Final Package Examples

```bash
python3 scripts/inspect_charmmgui_download.py /path/to/archive \
  --json-out /path/to/download_inspection.json

python3 scripts/validate_charmmgui_package.py /path/to/archive \
  --outdir /path/to/reports \
  --require-ligand --expected-ligand-charge 1 \
  --component-profile example-9segment-membrane

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

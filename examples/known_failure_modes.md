# Known CHARMM-GUI Failure Modes

## 2026-07-08 - job 9000000001 - Step 3/4

- Step: Membrane Builder Step 3 packing / Step 4 lipid component build.
- Error excerpt: `Unit 10 cannot be opened as STEP3_PACKING_HEAD.PSF`.
- Root cause: Step 3 packing did not generate `step3_packing_head.psf` and `step3_packing_head.crd`.
- Recovery action: Do not retry Step 4. Start a clean test-only retry job and gate Step 4 on the presence of both files.
- Reusable: yes.

## 2026-07-08 - job 9000000002 - orientation sanity

- Step: Membrane orientation.
- Error excerpt: orientation appeared to continue but effective orientation evidence was invalid or incomplete.
- Root cause: PPM/browser state can produce an apparently advanced page without reliable membrane placement.
- Recovery action: Re-run orientation carefully, inspect `step2_orient.pdb`, and check top/bottom area and protein Z range.
- Reusable: yes.

## 2026-07-08 - ion selection state

- Step: ion/water setup.
- Error excerpt: page state could revert from NaCl/SOD/CLA toward KCl/POT/CLA after refresh.
- Root cause: page defaults or stale form state.
- Recovery action: use visible page controls to select NaCl; confirm cation `SOD`, anion `CLA`, and concentration before submission.
- Reusable: yes.

## 2026-07-09 - job 9000000002 - Step 5 output generation

- Step: Generate Equilibration and Dynamics Inputs.
- Error excerpt: GROMACS checkbox looked easy to miss; later Safari page displayed `float() argument must be a string or a number, not 'NoneType'`.
- Root cause: checkbox state must be verified from DOM/accessibility, and page-level warnings can be stale even after backend output succeeds.
- Recovery action: confirm `gmx_checked=true`, then validate backend `step5_input.out` and the downloaded package.
- Reusable: yes.

## 2026-07-09 - final download archive type

- Step: download.
- Error excerpt: page label says `download.tgz`, but Safari saved a GNU tar archive.
- Root cause: browser/server download naming can differ from actual archive compression.
- Recovery action: always run `file` and `tar` listing; rename suffix to the actual type if needed.
- Reusable: yes.

## 2026-07-09 - job 9000000002 - strict GROMACS grompp preflight

- Step: post-download GROMACS preprocessing / minimization `grompp`.
- Error excerpt: `The largest distance between excluded atoms is 2.748 nm between atom 8299 and 8316` followed by `Fatal error: Too many warnings (1)`.
- Root cause: the example channel protein was treated as one continuous `PROA`
  segment across large unresolved residue gaps. The generated topology therefore
  connected residues on opposite sides of missing coordinate regions.
- Recovery action: do not use `-maxwarn` as pass evidence. Prepare a new
  CHARMM-GUI rebuild input with reviewed explicit segment breaks (`TER` and/or
  split protein chains), then regenerate the GROMACS package and re-run strict
  `grompp`.
- Reusable: yes.

## 2026-07-09 - job 9000000003 - PDB Reader Step 3 running gate

- Step: PDB Reader Step 3 / Orientation Options.
- Error excerpt: page repeatedly displayed `The CHARMM-GUI process is still running. Please reload this page again a few minutes later.`
- Root cause: `step1_pdbreader.out` ended normally and Step 1 PSF/CRD/PDB existed, but `step2_orient.pdb` and `step2_area.str` remained 404 after low-frequency checks. The page/running gate did not release for the pre-oriented chain-split rebuild input.
- Recovery action: do not repeatedly click `Next`. Preserve the job evidence as stalled, keep the oriented chain-split input, and consider a cleaner rebuild route or manual expert review before creating another CHARMM-GUI job.
- Reusable: yes.

## 2026-07-09 - example ligand high CGenFF penalty vs MD runtime

- Step: ligand parameterization / downstream MD planning.
- Error excerpt: `RESI LIG 1.000 ! param penalty= 77.000 ; charge penalty= 36.139`.
- Root cause: CGenFF automatic analogy parameters are high-risk for example ligand; running 10 ns or 1000 ns MD with these parameters does not validate or improve the ligand force field.
- Recovery action: keep all current MD as `test_only_not_for_production`; prepare QM/ffTK/CGenFF Optimizer route in a separate directory and rebuild the CHARMM-GUI/GROMACS package after optimized parameters are approved.
- Reusable: yes.

## 2026-07-17 - job 9000000004 - backend complete while page fails

- Step: PDB Reader completion / orientation handoff.
- Error excerpt: Chrome displayed `ERR_EMPTY_RESPONSE` while the recorded `step1_pdbreader.out` had `NORMAL TERMINATION`.
- Root cause: the CHARMM-GUI page/network response failed after the backend completed; browser/page state and backend state diverged.
- Recovery action: preserve the jobid and submitted-action lock, do not resubmit, wait through a transient cooldown, and reopen the job through its bookmark or Job Retriever. Advance only after the backend artifact gate and page identity are both confirmed.
- Reusable: yes.

## 2026-07-17 - job 9000000004 - empty system-size preview

- Step: Step 2 system-size and lipid preview.
- Error excerpt: the first preview contained no selected lipids.
- Root cause: the preview was calculated before an XY initial guess was entered.
- Recovery action: do not submit the preview. Enter the reviewed XY guess, recalculate, and require nonzero intended leaflet counts before submission. The corrected run produced 108 CHL1 and 252 POPC per leaflet.
- Reusable: yes.

## 2026-07-17 - job 9000000004 - force-field control resets Step 5 fields

- Step: Step 5 assembly to input-generation form.
- Error excerpt: re-selecting the already selected CHARMM36m value reset dynamic controls.
- Root cause: the force-field dropdown triggers page JavaScript even when the selected value does not change.
- Recovery action: reload a clean same-job page, keep the existing reviewed force field, change only required controls such as GROMACS, then re-read all dependent fields before submit.
- Reusable: yes.

## 2026-07-17 - job 9000000004 - Step 6 navigation empty response

- Step: Generate Equilibration and Dynamics Inputs.
- Error excerpt: Chrome returned `ERR_EMPTY_RESPONSE` after the single Step 6 click.
- Root cause: the browser response failed while the backend accepted the submission.
- Recovery action: keep the submitted-action lock, do not click again, and probe `step5_input.out`. This job later produced a 110,383,673-byte output with normal termination.
- Reusable: yes.

## 2026-07-17 - job 9000000004 - final tgz is HTML

- Step: final package download.
- Error excerpt: a file named `CHARMMGUI_9000000004_...tgz` was only 6,034 bytes and `file` identified it as HTML; `tar` listing failed.
- Root cause: the save/download flow captured a CHARMM-GUI HTML response rather than the authenticated archive payload.
- Recovery action: classify the build as `Builder_Backend_Complete_Package_Unverified`, preserve only safe artifact metadata, and re-download once from the authenticated final page for the same job. Do not rebuild and do not run package/custom-parameter validation on the HTML file.
- Reusable: yes.

## 2026-07-18 - job 9000000004 - Chrome transfer repeatedly interrupted

- Step: final-package browser transfer.
- Error excerpt: Chrome downloads grew to several MB and then showed a network-connection failure.
- Root cause: browser/proxy/VPN/extension transport instability; the CHARMM-GUI backend and final page were already complete.
- Recovery action: resume only the newest record in Chrome's download panel. Do not click the webpage `download.tgz` link again. After repeated failures, reopen the same completed job in Safari rather than rerunning Step 5/6.
- Reusable: yes.

## 2026-07-18 - job 9000000004 - Safari expands tgz to tar

- Step: final-package download and local identification.
- Error excerpt: the website link was `download.tgz`, but Safari saved a 758,997,504-byte POSIX tar as `charmm-gui.tar`.
- Root cause: Safari automatically expanded the gzip transport. Browser-displayed transfer bytes and final on-disk bytes represented different layers.
- Recovery action: ignore the suffix when choosing the reader. Use `file` or `inspect_charmmgui_download.py`, record size/SHA-256, and open with content-based tar detection.
- Reusable: yes.

## 2026-07-18 - job 9000000004 - custom-ligand verifier false negative

- Step: post-download custom-parameter injection validation.
- Error excerpt: the old verifier failed because no standalone `lig.str` existed and final `LIG.itp` did not contain the frozen ITP's explicit dihedral values.
- Root cause: CHARMM-GUI stored the accepted custom input as `lig.rtf + lig.prm`; GROMACS kept function-9 connectivity in `LIG.itp` and converted parameter values in `toppar/forcefield.itp [ dihedraltypes ]`.
- Recovery action: verify RTF/PRM identity, LIG atom order/types/charges, function-9 connectivity, and all converted dihedraltypes using kcal/mol x 4.184, forward/reverse type matching, and phase modulo 360. Job 9000000004 then passed 46/46 changed terms, 5/5 primary terms, and 3/3 target connections.
- Reusable: yes.

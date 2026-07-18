# Synthetic Custom-Parameter Rebuild And Closure State

This public example uses a synthetic job ID. It contains no credentials,
cookies, tokens, session data, authentication HTML, live job URL, local path, or
real archive hash.

## Build

- Synthetic job ID: `9000000004`
- Mode: `Candidate_Not_For_MD` / `test_only_not_for_production`
- Builder: Membrane Builder, Protein/Membrane System
- Protein: explicitly split into `PROA` through `PROI`
- Ligand: `LIG`, total charge `+1`, custom parameter candidate expected
- Key ion: `CAL` retained as a review item
- Force field: CHARMM36m protein / CHARMM36 lipid
- Water: TIP3P
- Membrane: symmetric POPC:CHL1 = 70:30
- Salt: 0.15 M NaCl, SOD/CLA
- Output engine selected: GROMACS only
- Ensemble/temperature: NPT, 303.15 K
- Surface tension: 0

## Gate Evidence

- Orientation produced nonzero top/bottom areas and preserved the submitted
  pose under rigid-transform sanity checks.
- Packing produced required head PSF/CRD products and normal termination.
- Assembly PSF/CRD/PDB existed before final input generation.
- `step5_input.out` reached normal termination.
- The final page exposed a download link without a running or fatal banner.

## Download Recovery

The first `.tgz` was a small HTML response. That was a transfer failure, not a
backend failure. Repeated Chrome transfers were resumed only from the newest
download record. The same completed job was then opened in Safari without
rerunning the builder.

Safari expanded `download.tgz` into a large uncompressed POSIX tar. Content-based
inspection found a readable archive, all required GROMACS file classes, and no
unsafe members.

## Final Local Validation

- `step5_input.out`: normal termination, no abnormal termination.
- Protein segments, CAL, LIG, CHL1, POPC, SOD, CLA, and TIP3 were present.
- LIG atom names/order/types and total charge were preserved.
- `lig.rtf + lig.prm` was valid without a standalone `lig.str`.
- GROMACS stored function-9 connectivity in `LIG.itp` and converted values in
  `toppar/forcefield.itp [ dihedraltypes ]`.
- Fixture expectation: 46/46 changed terms, 5/5 primary terms, and 3/3 target
  connections.
- Status: `Technical_Pass_Not_Production_Approval`.
- Production-ready: false.
- `gmx mdrun` executed: no.

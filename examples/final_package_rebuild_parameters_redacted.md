# Final Package Rebuild Parameters And Closure State

This is a redacted technical case record. It contains no real job ID, local
path, credential, cookie, token, session data, or authentication HTML.

## Build

- Job ID: `[REDACTED_REBUILD_JOB]`
- Mode: `Candidate_Not_For_MD` / `test_only_not_for_production`
- Builder: Membrane Builder, Protein/Membrane System
- Protein: membrane protein split into nine reviewed segments
- Ligand: LIG, total charge +1, custom optimized parameter candidate expected
- Key ion: CAL retained as a review item
- Force field: CHARMM36m protein / CHARMM36 lipid
- Water: TIP3P
- Membrane: symmetric POPC:CHL1 = 70:30
- Per leaflet: POPC 252, CHL1 108
- Salt: 0.15 M NaCl, SOD/CLA
- Final ion counts observed: SOD 194, CLA 204
- Output engine selected: GROMACS only
- Ensemble/temperature: NPT, 303.15 K
- Surface tension: 0

## Gate Evidence

- PPM orientation produced nonzero top/bottom areas and preserved the submitted pose by rigid-transform sanity checks.
- Step 3 packing produced required head PSF/CRD/PDB and normal termination.
- Component, waterbox, ion, and assembly stages produced required products.
- `step5_assembly.psf/.crd/.pdb` existed before Step 6 submission.
- `step5_input.out` reached normal termination.
- Final page showed the download link with no running or fatal banner.

## Download Recovery

The first saved `.tgz` was a small HTML response. This was a transfer failure,
not a CHARMM-GUI backend failure. Repeated Chrome transfers were resumed only
from the newest download record. The same completed job was then opened in
Safari without rerunning Step 5/6.

Safari automatically expanded `download.tgz` and saved a POSIX tar. Content-
based inspection found 213 archive members, 209 regular files, one `.gro`, one
`.top`, 17 `.itp`, eight `.mdp`, no unsafe members, and classification
`valid_final_candidate`.

## Final Local Validation

- `step5_input.out`: normal termination, no abnormal termination.
- Molecules: nine protein segments, CAL, LIG, CHL1, POPC, SOD, CLA, and TIP3 present.
- LIG: 92 atoms, preserved names/order/types, total charge +1.
- Package ligand layout: `lig.rtf + lig.prm`; standalone `lig.str` absent and not required.
- GROMACS representation: function-9 connectivity in `LIG.itp`, converted custom values in `toppar/forcefield.itp [ dihedraltypes ]`.
- Changed optimized terms: 46/46.
- Primary optimized torsion terms: 5/5.
- Target connections: three of three.
- Package status: `Candidate_Package_Validated`.
- Overall use status: `Candidate_Not_For_MD`.
- Production-ready: false.
- `gmx mdrun` executed: no.

Strict `gmx grompp` and scientific/expert approval remain independent closure
gates before any production use.

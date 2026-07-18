# Transmembrane Protein + Ligand Test-Only Case Summary

This public case is intentionally generalized. Job IDs are synthetic and local
paths are placeholders.

- Target: a nine-segment transmembrane protein plus a cationic ligand.
- Successful synthetic job ID: `9000000002`.
- Failed/stalled synthetic job ID: `9000000001`.
- Example package: `<RUN_DIR>/04_Downloads/final_test_only.tar`.
- Final status: `test_only_not_for_production`.
- Production blocker: automatic CGenFF parameter penalty above the review gate.
- `gmx mdrun` was not run.
- The system is not evidence of a true binding site.
- Strict `gmx grompp` exposed a continuous-segment topology across large
  unresolved sequence gaps. The package remained an audited test-only artifact
  until an explicit segmented rebuild could pass preprocessing without
  `-maxwarn`.

## Example Components

| Molecule | Count |
|---|---:|
| PROA-PROI | 1 each |
| CAL | 1 |
| LIG | 1 |
| CHL1 | 216 |
| POPC | 504 |
| SOD | 194 |
| CLA | 204 |
| TIP3 | 70624 |

## Example Checks

- Cholesterol fraction: `216 / (216 + 504) = 30%`.
- Ligand total charge: `+1`.
- `step5_input.out`: normal termination.
- A Safari download may be an uncompressed POSIX tar despite a `.tgz` page
  label.
- Required GROMACS file classes: `.gro`, `.top`, `.itp`, and `.mdp`.

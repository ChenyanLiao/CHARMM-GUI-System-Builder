# Cav3.2 + Ligand Test-Only Case Summary

- Original target: Cav3.2 + ligand transmembrane GROMACS test-only system.
- Successful job ID: `[REDACTED_SUCCESS_JOB]`.
- Failed/stalled job ID: `[REDACTED_FAILED_JOB]`.
- Final package path: `<RUN_ROOT>/04_Downloads/<final-package>.tar`.
- Final status: test_only_not_for_production.
- Production blocked reason: ligand CGenFF `param penalty=77.000`.
- `gmx mdrun` was not run.
- This system is not evidence of a true binding site.
- Remote strict `gmx grompp` preflight later identified a technical blocker: a continuous protein topology spanned large sequence gaps. The package remains an audited test-only artifact, not valid MD input until rebuilt or fixed without `-maxwarn`.
- A chain-split/pre-oriented rebuild attempt stalled at the PDB Reader running gate before producing the required orientation products.

## Final Components

From `gromacs/topol.top`:

| Molecule | Count |
|---|---:|
| PROA | 1 |
| CAL | 1 |
| LIG | 1 |
| CHL1 | 216 |
| POPC | 504 |
| SOD | 194 |
| CLA | 204 |
| TIP3 | 70624 |

## Final Checks

- Lipid ratio: CHL1/(CHL1+POPC)=216/720=30%.
- LIG total charge: +1.
- `step5_input.out`: normal termination.
- Archive type: POSIX tar archive (GNU), despite the page label `download.tgz`.
- GROMACS files present: `.gro`, `.top`, `.itp`, `.mdp`.

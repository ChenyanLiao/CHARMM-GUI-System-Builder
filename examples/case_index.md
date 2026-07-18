# Case Index

All job IDs and local paths in public examples are synthetic or redacted. The
records preserve reusable failure and recovery patterns without exposing a live
CHARMM-GUI job or a contributor workstation path.

| Target | Builder | Synthetic job ID | Final status | Package | Production blocker |
|---|---|---:|---|---|---|
| Nine-segment membrane protein + cationic ligand | Membrane Builder / Protein-Membrane / GROMACS | 9000000002 | `test_only_not_for_production` | `<RUN_DIR>/04_Downloads/final_test_only.tar` | Automatic ligand parameter penalty above review threshold |
| Chain-split orientation retry | PDB Reader / orientation | 9000000003 | `stalled_before_membrane_builder` | none | Orientation gate did not release |
| Custom-parameter rebuild candidate | Membrane Builder / Protein-Membrane / GROMACS | 9000000004 | `Technical_Pass_Not_Production_Approval` | `<RUN_DIR>/04_Downloads/final_candidate.tar` | Strict preprocessing and scientific approval remain open |

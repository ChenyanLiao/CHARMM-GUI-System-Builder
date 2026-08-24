# Structural Environment Parity Checklist

- [ ] Classify every non-protein HETATM as bulk membrane, structure-resolved
      lipid, structural ion/cofactor, unrelated/obsolete, or unknown.
- [ ] Record atom completeness, parameter availability, nearest ligand/protein
      contacts, coordination, hydrogen bonds, salt bridges, and pocket-filling
      roles.
- [ ] Do not treat a lipid-like residue as disposable bulk lipid from its name
      alone.
- [ ] For every retained, replaced, removed, or unresolved component, record
      rationale and review scope.
- [ ] A direct-contact removal or replacement is Critical and cannot be silent.
- [ ] Candidate-only omission records `environmental_equivalence: false` and a
      named downstream sensitivity branch.
- [ ] Unknown or unresolved Critical components block a passing receipt.
- [ ] Record pose-preservation metrics across cleaning, PDB Reader,
      orientation, assembly, and final GROMACS coordinates.
- [ ] Record restraint files, macros, equilibration schedule, and expected
      production `define` state.
- [ ] Do not run `gmx mdrun`; Stage 2 records downstream release-validation
      requirements only.

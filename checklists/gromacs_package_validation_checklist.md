# GROMACS Package Validation Checklist

- [ ] Archive exists.
- [ ] Locked build contract hash recorded and verified.
- [ ] Expected components, segments, ligand name, and ligand charge are derived
      from the contract rather than a remembered case profile.
- [ ] Page completion, backend completion, and browser transfer state are recorded separately.
- [ ] Interrupted Chrome transfer was resumed from the newest download record; the webpage link was not clicked repeatedly.
- [ ] If Safari was used, possible automatic `.tgz` to `.tar` expansion is recorded.
- [ ] `inspect_charmmgui_download.py` classifies the file as `valid_final_candidate`.
- [ ] HTML/login/auth response is absent; HTML body was not copied into reports.
- [ ] Archive type checked by content with `file` or the inspector, not suffix.
- [ ] Size, modification time, and SHA-256 recorded.
- [ ] `archive_member_count` and regular-file count semantics are explicit.
- [ ] Archive lists with auto-detected compression; `tar -tzf` was not chosen only from suffix.
- [ ] No path traversal, absolute path, unsafe link, device, or FIFO member exists.
- [ ] `.gro` files counted.
- [ ] `.top` files counted.
- [ ] `.itp` files counted.
- [ ] `.mdp` files counted.
- [ ] `gromacs/topol.top` parsed.
- [ ] Protein molecule present.
- [ ] Ligand molecule present.
- [ ] Lipids present.
- [ ] Water present.
- [ ] Ions present.
- [ ] Ligand topology present.
- [ ] Frozen custom RTF/PRM/optional STR/ITP injection checked when expected.
- [ ] Optimized changed terms and frozen-parameter SHA match when expected.
- [ ] Missing standalone `lig.str` is non-blocking when `lig.rtf + lig.prm` and GROMACS conversion pass.
- [ ] `LIG.itp` atom names, order, types, charges, and function-9 connectivity checked.
- [ ] `toppar/forcefield.itp [ dihedraltypes ]` checked with kcal/mol to kJ/mol factor 4.184.
- [ ] Atom-type direction and phase modulo 360 are handled during comparison.
- [ ] Ligand charge checked.
- [ ] Lipid ratio checked.
- [ ] `step5_input.out` normal termination checked.
- [ ] Warnings recorded.
- [ ] Production status explicitly stated.
- [ ] Package validator status is at most `Candidate_Package_Validated`; do not
  claim `Technical_Pass_Not_Production_Approval` until strict `grompp` and any
  applicable custom-ligand gate also pass.
- [ ] Backend completion and package validation are reported as separate gates.
- [ ] Strict `gmx grompp` checked without `-maxwarn`.
- [ ] Large protein sequence gaps checked for accidental continuous segment bonding.
- [ ] `pcoupltype = semiisotropic` checked for membrane production-style MDPs.
- [ ] Original CHARMM-GUI `.mdp` files preserved before any edits.
- [ ] Replica MDP edits limited to seed/initial velocity and intended length unless explicitly documented.
- [ ] 10 ns self-check reports exist before any 1000 ns continuation.
- [ ] 1000 ns disk/queue/output-size/checkpoint gates documented before submission.

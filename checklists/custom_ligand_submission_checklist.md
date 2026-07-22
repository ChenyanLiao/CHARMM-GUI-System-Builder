# Custom Ligand Submission Checklist

## Frozen inputs

- [ ] Locked build contract records ligand identity, residue name, formal
      charge, parameter source, input hashes, and expected final component.
- [ ] SDF/MOL2 identity, atom order, and formal charge are audited.
- [ ] Optimized RTF, PRM, optional STR, validation ITP, changed-term table, and
      provenance file are copied into the run without modifying sources.
- [ ] Input hashes match the frozen manifest.
- [ ] Ligand PDB heavy-atom names match the optimized RTF names.

## Website submission

- [ ] Route is audited browser unless an official capability is documented in
      the registry; no captured hidden endpoint is replayed.
- [ ] The website exposes an explicit custom topology/parameter upload route.
- [ ] SDF is used for structure recognition only.
- [ ] Optimized RTF/PRM, or the explicitly supported equivalent STR, is loaded.
- [ ] Residue name and total charge are correct.
- [ ] The page is not silently starting a new automatic CGenFF parameterization.
- [ ] No hidden field is edited to simulate unsupported custom-file handling.

## Download verification

- [ ] The archive is real and can be listed.
- [ ] `inspect_charmmgui_download.py` passed before injection validation.
- [ ] Package contains either standalone `lig.str`, or `lig.rtf + lig.prm`.
- [ ] GROMACS `LIG.itp` and `toppar/forcefield.itp` are present.
- [ ] `LIG.itp` atom index/name/order/type/charge matches the frozen ligand.
- [ ] `LIG.itp` contains function-9 connectivity for required target torsions.
- [ ] Changed-term kcal/mol values are converted by 4.184 and matched against
      `forcefield.itp [ dihedraltypes ]`, allowing reversed types and phase modulo 360.
- [ ] The five primary optimized C22-O2 terms match 5/5.
- [ ] The complete changed/inserted parameter payload matches 46/46 for this case.
- [ ] Target connections `C12-C22-O2-C23`, `C25-C22-O2-C23`, and
      `H33-C22-O2-C23` match 3/3.
- [ ] Lack of standalone `lig.str` was not treated as failure when RTF/PRM and
      the converted GROMACS payload are complete.
- [ ] Frozen parameter provenance and local input hashes are recorded.
- [ ] LIG remains 92 atoms and total charge +1.
- [ ] The historical automatic CGenFF package is rejected by the same verifier.
- [ ] Step 1 append messages alone were not used as final injection proof.
- [ ] Status is at most `Technical_Pass_Not_Production_Approval`; `production_ready=false` and `no_mdrun=true` remain explicit.

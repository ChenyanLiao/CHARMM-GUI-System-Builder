# Membrane Builder Checklist

- [ ] Input audit, active-module inventory, and Decision Register exist.
- [ ] Every Routine value is visible in the contract.
- [ ] Every Contextual value has one recorded confirmation.
- [ ] Critical ligand identity, protein segmentation, and orientation decisions
      are resolved without temporary defaults.
- [ ] The build contract is locked and its hash matches the run state.
- [ ] Execution route is `audited_browser`; no undocumented full-builder API is
      claimed.
- [ ] Builder is Protein/Membrane System.
- [ ] Ordinary water box was not used as final membrane system.
- [ ] PDB Reader output inspected.
- [ ] Ligand retained.
- [ ] Key ions retained or removed by explicit decision.
- [ ] Orientation method recorded.
- [ ] `step2_orient.pdb` inspected.
- [ ] Top/bottom area checked.
- [ ] Protein Z range checked.
- [ ] Lipid option recorded.
- [ ] POPC/CHOL or other composition recorded.
- [ ] Leaflet symmetry/asymmetry recorded.
- [ ] Salt type recorded.
- [ ] Salt recommendation was compared with experimental conditions.
- [ ] SOD/CLA vs POT/CLA checked.
- [ ] Ion concentration recorded.
- [ ] Neutralization setting and estimated ion counts recorded.
- [ ] Visible and safe hidden ion fields agree with the contract after refresh.
- [ ] `step3_packing_head.psf` exists before Step 4.
- [ ] `step3_packing_head.crd` exists before Step 4.
- [ ] `step5_assembly.psf/crd/pdb` exist before Step 6.
- [ ] Step 5 GROMACS checkbox verified from DOM/accessibility state.
- [ ] Any DOM/contract/output drift is recorded and blocks progression until
      resolved or revised.

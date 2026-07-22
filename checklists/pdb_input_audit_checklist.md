# PDB Input Audit Checklist

- [ ] Original PDB path recorded.
- [ ] Cleaned PDB path recorded.
- [ ] Original PDB not overwritten.
- [ ] Input path, size, and SHA-256 recorded in the run request/contract.
- [ ] Chain IDs listed.
- [ ] Protein residue ranges listed.
- [ ] `ATOM` and `HETATM` counts recorded.
- [ ] Water residues checked.
- [ ] Ion residues checked.
- [ ] Hetero residues listed.
- [ ] Intended ligand residue name identified.
- [ ] Key ions identified and justified.
- [ ] Duplicate protein/ligand checked.
- [ ] Altloc checked.
- [ ] Missing coordinates checked.
- [ ] Non-standard residues checked.
- [ ] Protein connectivity and segment strategy reviewed for large gaps.
- [ ] Missing-residue strategy is explicit; no silent large-loop rebuilding.
- [ ] Removed residues documented.
- [ ] Kept residues documented.
- [ ] Audit evidence is attached to the Decision Register; it does not itself
      authorize submission.

# Ligand / CGenFF Checklist

- [ ] Ligand file path recorded.
- [ ] Ligand residue name recorded.
- [ ] Total atom count checked.
- [ ] Heavy atom count checked.
- [ ] Hydrogen count checked.
- [ ] Explicit hydrogens checked.
- [ ] Formal charge checked.
- [ ] Bond orders checked.
- [ ] Tautomer, stereochemistry, atom names, and atom ordering checked.
- [ ] Ligand chemical identity is confirmed; no test-only default bypasses it.
- [ ] CGenFF `lig.rtf` located.
- [ ] CGenFF `lig.prm` located.
- [ ] Param penalty parsed.
- [ ] Charge penalty parsed.
- [ ] `param penalty > 50` blocks production.
- [ ] Expert review required if charge/protonation is uncertain.
- [ ] Parameter source and expected final ligand residue/charge are frozen in
      the build contract.

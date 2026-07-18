# CHARMM-GUI System Builder

An auditable Codex skill and read-only validation toolkit for CHARMM-GUI PDB
Reader, Ligand Reader, Membrane Builder, Solution Builder, and GROMACS package
workflows.

> **Unofficial project:** this repository is not affiliated with or endorsed by
> the CHARMM-GUI team, Im Lab, or Lehigh University.

## Why This Exists

CHARMM-GUI workflows cross several independent failure boundaries: dynamic
browser forms, asynchronous backend jobs, browser downloads, archive formats,
force-field conversion, topology integrity, and scientific approval. This skill
keeps those boundaries separate and records evidence before advancing.

It is designed to prevent common false positives such as:

- treating a visible Step 6 page as a validated package;
- treating an HTML response named `.tgz` as an archive;
- assuming Safari's `.tar` output is corrupt because the page said `.tgz`;
- advancing before required PSF/CRD products exist;
- overlooking reset form controls after a dynamic selection;
- accepting a custom ligand without checking the converted GROMACS
  `dihedraltypes`;
- calling a technical package pass production approval;
- bypassing topology warnings with `gmx grompp -maxwarn`.

## Capabilities

- audited PDB and ligand input preparation;
- explicit protein segmentation and submission-PDB checks;
- browser and backend state separation;
- low-frequency job recovery without duplicate submissions;
- content-based tar/tar.gz/HTML/partial download inspection;
- safe archive-member validation;
- GROMACS package and component validation;
- custom ligand RTF/PRM/ITP injection verification;
- strict, non-production status vocabulary;
- reusable checklists, templates, synthetic fixtures, and failure records.

The scripts do **not** log in, read browser credentials, submit CHARMM-GUI jobs,
run production MD, or run `gmx mdrun`.

## Install As A Codex Skill

```bash
git clone https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder.git
mkdir -p ~/.codex/skills/charmm-gui-system-builder
rsync -a --exclude '.git' --exclude '.github' \
  CHARMM-GUI-System-Builder/ ~/.codex/skills/charmm-gui-system-builder/
```

Restart or reload Codex skill discovery after installation. The entry point is
[`SKILL.md`](SKILL.md).

## Run The Tests

Python 3.10 or newer is recommended. The test suite uses only the standard
library.

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
python3 -m compileall -q scripts
```

## Command-Line Examples

```bash
python3 scripts/inspect_charmmgui_download.py /path/to/download \
  --json-out /path/to/download_inspection.json

python3 scripts/validate_charmmgui_package.py /path/to/archive \
  --outdir /path/to/reports \
  --require-ligand \
  --expected-ligand-charge 1 \
  --component-profile example-9segment-membrane

python3 scripts/verify_custom_ligand_injection.py \
  --frozen-dir /path/to/frozen_ligand_parameters \
  --package /path/to/archive \
  --output /path/to/custom_ligand_validation
```

## Status Boundary

A script pass means at most `Technical_Pass_Not_Production_Approval`.
Production still requires reviewed molecular identity, protonation, ligand
parameters, protein segmentation, orientation, topology preprocessing, and
explicit expert approval. A prepared structure is not binding-site evidence.

## Authorship And Canonical Source

- Original author and project founder: **Liao Chenyan**
- Canonical repository:
  <https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder>
- Machine-readable origin ID:
  `io.github.ChenyanLiao.charmm-gui-system-builder`

See [`NOTICE`](NOTICE), [`ADDITIONAL_TERMS.md`](ADDITIONAL_TERMS.md),
[`AUTHORS.md`](AUTHORS.md), and [`CITATION.cff`](CITATION.cff). Official releases
are releases published from the canonical repository according to
[`GOVERNANCE.md`](GOVERNANCE.md).

## License

GNU Affero General Public License v3.0, with the permitted attribution and
origin notices described in `ADDITIONAL_TERMS.md` under AGPLv3 section 7.


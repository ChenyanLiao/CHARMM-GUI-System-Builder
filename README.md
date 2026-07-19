# CHARMM-GUI System Builder

An auditable cross-agent skill and read-only validation toolkit for CHARMM-GUI
PDB Reader, Ligand Reader, Membrane Builder, Solution Builder, and GROMACS
package workflows. Version 1.1.1 uses one Agent Skills-compatible core with
small runtime adapters for Codex, Claude Code, OpenClaw, Hermes Agent, and
generic Agent Skills clients.

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

## Cross-Agent Support

The same root [`SKILL.md`](SKILL.md) is installed everywhere. Adapters map the
available terminal, browser, screenshot, download, and native-dialog tools; they
do not duplicate or weaken the scientific gates.

| Runtime | Core skill and validators | Authenticated website workflow |
|---|---|---|
| Codex | Supported | Supported when browser/computer tools are enabled |
| Claude Code | Supported | Requires a configured browser MCP, Playwright, or operator handoff |
| OpenClaw | Supported | Supported when terminal and browser capabilities are enabled |
| Hermes Agent | Supported | Supported when terminal and browser toolsets are enabled |
| Other Agent Skills clients | Supported for instruction loading and local validation | Capability-dependent |

See the full [capability matrix](docs/CAPABILITY_MATRIX.md) and
[cross-agent architecture](docs/CROSS_AGENT_ARCHITECTURE.md).

The distribution follows the [Agent Skills specification](https://agentskills.io/specification).
Runtime behavior is documented against the official
[Claude Code](https://code.claude.com/docs/en/slash-commands),
[OpenClaw](https://docs.openclaw.ai/skills), and
[Hermes Agent](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md)
skill documentation.

## Installation

- [Codex](docs/INSTALL_CODEX.md)
- [Claude Code](docs/INSTALL_CLAUDE.md)
- [OpenClaw](docs/INSTALL_OPENCLAW.md)
- [Hermes Agent](docs/INSTALL_HERMES.md)

Quick Codex install:

```bash
git clone --branch v1.1.1 --depth 1 \
  https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder.git \
  ~/.codex/skills/charmm-gui-system-builder
```

Restart or reload Codex skill discovery after installation. The entry point is
[`SKILL.md`](SKILL.md).

## Run The Tests

Python 3.10 or newer is recommended. The test suite uses only the standard
library.

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
python3 -m compileall -q scripts
python3 scripts/validate_skill_package.py .
```

The repository display name contains uppercase characters. Installed skill
directories must use the lowercase canonical name
`charmm-gui-system-builder`; run the validator with `--strict-directory-name`
against an installed copy.

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

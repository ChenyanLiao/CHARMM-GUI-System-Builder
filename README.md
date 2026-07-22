# CHARMM-GUI System Builder

An auditable cross-agent skill for planning, building, recovering, and
validating CHARMM-GUI PDB Reader, Ligand Reader, Membrane Builder, Solution
Builder, Quick Bilayer, and GROMACS workflows. Version 2.1.0 adds a complete
parameter inventory, risk-ranked recommendations, immutable build contracts,
documented official-API routing, opt-in OS-vault credentials, and
contract-derived output validation while retaining one Agent Skills-compatible
core for Codex, Claude Code, OpenClaw, Hermes Agent, and generic clients.

> **Unofficial project:** this repository is not affiliated with or endorsed by
> the CHARMM-GUI team, Im Lab, or Lehigh University.

## Why This Exists

CHARMM-GUI workflows cross several independent failure boundaries: dynamic
browser forms, asynchronous backend jobs, browser downloads, archive formats,
force-field conversion, topology integrity, and scientific approval. They also
contain many linked scientific choices that should not be silently inherited
from a page default. This skill explains and freezes those choices before it
acts, then keeps each execution and validation boundary separate.

It is designed to prevent common false positives such as:

- treating a visible Step 6 page as a validated package;
- asking for only one salt number while ignoring species, internal ion names,
  neutralization, and experimental conditions;
- silently using a default for ligand identity, protein segmentation, or
  membrane orientation;
- inventing full-builder API support from undocumented page requests;
- duplicating a job after an uncertain POST or stale browser response;
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
- system-specific parameter dependency expansion;
- Routine, Contextual, and Critical decision records with evidence and
  conflict escalation;
- immutable, hashed build contracts and append-only approval/evidence ledgers;
- registry-backed official API routing for documented login, status, download,
  and Quick Bilayer capabilities;
- audited-browser fallback for full interactive builders;
- optional macOS Keychain or system-keyring Credential Broker with separate,
  expiring, one-submission authorization;
- explicit protein segmentation and submission-PDB checks;
- browser and backend state separation;
- low-frequency job recovery without duplicate submissions;
- content-based tar/tar.gz/HTML/partial download inspection;
- safe archive-member validation;
- GROMACS package and component validation;
- custom ligand RTF/PRM/ITP injection verification;
- strict, non-production status vocabulary;
- reusable checklists, templates, synthetic fixtures, and failure records.

Most scripts remain read-only. The official API client can log in, query,
download, or submit Quick Bilayer only behind explicit live-action and
authorization gates. No script extracts browser credentials, supports
undocumented builder endpoints, runs production MD, or runs `gmx mdrun`.

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
[cross-agent architecture](docs/CROSS_AGENT_ARCHITECTURE.md). API scope,
credential safety, and maturity evidence are documented separately in
[API_CAPABILITY_REGISTRY.md](docs/API_CAPABILITY_REGISTRY.md),
[CREDENTIAL_SECURITY.md](docs/CREDENTIAL_SECURITY.md), and
[COMMUNITY_VALIDATION.md](docs/COMMUNITY_VALIDATION.md).

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
git clone --branch v2.1.0 --depth 1 \
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
python3 -m compileall -q core scripts
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

python3 scripts/prepare_build_contract.py /path/to/RUN_REQUEST.yaml \
  --target-profile /path/to/TARGET_PROFILE.yaml \
  --input-audit /path/to/INPUT_AUDIT.json \
  --answers /path/to/DECISION_ANSWERS.json \
  --outdir /path/to/contract_review --lock-if-ready

python3 scripts/charmmgui_api_client.py capabilities

python3 scripts/validate_charmmgui_package.py /path/to/archive \
  --outdir /path/to/reports \
  --build-contract /path/to/APPROVED_BUILD_CONTRACT.json

python3 scripts/verify_custom_ligand_injection.py \
  --frozen-dir /path/to/frozen_ligand_parameters \
  --package /path/to/archive \
  --output /path/to/custom_ligand_validation
```

## Status Boundary

A package-validator pass means only `Candidate_Package_Validated`. The later
`Technical_Pass_Not_Production_Approval` state additionally requires strict
`grompp` and any applicable custom-ligand injection gate. Production still
requires reviewed molecular identity, protonation, ligand
parameters, protein segmentation, orientation, topology preprocessing, and
explicit expert approval. A saved credential or signed test-only authorization
does not clear those gates. A prepared structure is not binding-site evidence.

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

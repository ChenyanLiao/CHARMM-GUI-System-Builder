# Install For Codex

## Personal Installation

Back up an existing installation before replacing it. For a fresh install:

```bash
git clone --branch v1.1.1 --depth 1 \
  https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder.git \
  ~/.codex/skills/charmm-gui-system-builder
```

The lowercase destination is required by the Agent Skills name rule. Reload
Codex skill discovery, then verify:

```bash
python3 ~/.codex/skills/charmm-gui-system-builder/scripts/validate_skill_package.py \
  ~/.codex/skills/charmm-gui-system-builder --strict-directory-name
```

Read [`adapters/codex.md`](../adapters/codex.md) before a browser-assisted run.
Available Codex tools vary by host, so capability detection is mandatory.

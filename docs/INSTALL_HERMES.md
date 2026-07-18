# Install For Hermes Agent

Install a pinned release directly into the Hermes skill root:

```bash
git clone --branch v1.1.0 --depth 1 \
  https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder.git \
  ~/.hermes/skills/charmm-gui-system-builder
```

Then verify discovery and package structure:

```bash
hermes skills list
python3 ~/.hermes/skills/charmm-gui-system-builder/scripts/validate_skill_package.py \
  ~/.hermes/skills/charmm-gui-system-builder --strict-directory-name
```

Hermes can also scan a shared skill root through `skills.external_dirs`, but a
writable external directory is not a write-protection boundary. Use a release
copy or filesystem permissions when the skill must remain frozen.

Read [`adapters/hermes.md`](../adapters/hermes.md). Terminal and browser
toolsets are independent; the skill loading successfully does not prove that
either capability is enabled.

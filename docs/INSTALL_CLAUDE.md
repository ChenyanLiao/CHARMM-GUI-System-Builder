# Install For Claude Code

## Personal Installation

```bash
git clone --branch v1.1.1 --depth 1 \
  https://github.com/ChenyanLiao/CHARMM-GUI-System-Builder.git \
  ~/.claude/skills/charmm-gui-system-builder
```

For one repository, clone or copy the release to
`.claude/skills/charmm-gui-system-builder/` instead. Claude Code watches an
existing skills root for changes; restart it if the top-level root did not
exist when the session began.

Verify the installed copy:

```bash
python3 ~/.claude/skills/charmm-gui-system-builder/scripts/validate_skill_package.py \
  ~/.claude/skills/charmm-gui-system-builder --strict-directory-name
```

The skill's local audit and archive scripts work with Claude Code file/shell
tools. Interactive CHARMM-GUI operation additionally requires an explicitly
configured browser integration or an operator handoff. See
[`adapters/claude-code.md`](../adapters/claude-code.md).

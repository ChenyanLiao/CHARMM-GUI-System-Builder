# Claude Code Adapter

## Installation Root

Install the package as
`~/.claude/skills/charmm-gui-system-builder/SKILL.md` for personal use or under
`.claude/skills/charmm-gui-system-builder/` for one project.

## Tool Mapping

- Use Claude Code file and shell capabilities for manifests, validators, and
  read-only archive inspection.
- Local Claude Code does not guarantee an authenticated browser controller.
  Use a browser MCP, Playwright integration, or computer-use capability only
  when the operator has explicitly configured and trusted it.
- If no browser integration is available, produce the redacted page checklist,
  let the operator perform the website action, and resume from screenshots and
  downloaded files.
- Do not add Claude-specific `allowed-tools` or invocation fields to the shared
  core frontmatter; keep the package portable.

Claude cloud and Cowork sessions do not automatically inherit workstation
skills or browser sessions. Treat them as separate runtimes and re-check all
capabilities before claiming local file or website access.

# Hermes Agent Adapter

## Installation Root

Install a reviewed copy as
`~/.hermes/skills/charmm-gui-system-builder/SKILL.md`, or add a reviewed shared
directory through Hermes `skills.external_dirs`.

## Tool Mapping

- Use terminal and file toolsets for manifests and bundled validators.
- Use browser tools only when the active Hermes profile exposes them and they
  can retain the operator-authenticated CHARMM-GUI session.
- A Linux/VPS Hermes runtime has no macOS Safari or native Finder save panel.
  Use the same-job browser download path available on that host, or hand the
  download to the operator; retain content-based archive validation.
- Never infer browser or filesystem access merely because the skill loaded.

Hermes can update writable skills. Install a release copy or make a shared
external directory read-only when reproducibility matters; do not allow an
agent-managed edit to silently replace the canonical v1.1.0 workflow.

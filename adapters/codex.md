# Codex Adapter

## Installation Root

Install the package as
`~/.codex/skills/charmm-gui-system-builder/SKILL.md`. Keep the directory name
lowercase so it matches the Agent Skills `name`.

## Tool Mapping

- Use the available shell/exec tool for read-only probes and bundled Python
  validators.
- Use Codex browser or Chrome control for page state and form controls when the
  current session exposes those capabilities.
- Use computer control only for native upload/save dialogs that browser control
  cannot reach.
- If browser or computer control is absent, switch to the generic adapter's
  operator handoff. Do not assume every Codex host exposes the same tools.

## Runtime Rules

Keep authentication, MFA, CAPTCHA, Touch ID, and OS-password dialogs human.
Exclude auth/session fields from browser snapshots. Preserve the submitted
action lock across resumed turns and use backend evidence before repeating any
page action.

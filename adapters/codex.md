# Codex Adapter

## Installation Root

Install the package as
`~/.codex/skills/charmm-gui-system-builder/SKILL.md`. Keep the directory name
lowercase so it matches the Agent Skills `name`.

## Tool Mapping

Fill the run-local runtime capability manifest before selecting Codex tools;
Codex installations expose different browser, computer, network, and shell
capabilities.

- Use the available shell/exec tool for input audits, Guided Decision Protocol,
  contract locking, read-only probes, and bundled Python validators.
- Use `scripts/charmmgui_api_client.py` only for capabilities present in the
  official registry. Never infer full-builder API support.
- Use Codex browser or Chrome control for page state and form controls when the
  current session exposes those capabilities.
- Use computer control only for native upload/save dialogs that browser control
  cannot reach.
- If browser or computer control is absent, switch to the generic adapter's
  operator handoff. Do not assume every Codex host exposes the same tools.

## Runtime Rules

Manual authentication is the default. An explicitly configured macOS Keychain
reference may be used through the Credential Broker, but it must never appear
in chat or evidence and still requires a valid contract-bound authorization.
Keep MFA, CAPTCHA, terms changes, Touch ID, and account challenges human.
Exclude auth/session fields from browser snapshots. Preserve the submission
lock across resumed turns and use backend evidence before repeating any page or
API action.

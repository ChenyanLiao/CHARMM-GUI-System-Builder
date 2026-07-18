# OpenClaw Adapter

## Installation Root

OpenClaw can load workspace, project-agent, personal, or managed skills. Use a
single installed copy named `charmm-gui-system-builder`; do not edit the
canonical Git checkout in place during a run.

## Tool Mapping

- Use the configured terminal/exec capability for bundled validators.
- Use OpenClaw browser control only when it can preserve the user-authenticated
  session and expose the scientific form state required by the core workflow.
- Use a human operator for login, CAPTCHA, MFA, OS dialogs, and any upload/save
  dialog the browser tool cannot reach.
- If the OpenClaw agent runs remotely, confirm that local input and download
  paths actually exist on that host before acting.

## Multi-Agent Handoff

When another agent operates the browser, give it only the exact job ID, step,
resume URL, one allowed action, required pre-submit fields, action lock, and stop
conditions. Never transfer credentials or session artifacts between agents.

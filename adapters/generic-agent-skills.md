# Generic Agent Skills Adapter

Use this adapter when the runtime has no dedicated file in `adapters/`.

## Capability Handshake

Before acting, classify each capability as `available`, `operator_required`, or
`unavailable`:

| Capability | Minimum evidence |
|---|---|
| File access | Can read inputs and write only inside the selected run directory. |
| Command execution | Can run Python validators and capture exit status. |
| Browser | Can open the exact CHARMM-GUI job URL without fabricating requests. |
| Authenticated session | Can reuse a user-authenticated session without reading credentials. |
| Page capture | Can capture URL, title, visible scientific fields, warnings, and screenshots. |
| Download control | Can start once, observe transfer state, and identify the saved path. |
| Native dialogs | Can handle upload/save dialogs, or explicitly hand them to the operator. |
| Durable wait/resume | Can preserve job ID, step, action lock, and next check time. |

## Routing Rules

- Without file and command access, provide instructions only; do not claim a
  local audit or package validation.
- Without an authenticated browser path, perform local audits only and stop
  before website submission.
- Without page capture, require an operator screenshot and parameter record
  before each irreversible submit.
- Without native-dialog control, let the operator upload/download, then resume
  from the saved local artifact.
- Without durable wait/resume, write a redacted handoff containing the exact
  job, step, one allowed action, action lock, and stop conditions.
- Never replace a missing capability with invented tool names, hidden HTTP
  requests, credential extraction, or a higher-confidence status.

All local validation scripts remain usable independently of browser support.

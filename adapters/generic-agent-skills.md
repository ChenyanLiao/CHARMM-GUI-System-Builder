# Generic Agent Skills Adapter

Use this adapter when the runtime has no dedicated file in `adapters/`.

## Capability Handshake

Before acting, classify each capability as `available`, `operator_required`, or
`unavailable`:

Persist the result from
`templates/RUNTIME_CAPABILITY_MANIFEST_TEMPLATE.json` inside the run directory;
do not leave any capability as `unknown` before route selection.

| Capability | Minimum evidence |
|---|---|
| File access | Can read inputs and write only inside the selected run directory. |
| Command execution | Can run Python validators and capture exit status. |
| Structured decision support | Can render Routine/Contextual/Critical records and preserve user answers. |
| Official API | Can reach only registry-backed endpoints and keep tokens in memory. |
| Credential broker | Can use a local OS vault reference without exposing the secret. |
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
  before browser submission; a documented official API capability may still be
  used if its own credential and authorization gates pass.
- Without page capture, require an operator screenshot and parameter record
  before each irreversible submit.
- Without native-dialog control, let the operator upload/download, then resume
  from the saved local artifact.
- Without durable wait/resume, write a redacted handoff containing the exact
  contract hash, job, step, one allowed action, submission lock, and stop
  conditions.
- Without a credential broker, use manual login. Never replace it with a
  plaintext file, environment dump, browser-cookie extraction, or chat secret.
- Never replace a missing capability with invented tool names, hidden HTTP
  requests, credential extraction, or a higher-confidence status.

All local validation scripts remain usable independently of browser support.

# Capability Matrix

`Supported` below means the package can be discovered and its decision,
contract, and local validation code can run. Website automation and documented
API access remain conditional on configured tools, a safe authentication path,
and contract-bound authorization.

| Runtime | Decision/contract core | Official API | Authenticated browser | OS credential vault | Recommended mode |
|---|---|---|---|---|---|
| Codex | Supported | Conditional on network and authorization | Conditional on enabled browser/Chrome tools | macOS Keychain on local Mac | Full or operator-assisted test-only |
| Claude Code | Supported | Conditional | External browser MCP/Playwright/computer-use required | Host-dependent; do not transfer to cloud | Local validation plus configured route |
| OpenClaw | Supported with terminal | Conditional on host | Conditional on browser capability and host | Host-local only | Full or delegated browser step |
| Hermes Agent | Supported with terminal | Conditional on host | Conditional on browser toolset and host | Host-local only | Local validation plus configured route |
| Generic Agent Skills client | Client-specific | Client-specific | Client-specific | Client-specific | Capability-gated |

## Capability Levels

- **Level 1: Instruction only.** The runtime loads `SKILL.md` but cannot access
  files or commands. It may produce a checklist only.
- **Level 2: Local validation.** File and Python access permit input/archive/
  package audits and build-contract preparation, but no website action.
- **Level 3: Browser assisted.** The runtime can inspect forms and preserve an
  authenticated same-job session; native dialogs may remain human actions.
- **Level 4: Audited end to end.** Browser, page capture, durable waits,
  downloads, and local validation are all available. Scientific production
  approval is still a separate human/expert gate.

No capability level authorizes credential capture, CAPTCHA/MFA bypass,
`gmx mdrun`, or automatic production approval.

The matrix is descriptive, not run evidence. Each run must materialize
`templates/RUNTIME_CAPABILITY_MANIFEST_TEMPLATE.json` and resolve every
capability before selecting an official-API, audited-browser, operator-assisted,
or validation-only route.

Execution-module maturity is separate from runtime capability. Consult
`community/MODULE_MATURITY_REGISTRY.json`; an Agent at Level 4 must still treat
a Beta API adapter as Beta and a full builder as Browser-Assisted.

# Capability Matrix

`Supported` below means the package can be discovered and the local validators
can run. Website automation remains conditional on the runtime's configured
tools and a human-authenticated session.

| Runtime | Discovery path | Files and Python | Authenticated browser | Native dialogs | Recommended mode |
|---|---|---|---|---|---|
| Codex | `~/.codex/skills/...` | Supported | Conditional on enabled browser/Chrome tools | Conditional on computer control | Full workflow or operator-assisted |
| Claude Code | `~/.claude/skills/...` or project skill | Supported | External browser MCP/Playwright/computer-use required | Usually operator-assisted | Local validation plus configured browser |
| OpenClaw | workspace, `.agents/skills`, or `~/.openclaw/skills` | Supported when terminal is enabled | Conditional on browser capability and host | Host-dependent | Full workflow or delegated browser step |
| Hermes Agent | `~/.hermes/skills/...` or `external_dirs` | Supported when terminal toolset is enabled | Conditional on browser toolset and host | Host-dependent | Local validation plus configured browser |
| Generic Agent Skills client | Client-specific | Client-specific | Client-specific | Client-specific | Capability-gated |

## Capability Levels

- **Level 1: Instruction only.** The runtime loads `SKILL.md` but cannot access
  files or commands. It may produce a checklist only.
- **Level 2: Local validation.** File and Python access permit input/archive/
  package audits, but no website action.
- **Level 3: Browser assisted.** The runtime can inspect forms and preserve an
  authenticated same-job session; native dialogs may remain human actions.
- **Level 4: Audited end to end.** Browser, page capture, durable waits,
  downloads, and local validation are all available. Scientific production
  approval is still a separate human/expert gate.

No capability level authorizes credential capture, CAPTCHA/MFA bypass,
`gmx mdrun`, or automatic production approval.

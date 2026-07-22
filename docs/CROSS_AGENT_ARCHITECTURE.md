# Cross-Agent Architecture

## One Core, Multiple Adapters

`SKILL.md` is the only authoritative scientific and operational workflow. It
defines decision risk, build-contract, evidence, status, safety, and validation
gates.
Platform adapters only answer three runtime questions:

1. Where is the skill discovered?
2. Which available tool maps to file, terminal, browser, capture, download, and
   native-dialog capabilities?
3. Where must the agent stop for an operator handoff?

An adapter must not weaken a gate, duplicate the workflow, change scientific
defaults, or claim that a missing tool succeeded.

## Shared Execution Model

Every runtime uses the same sequence:

```text
Input audit -> rule-pack inventory -> guided decisions -> locked contract
-> capability router -> official API or audited browser -> evidence ledger
-> contract-derived validation -> technical status
```

Before that sequence, the adapter writes a run-local runtime capability
manifest from `templates/RUNTIME_CAPABILITY_MANIFEST_TEMPLATE.json`. The
manifest records evidence for file, command, browser, capture, upload, download,
native-dialog, network, vault, and durable-resume capabilities. Route selection
must not rely on an agent product name alone.

`TARGET_PROFILE.yaml` is reusable evidence, not approval. A locked build
contract is run-specific and immutable. Approvals are append-only records bound
to the contract hash. Runtime adapters may translate tool calls but cannot alter
parameter values, risk levels, authorization scope, or expected outputs.

## Portability Boundary

Agent Skills compatibility means a client can discover and load the core
instructions. It does not guarantee that the client can operate an authenticated
website, control a native dialog, wait for a backend job, or access the machine
holding the files. Each run starts with the capability handshake in
[`generic-agent-skills.md`](../adapters/generic-agent-skills.md).

Credential references and signing keys are host-local. Do not copy a Keychain
reference, secret, browser session, or authorization to another host and assume
equivalent assurance. A cross-agent handoff contains only the contract hash,
job ID, current gate, one allowed action, and redacted evidence locations.

## Update Rule

Behavioral and scientific changes go into `SKILL.md`, versioned rule packs,
scripts, checklists, or references once. Runtime-only changes go into the
relevant adapter and install guide. Community evidence creates a reviewed rule
proposal rather than an automatic edit. Every release validates version
consistency and the official Agent Skills frontmatter rules.

# Cross-Agent Architecture

## One Core, Multiple Adapters

`SKILL.md` is the only authoritative scientific and operational workflow. It
defines evidence gates, status vocabulary, safety boundaries, and validators.
Platform adapters only answer three runtime questions:

1. Where is the skill discovered?
2. Which available tool maps to file, terminal, browser, capture, download, and
   native-dialog capabilities?
3. Where must the agent stop for an operator handoff?

An adapter must not weaken a gate, duplicate the workflow, change scientific
defaults, or claim that a missing tool succeeded.

## Portability Boundary

Agent Skills compatibility means a client can discover and load the core
instructions. It does not guarantee that the client can operate an authenticated
website, control a native dialog, wait for a backend job, or access the machine
holding the files. Each run starts with the capability handshake in
[`generic-agent-skills.md`](../adapters/generic-agent-skills.md).

## Update Rule

Behavioral and scientific changes go into `SKILL.md`, scripts, checklists, or
references once. Runtime-only changes go into the relevant adapter and install
guide. Every release validates version consistency and the official Agent
Skills frontmatter rules.

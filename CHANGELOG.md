# Changelog

## 1.1.1 - 2026-07-20

- Consolidates duplicate optional JSON metadata loading in the Skill package
  validator without changing its public output or validation behavior.
- Adds regression coverage for malformed compatibility and provenance JSON.
- Keeps all scientific gates unchanged, including `production_ready=false`
  and `no_mdrun=true`.

## 1.1.0 - 2026-07-18

- Establishes `v1.1.0` as the Cross-Agent Edition following the initial
  `v1.0.0` release.

- Adds Cross-Agent Edition adapters for Codex, Claude Code, OpenClaw, Hermes
  Agent, and generic Agent Skills clients while retaining one core `SKILL.md`.
- Adds platform installation guides, a capability matrix, and explicit
  capability-gated browser handoff rules.
- Adds Agent Skills frontmatter metadata, a standard-library package validator,
  compatibility metadata, and cross-agent regression tests.
- Adds official `skills-ref` validation to CI using a pinned upstream revision.

## 1.0.0 - 2026-07-18

- Initial public release.
- Separates backend, page, download, archive, package, custom-parameter,
  preprocessing, and scientific approval states.
- Adds content-based tar/tar.gz/HTML/partial classification and archive safety
  checks.
- Adds GROMACS component, ligand charge, and custom dihedraltype validation.
- Adds synthetic tests for interrupted downloads, unsafe archives, intermediate
  packages, and alternate custom-ligand layouts.

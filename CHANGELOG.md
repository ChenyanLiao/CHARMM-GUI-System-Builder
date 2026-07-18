# Changelog

## 6.1.0 - 2026-07-18

- Adds Cross-Agent Edition adapters for Codex, Claude Code, OpenClaw, Hermes
  Agent, and generic Agent Skills clients while retaining one core `SKILL.md`.
- Adds platform installation guides, a capability matrix, and explicit
  capability-gated browser handoff rules.
- Adds Agent Skills frontmatter metadata, a standard-library package validator,
  compatibility metadata, and cross-agent regression tests.
- Adds official `skills-ref` validation to CI using a pinned upstream revision.

## 6.0.0 - 2026-07-18

- Initial public release.
- Separates backend, page, download, archive, package, custom-parameter,
  preprocessing, and scientific approval states.
- Adds content-based tar/tar.gz/HTML/partial classification and archive safety
  checks.
- Adds GROMACS component, ligand charge, and custom dihedraltype validation.
- Adds synthetic tests for interrupted downloads, unsafe archives, intermediate
  packages, and alternate custom-ligand layouts.

# Community Validation And Module Maturity

## Maturity Levels

- `Stable`: automated tests, maintainer reproduction, two independent external
  reproductions, complete recovery documentation, and no unresolved
  high-severity defect.
- `Beta`: implemented and tested, but the Stable evidence gate is incomplete.
- `Browser-Assisted`: requires audited interactive website operation.
- `Validation-Only`: can inspect outputs but cannot safely execute the module.
- `Unsupported`: no verified route.

The current registry is
[`community/MODULE_MATURITY_REGISTRY.json`](../community/MODULE_MATURITY_REGISTRY.json).
Maturity is evidence-based and never inherited from an older release label.

## How To Contribute A Validation

Start from
[`VALIDATION_REPORT_TEMPLATE.yaml`](../community/VALIDATION_REPORT_TEMPLATE.yaml).
Reports may include the builder, target category, Skill version, redacted
contract hash/summary, job step, warnings, error excerpts, artifact hashes, and
technical result. Do not include:

- passwords, cookies, API/session tokens, MFA/CAPTCHA data, or login HTML;
- private or identifying screenshots;
- unpublished structures without authorization;
- license-restricted complete CHARMM-GUI output packages;
- a claim that a technical pass proves binding, efficacy, or production
  readiness.

Contributors may request public credit in `COMMUNITY_VALIDATORS.md`. Validation
does not imply paper authorship or ownership transfer.

## Rule Change Lifecycle

```text
Validation report
-> Rule change proposal
-> Maintainer review
-> Tests and reproduction
-> New versioned rule pack
```

Use
[`RULE_CHANGE_PROPOSAL_TEMPLATE.yaml`](../community/RULE_CHANGE_PROPOSAL_TEMPLATE.yaml).
Community evidence never changes a recommendation automatically and never edits
an already locked contract. A merged rule version affects future contracts
only.

## Stable Promotion Gate

A maintainer may mark a module Stable only when the registry records:

1. passing unit and integration tests;
2. a maintainer reproduction with redacted evidence;
3. at least two independent external groups;
4. zero unresolved high-severity defects;
5. complete documentation, failure recovery, and safety boundaries.

Until every item is recorded, the module remains Beta or Browser-Assisted.

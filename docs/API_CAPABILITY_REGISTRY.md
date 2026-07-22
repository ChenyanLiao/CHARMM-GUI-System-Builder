# Official API Capability Registry

## Scope

CHARMM-GUI System Builder is still a system-building skill. The API adapter is
one execution route for capabilities that CHARMM-GUI publicly documents; it is
not a substitute for input audit, parameter review, build contracts, browser
steps, or final package validation.

The machine-readable registry is
[`rules/capabilities/official_api.json`](../rules/capabilities/official_api.json).
At v2.1.0 it recognizes only:

| Capability | Method and endpoint | Route | Maturity |
|---|---|---|---|
| Login | `POST https://charmm-gui.org/api/login` | Official API | Beta |
| Job status | `GET https://charmm-gui.org/api/check_status?jobid=...` | Official API | Beta |
| Job download | `GET https://charmm-gui.org/api/download?jobid=...` | Official API | Beta |
| Quick Bilayer | `POST https://charmm-gui.org/api/quick_bilayer` | Official API | Beta |
| PDB Reader submission | No confirmed public endpoint | Audited browser | Browser-Assisted |
| Ligand Reader submission | No confirmed public endpoint | Audited browser | Browser-Assisted |
| Protein/Membrane Builder | No confirmed public endpoint | Audited browser | Browser-Assisted |
| Solution Builder | No confirmed public endpoint | Audited browser | Browser-Assisted |

Official sources:

- <https://www.charmm-gui.org/?doc=api>
- <https://www.charmm-gui.org/?doc=api&module=quickb>

An endpoint must not enter the registry because it appeared in browser network
traffic, a page form, a forum post, or a third-party script. It needs a current
official source and a reviewed parameter schema.

## Safe Routing

1. Complete input audit and Guided Decision Protocol.
2. Lock `APPROVED_BUILD_CONTRACT.json` and verify its hash.
3. Select a capability whose route and maturity are recorded in the registry.
4. For a side effect, verify a scoped, unexpired execution authorization and
   remaining submission count.
5. Capture a sanitized request summary, submit once, and persist a returned job
   ID immediately.
6. Reuse only that contract-bound job ID for authorized status checks, recovery,
   and download; reject a caller-supplied mismatch.

If the POST transport fails after bytes may have been sent and no job ID was
captured, set `submission_state=submission_uncertain`. Do not retry until Job
Retriever or other authorized evidence establishes whether a job exists.

## Quick Bilayer Boundary

`scripts/charmmgui_api_client.py` validates only the documented Quick Bilayer
field allowlist. Every live field must have a v2.1 rule binding and equal the
locked contract; dry summaries may display documented fields that are not yet
enabled for live submission. Protein use requires an existing PDB Reader job ID
and hashed input provenance in the contract. The
presence of a `heteroatoms` field does not prove that a custom ligand topology
will be transferred correctly. Protein-ligand Quick Bilayer remains Critical
until the final package proves the intended ligand and parameters.

The CLI defaults to request summaries. Live network access requires
`--allow-live`; Quick Bilayer additionally requires a locked test-only contract
and a valid signed authorization plus the run's `RUN_STATE.json`. Contract,
authorization, exact parameter, input-provenance, and remaining-submission
checks occur before login. Status and download also require the same locked
contract, signed action scope, run state, and recorded job ID. A successful
response atomically records its job ID; a missing or lost response atomically
records `submission_uncertain` and forbids automatic retry. v2.1.0 does not
permit API production submission.

## Test Tiers

- Offline tests use fictional credentials and mocked HTTP responses only.
- A read-only live smoke test may check official documentation, status, or an
  already authorized download without creating a job.
- A minimal Quick Bilayer live test requires one explicitly authorized public
  membrane-only `test_only` submission.
- Full protein/ligand builders remain audited-browser workflows.

No API success automatically implies scientific correctness or production
approval.

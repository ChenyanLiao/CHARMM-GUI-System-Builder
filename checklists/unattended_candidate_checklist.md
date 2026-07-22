# Unattended Candidate Checklist

## Continuous execution

- [ ] `RUN_STATE.json` uses schema version `2.1`.
- [ ] A locked `APPROVED_BUILD_CONTRACT.json` hash is recorded.
- [ ] Every side-effecting action is within a valid, unexpired authorization.
- [ ] Credential storage, if enabled, uses only an opaque OS-vault reference.
- [ ] API tokens are memory-only and login evidence capture is disabled.
- [ ] `next_allowed_action` is either allowlisted or explicitly treated as a human gate.
- [ ] A ready routine action is executed immediately rather than reported as waiting.
- [ ] The active task remains alive during low-frequency backend polling.
- [ ] `continuation_guard.py RUN_STATE.json` is run before yielding.
- [ ] Exit code `20` is treated as MUST_CONTINUE, not as a failed test.
- [ ] The task yields only for authentication, scientific review, fatal/stalled state, production approval, or verified completion.

- [ ] Candidate/test-only mode is explicit.
- [ ] Existing authenticated Chrome profile is selected.
- [ ] Job ID and resumable URL are recorded before waiting.
- [ ] `submission_state` and submission count are updated immediately after the
      single submission.
- [ ] A lost side-effecting response becomes `submission_uncertain`, not an
      automatic retry.
- [ ] Authentication, browser, page, and backend states are recorded separately.
- [ ] Download state and closure gates are recorded separately from backend state.
- [ ] Required products for the current step are listed in `RUN_STATE.json`.
- [ ] Routine polls use compact JSON rather than full screenshots.
- [ ] Output size and tail digest are compared with the previous poll.
- [ ] Network errors use cooldown and Job Retriever recovery without resubmission.
- [ ] Human notification is reserved for defined gates and stop conditions.
- [ ] PPM orientation remains an explicit human review gate.
- [ ] Custom ligand parameters remain unverified until final 5/5 package validation.
- [ ] Dynamic form controls are changed one at a time and dependent fields are re-read.
- [ ] Already selected force-field controls are not re-selected unnecessarily.
- [ ] System-size preview has nonzero intended lipid counts before submission.
- [ ] Final download is inspected for HTML/non-tar content before package validation.
- [ ] `workflow_complete` is false until archive/package and required custom-ligand gates pass.
- [ ] `production_ready` remains false.
- [ ] `gmx mdrun` is not executed.

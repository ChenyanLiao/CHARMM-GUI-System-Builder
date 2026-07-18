# Continuous Execution Reference

## Contract

`unattended_candidate` is a continuous active-task contract, not a claim that a
browser daemon exists. The Codex task controlling the browser must remain alive
until a valid pause or terminal gate is reached.

After every page observation or backend probe:

1. Update `RUN_STATE.json`.
2. Run `classify_charmmgui_state.py`.
3. For `ADVANCE_ONE_STEP`, capture required evidence, verify the DOM and jobid,
   then execute `next_allowed_action` exactly once.
4. For a wait or retry decision, keep the task alive at the recorded
   low-frequency interval. Do not ask the user to watch routine polling.
5. Before yielding or sending a final response, run `continuation_guard.py`.
6. After backend input generation completes, continue through authenticated
   download inspection, package validation, and required custom-injection
   validation. Backend completion alone is not a terminal gate.

```bash
python3 scripts/classify_charmmgui_state.py /path/to/RUN_STATE.json
python3 scripts/continuation_guard.py /path/to/RUN_STATE.json
```

Exit code `20` from the guard means MUST_CONTINUE. It is not a test failure.

## Valid Pause Conditions

Yield only for:

- login, MFA, CAPTCHA, Touch ID, or OS credential confirmation;
- membrane-orientation review;
- custom topology/parameter ambiguity or an unexpected scientific default;
- fatal or explicitly stalled backend state;
- explicit production approval;
- verified final workflow completion.

For schema V6, verified completion requires `closure_gates.archive_verified`
and `closure_gates.package_validated`. If custom ligand parameters are expected,
also require `closure_gates.custom_ligand_verified`. A true
`workflow_complete` flag cannot override false closure gates.

Routine actions such as `SUBMIT_SYSTEM_SIZE`, `SUBMIT_PACKING`,
`SUBMIT_COMPONENT_BUILD`, `SUBMIT_ASSEMBLY`, and
`SUBMIT_INPUT_GENERATION` are not human gates.

Local read-only actions such as `VALIDATE_DOWNLOAD_ARTIFACT`,
`VALIDATE_FINAL_PACKAGE`, and `VERIFY_CUSTOM_LIGAND_INJECTION` do not require a
connected browser and must be consumed before yielding.

## Browser Boundary

The skill never stores credentials and does not inspect password stores,
cookies, session storage, or tokens. Actual page actions remain in the active
Codex browser-control loop. That loop must not terminate while the continuation
guard says to continue.

If browser control disconnects, preserve the jobid and state. Retry within the
documented cooldown budget or resume through the exact bookmark/Job Retriever.
Do not resubmit the previous page merely because the visible tab is stale.

If the saved final file is HTML or another non-tar artifact, preserve its path,
size, and hash, set the download state to invalid, and return to the same
authenticated final page. Do not start a new CHARMM-GUI job and do not record
the HTML body.

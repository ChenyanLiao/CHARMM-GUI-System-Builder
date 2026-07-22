# Failure Recovery Checklist

- [ ] Record jobid.
- [ ] Record build-contract hash, execution route, and module maturity.
- [ ] Record step.
- [ ] Save screenshot.
- [ ] Save page HTML/DOM or parameter JSON if possible.
- [ ] Save exact warning/error excerpt.
- [ ] Check required previous-step files.
- [ ] Check whether current output file is growing.
- [ ] Check last 50-100 lines of output.
- [ ] Do not repeatedly click `Next`.
- [ ] If a POST may have succeeded without returning a job ID, set
      `submission_uncertain` and inspect existing-job evidence before retrying.
- [ ] Do not use fallback GET as proof of valid submission.
- [ ] Use Job Retriever if browser state is lost.
- [ ] Classify authentication, browser, page, and backend state separately.
- [ ] Treat `ERR_EMPTY_RESPONSE` as a transient page/network failure, not proof of backend failure.
- [ ] If backend output has normal termination while the page is stale, resume by jobid after cooldown instead of resubmitting.
- [ ] Exhaust at most three transient network retries before requesting assistance.
- [ ] Classify a `.tgz` containing HTML as a download failure, not a builder failure.
- [ ] Do not copy invalid-download HTML bodies into logs or reports.
- [ ] Re-download from the same authenticated final job page; do not create a new job.
- [ ] If stalled, stop and create a new test-only job only after recording the failure.
- [ ] Append reusable failure to `examples/known_failure_modes.md`.

# Browser Form And Download Recovery

## Contents

- Form mutation rules
- Preview and confirmation boundaries
- Backend versus page state
- Final download acquisition
- Recovery decision table
- Redacted synthetic evidence

## Form Mutation Rules

Treat CHARMM-GUI forms as dynamic state, not static HTML.

1. Capture the exact job ID, URL, step, selected controls, and dependent fields.
2. Change only a value that differs from the locked build contract.
3. After changing a dropdown, radio button, or checkbox that can trigger page
   JavaScript, re-read every dependent control before making another change.
4. Do not re-select an already selected force field. In job `9000000004`,
   programmatically selecting the existing CHARMM36m value reset dynamic Step 5
   controls. Reloading a clean same-job page and changing only GROMACS preserved
   the intended state.
5. Confirm controls from DOM/accessibility state, not nearby text.
6. Suppress capture for the entire login operation. On all other pages, exclude
   password, token, session, cookie, CSRF, auth, JWT, MFA, CAPTCHA, and
   credential fields from snapshots.
7. Compare recommendation, locked value, final DOM value, safe hidden value,
   and generated output. Mark drift `WRONG`, `MISSING`, `UNKNOWN`, `RISK`, or
   `BLOCK_PRODUCTION`; do not continue on material drift.

Use a before/after field diff for each dependency-changing mutation. If an
unrelated field changes, stop and restore the page from the same-job URL rather
than continuing with mixed state.

## Preview And Confirmation Boundaries

Do not equate a calculation preview with a submitted step.

- A system-size preview must show nonzero intended lipid counts before submit.
- In job `9000000004`, calculating before entering the XY initial guess produced
  a no-lipid preview. It was discarded. The corrected 160 A preview produced
  108 CHL1 and 252 POPC per leaflet.
- Record a confirmation dialog as a separate UI event tied to the same intended
  action. Do not count it as permission to submit the page twice.
- Set the submitted-action lock as soon as the effective submit handler returns
  or navigation begins.

## Backend Versus Page State

Keep `page_state`, `backend_state`, and `download_state` independent.

- A stale running banner does not override `NORMAL TERMINATION` plus required
  backend files.
- `ERR_EMPTY_RESPONSE` after a single submit does not prove rejection. In job
  `9000000004`, Step 6 navigation failed while `step5_input.out` later reached
  normal termination.
- A visually advanced page does not prove the required PSF/CRD/PDB exists.
- Reopen the same job only after preserving the submitted-action lock and
  checking backend evidence.
- A browser network error does not change a normally completed backend into a
  failed CHARMM-GUI build. Do not rerun Step 5/6 merely because transfer failed.

## Final Download Acquisition

Treat the download as an authenticated browser action followed by a local
artifact gate.

1. Confirm the final page is authenticated, the exact job ID matches, the
   running banner is absent, and the download link is visible.
2. Click the webpage download link once. Use the native save panel if needed.
3. If Chrome interrupts the transfer, resume only the newest record at the top
   of Chrome's download panel. Do not click `download.tgz` on the page again.
4. Do not infer resumability from the run directory alone. Chrome can remove a
   `.crdownload` while retaining a resumable download record in its UI.
5. After repeated Chrome transport failures, use Safari with the same completed
   job and authenticated account. Do not rerun the CHARMM-GUI job.
6. Safari may automatically expand `download.tgz` and save `charmm-gui.tar`.
   The displayed transfer size can be compressed bytes while the on-disk tar is
   much larger.
7. Prefer the run download directory. If the browser must finish in its default
   Downloads folder, validate the artifact type first, then move it to
   `run/04_Downloads` without overwriting an existing final archive.
8. Wait for transfer completion; never validate `.crdownload`, `.part`, or
   another partial artifact as final.
9. Run:

   ```bash
   python3 scripts/inspect_charmmgui_download.py /path/to/download \
     --json-out /path/to/download_inspection.json
   ```

10. Continue only when `classification` is `valid_final_candidate`.

Do not trust the extension or browser-reported size. Run `file` and the
inspector, which detects gzip, bzip2, xz, and uncompressed tar from content.
Never choose `tar -tf` versus `tar -tzf` from the suffix. Chrome or a save-panel
flow may save an authenticated HTML response under a `.tgz` name. Do not record
the HTML body, cookies, account context, or session values.

The inspector reports:

- `archive_member_count`: every tar member, including directories and links;
- `archive_regular_file_count`: regular files only;
- size, modification time, SHA-256, content-defined compression;
- `.gro/.top/.itp/.mdp` counts and GROMACS entry count;
- unsafe member paths, unsafe links, and special files;
- one of `valid_final_candidate`, `intermediate`, `invalid_html`, `partial`,
  `unsafe_archive`, `corrupt_archive`, or another explicit invalid class;
- a single `recommended_next_action`.

## Recovery Decision Table

| Observation | Classification | Action |
|---|---|---|
| Backend output still grows | backend running | Wait at the configured interval. |
| Page says running, backend is normal and products exist | stale page | Reopen the same job; do not resubmit. |
| Navigation returns `ERR_EMPTY_RESPONSE`, backend status unknown | transient page failure | Preserve lock, wait, and probe backend. |
| API/browser POST may have succeeded but no job ID was captured | `submission_uncertain` | Inspect Job Retriever or authorized existing-job evidence; do not retry automatically. |
| Chrome shows network failure but backend is normal | transfer failure | Resume only the newest Chrome record; do not click the page link again. |
| Repeated Chrome interruptions | browser-path failure | Open the same completed job in Safari; do not rerun Step 5/6. |
| Final file begins with HTML or contains a CHARMM-GUI login page | `invalid_html` | Preserve hash/size, re-download from authenticated final page. |
| Filename ends in `.crdownload`, `.part`, or `.partial` | `partial` | Wait or resume the latest browser download; do not inspect as final. |
| File is a readable tar but lacks `.gro/.top/.itp/.mdp` | `intermediate` | Do not call it final; inspect the selected engine and job stage. |
| Tar has absolute, traversal, unsafe link, device, or FIFO members | `unsafe_archive` | Quarantine; do not extract. |
| Archive contains required files but custom payload mismatches | custom injection failure | Stop; do not use automatic-CGenFF fallback as the optimized build. |
| Package passes counts but strict `grompp` fails | topology/preflight failure | Repair segmentation/topology and rebuild; never use `-maxwarn` as pass evidence. |

## Redacted Synthetic Evidence

The following reusable facts are redacted from prior runs. Job IDs, target
names, ligand names, and local paths are synthetic:

- Job `9000000001`: Step 3 packing did not create head PSF/CRD; Step 4 failed.
- Job `9000000002`: final test-only archive was real and complete, but strict
  preprocessing exposed one-segment cross-gap topology risk.
- Job `9000000003`: PDB Reader/orientation gate remained stalled despite normal
  early backend output.
- Job `9000000004`: nine-segment/custom-parameter candidate reached Step 6
  backend normal termination. A 6,034-byte `.tgz` was HTML, but that was a
  transfer failure rather than a backend build failure. Reusing the same job in
  Safari produced a 758,997,504-byte POSIX tar. The package passed GROMACS
  component validation and custom injection checks at 46/46 converted terms,
  5/5 primary terms, and 3/3 function-9 target connections. Its status remains
  `Candidate_Package_Validated`. Strict `grompp` and any applicable custom-
  ligand verification are separate gates before
  `Technical_Pass_Not_Production_Approval`; neither status is production-ready.

These examples are recovery patterns, not production approval.

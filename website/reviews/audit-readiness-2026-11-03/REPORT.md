# Audit readiness: remove a helper fetch and preserve failure state

The owner authorized addressing the remaining website work after PR #17 merged. This milestone concerns the audit-readiness follow-up. It starts from website main `b3436760754d231c3866e1dd1910833ba33c38da`, which includes the published Distributed Systems, Backend for Mobile, Security, Release Engineering and separate MSD Authentication updates. The current Q&A experience remains unchanged under the owner's explicit decision.

## Evidence and scope

PR #17's fresh full-site run failed on one of 249 pages. Caching Library reported `Page readiness timed out`, with a complete document, its expected title and no recorded JavaScript errors. A separate focused check passed. The failed full-run evidence remains at `/private/tmp/audit-tools-validation/main-1ca9c8e-head-8310972-2026-11-03/`; it was not overwritten by the focused result. That old evidence does not record the route marker, source identity, inspector type or failed resource URLs, so the precise original cause cannot be reconstructed. This change does not claim otherwise.

The old QA copy loaded the read-only inspector from an additional external script in each iframe. The readiness predicate required that function before it could inspect the page. A failed inspector request could therefore leave a complete document waiting for a function that would never appear, while resource-load errors were absent from the JavaScript-error array.

The prepared QA documents now embed the inspector directly in their initial head script. It is trusted local audit infrastructure, separate from the reader's own assets. The preservation-tampering fixtures also receive the inspector inline. There is no additional inspector request or console eval, and the source chapter files and deployable reader output are unchanged.

## Failure handling

Reader assets remain real resource requests. The QA error listener now records failed script, stylesheet or image element URLs separately from JavaScript exceptions. Once the expected document is complete, missing source identity, a missing inspector and recorded resource failures fail explicitly. A document that does not finish still has the same thirty-second readiness limit. Every failed page records the expected route, actual route, document state, source identity, inspector type and resource errors.

No automatic retry, timeout increase, failure suppression or replacement of failed full-run evidence is introduced. This is a targeted removal of an extra QA dependency plus better diagnostics; a future timeout caused by a different mechanism must still fail and retain its observed state.

## Controlled browser checks

The new `dev.py readiness` command prepares a disposable copy and executes four real Chromium cases. The intact Caching Library page passes with preservation checks enabled. Deliberately missing reader JavaScript, missing inspector and missing source identity each fail with the corresponding diagnostic before the readiness budget expires. Every case verifies zero external inspector requests. The missing-reader-script case also requires the exact failed script URL and tag in the recorded state. All four cases pass.

All thirty-one existing preservation-tampering fixtures pass with inline instrumentation. They continue detecting missing, duplicated, hidden and changed original content and answers. The four cases and tampering checks are controlled regressions, not a claim that the previous intermittent timeout has been reproduced with its original cause.

The HTML Standard's iframe, script-processing and document-completion contracts were consulted. The new behavior is confined to disposable QA copies and the local audit commands. Headless Chromium does not certify other engines, physical devices or screen readers. No new chapter example is compiled or real Android integration certified by this tooling change. The unchanged Java examples retain their existing compile/behavior check. Final full-site audit, frame, CI and publication-gate results are recorded below after the run on these inputs.

The final full run passes all six suites on these inputs: browser 249/249 pages, code readability 8,200/8,200, original Q&A pairing 1,481/1,481, Binder 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering 31/31. This is one new full run after the instrumentation changes, separate from the retained earlier failed run. The result demonstrates a clean current integration; it does not retroactively establish what failed in the older capture.

Build preservation passes 249 pages and 30,397 original units. Figure validation passes 220 models. The frame check passes 238 chapter pages, 218 figures, 137 relationship maps and 3,826 labels. CI passes all forty-six website tests, thirty-one docs-checker tests, seventy-four exact Java examples, documentation checks and fifteen browser-script syntax checks. The real `dev.py readiness` wrapper passes all four controlled browser cases. Fresh fingerprints and the real project-path publication build are checked before pushing.

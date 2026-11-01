# Observability linked-source repair

## Scope and reader impact

The published SLO and Alerting pages link to an unpublished crash-gating chapter in this website repository. That snapshot predated source PR #72, so readers following the SLO page's matching-policy link could not find `evaluate_crash_gate`. This change refreshes `release-engineering/crash-rate-gating.md` and `milestones.md` from the exact bytes of approved source commit `7666569cf77db7616d43f05cf041c438cb947035`. Release Engineering remains unpublished; no tree registration or lesson is added.

The snapshot metadata records the reference commit and both SHA256 hashes. Review-data validation now enforces those two paths and their hashes in addition to the existing checks. No gate requirement or correction-source validation has been relaxed. The crash-gating file contains `evaluate_crash_gate` and `## 4. The Auto-Halt Workflow`; it contains neither “1 in 200 sessions” nor `vitals_crashrate.py`. The milestones snapshot includes the `observability/slos.md` Currency Watchlist row.

## Snapshot and link verification

The outbound scan covers the twelve Observability pages and three corrected Android pages in the generated output. It found twenty unique GitHub `blob/main` file targets. After the refresh, seventeen match the approved source commit. The three remaining differences are the deliberately frozen Android snapshots: `android/networking-and-security/retrofit-and-okhttp.md`, `android/performance/anrs.md`, and `android/performance/memory-management-and-leaks.md`. These files were changed by source PR #72, but the owner's instructions explicitly preserve their raw website snapshots and apply corrections through the existing overlay. No other differing target was found.

All twelve Observability snapshots retain their previous hashes. Each corrected Android input still matches its approved `source_sha256`. The generated original-unit manifest is byte-identical to the pre-change manifest across all 207 published pages, preserving all 26,240 original units. Both generated Observability source links resolve to the refreshed repository path. Anonymous requests to the two candidate-branch raw URLs returned HTTP 200 and bytes identical to the approved source; those results are recorded in `public-candidate-files.json`.

Source PR #72 returned HTTP 404 to an anonymous request. Its hyperlink has therefore been removed from the three supplemental correction source lists. Their correction histories retain the PR number and full merge commit as plain provenance text, alongside the existing public official-source links. All three lists remain nonempty and pass the unchanged validation. A focused Chrome check opened each correction history at 320 and 375 CSS pixels: all six checks passed, with the full provenance visible, no private PR hyperlink, and no page overflow.

## Validation

The local build, FigureMap validation, frame checks and CI command pass. They cover 207 rendered pages, 167 diagram models, 200 chapter pages in the frame audit, twenty website tests, thirty-one docs checker tests, the docs gate and ten browser-script syntax checks. The fresh six-audit run passes: browser 207/207 pages, code 7,112/7,112 blocks, Q&A 1,299/1,299 pairs, binder 560/560, motion 13/13, refinement 69/69, UX 278/278 and tampering 31/31. The publication gate uses this folder's evidence. These checks validate the candidate build; they do not establish that an unmerged change is already live.

## Limits and owner follow-up

Safari, Firefox, screen readers and physical devices were not tested. Phone-width checks used Chrome viewport emulation. No Android sample was compiled or executed, and no new fact-check of the frozen Android source text was performed. The source PR remains unavailable without login; the public provenance and official references avoid depending on that private page.

This repair is submitted as an unmerged website PR. After the owner merges it, the owner must confirm the GitHub Pages deployment succeeds and re-open the live SLO matching-policy link and Alerting source link. Confirm that the destination contains the corrected function and anchor, and that the live milestones link exposes the new watchlist row. Those post-merge checks remain outstanding until the candidate reaches `main`.

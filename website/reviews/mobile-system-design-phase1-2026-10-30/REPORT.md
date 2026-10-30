# Mobile System Design Phase 1 publication review

## Scope and source

This milestone adds the seven Phase 1 chapters to the reader website while keeping the existing Offline Sync pilot live. The five method and cross-cutting practice chapters use the normal chapter layout. Performance and Versioning & Backward Compatibility use the interview walkthrough layout because each presents a timed design problem, trade-offs, and follow-up questions. Phase 2 remains linked to the Markdown on GitHub; its seven chapters are refreshed in the website repository but are not rendered as reader pages in this release.

All 14 Phase 1 and Phase 2 chapter snapshots were compared byte for byte with original playbook merge commit `5ff8d44` (source PR #64). All 14 matched, and `source-snapshot.json` records their hashes. The website does not edit or rearrange that original text. The build's preservation check verifies the original units in order. The original Mermaid source remains available in labelled disclosures beside the designed figures.

## Added teaching layer

Seven Phase 1 Mermaid diagrams now have FigureMap models with labelled arrows, owner boundaries, role legends, point-making captions, and source references. The seven chapter intros describe the lesson's practical focus. Each chapter ends with a concise recap labelled as added by this site. Performance adds a seven-step journey from a scrolling frame through telemetry, diagnosis, and a benchmark gate. Versioning adds a six-step policy-gate journey showing soft deprecation, forced update, and cached-policy fallback. These are manual step-throughs, with text captions and controls; nothing plays automatically.

During Codex review, one new Performance caption was corrected. JankStats calls its listener for every measured frame, including a smooth frame with `isJank=false`; it does not stay silent on smooth frames. The revised wording follows the [AndroidX listener reference](https://developer.android.com/reference/androidx/metrics/performance/JankStats.OnFrameListener). The jank threshold example follows the [documented default multiplier of two](https://developer.android.com/reference/androidx/metrics/performance/JankStats). The other added descriptions were checked against the chapter and its cited official sources. No original source chapter was edited for this website milestone.

## Verification

The non-pending `dev.py build` passes: 168 pages, 21,028 original units preserved in order, and no preservation problems. `dev.py figures` passes 99 models. `dev.py frames` passes 162 pages, 98 figures, 121 maps, and 2,015 labels with no overflow or clipping problems. `dev.py ci` passes its website tests, docs tests, docs checker, and browser-script syntax checks. `git diff --check` is clean.

A browser preview covered the Performance and Versioning walkthroughs, a normal-layout Accessibility page, the desktop curriculum and timeline, and the Performance step-through at 375 CSS pixels. The narrow diagram stayed in a labelled local scroll frame, with readable step controls and no page-wide sideways scroll observed. The learning path renders all seven Phase 1 links locally, keeps Offline Sync local, and leaves Phase 2 links on GitHub. The full manual mobile review remains deferred under rulebook §20 until the complete website is integrated.

## Browser audit

All six fresh browser audits passed on this build:

| Audit | Result |
| --- | --- |
| Browser preservation | 168/168 pages; code 5,936/5,936; Q&A pairs 1,194/1,194 |
| Binder | 560/560 |
| Motion | 13/13 |
| Refinement | 69/69 |
| UX | 278/278 |
| QA tampering | 31/31 |

The browser audit completed across the whole built site, including the unchanged topics. These results are evidence for this commit and its source snapshot; another change to shared output requires fresh audit evidence.

## Limits and next milestone

This release publishes Phase 1 and the prior Offline Sync pilot, not the rest of the 35-chapter tree. Practice mode, which would hide original answers until reveal, remains an owner decision; original answers are visible. Phase 2 needs its own 15 FigureMaps, seven chapter intros and recaps, seven step-throughs, review, audit, gate, and website PR. Before Phase 2, the source Telemetry SDK chapter needs a separate correction to its JankStats example: the documented default jank heuristic is twice the frame interval, so its example thresholds are 33.3 ms at 60 Hz and 16.7 ms at 120 Hz. That source fix is outside this Phase 1 publication.

> Historical review record. Current completion, public publication and candidate dispositions are in [completion/REPORT.md](completion/REPORT.md). Earlier pending/private-hosting statements below are superseded.

# Handover: AirBridge-style reader refinement

**Latest completion:** The owner additionally authorized verified technical fixes and an original-source PR. [The official verification report](OFFICIAL-CONTENT-VERIFICATION-2026-10-27.md) records 86 replacements across 31 chapters and source PR #57. This supersedes the earlier read-only/no-corrections instruction for that specific verified set. Both repositories retain their established visibility; no PR is merged.


**Superseded continuation instructions, 27 October 2026:** The owner subsequently approved making the website repository and GitHub Pages website public. The AirBridge shared presentation pass is now implemented; three decision figures are static, with 119 illustrated state figures and 17 temporal scenes retained. Use [the completed refinement report](AIRBRIDGE-REFINEMENT-2026-10-27.md) and [deployment guide](../DEPLOYMENT.md) for current checks, publication and live links. The original playbook repository remains private. The restart automation remains PAUSED. Older privacy, download-only and pending-implementation statements below are historical and must not override this update.


This is the continuation point after the owner reported low remaining usage and requested an automatic restart after the usage window renews. The implemented illustrated pass is complete; the subsequent article-experience refinement has been discussed and documented, but has not been implemented. Continue from the existing work rather than rebuilding the website or rewriting every chapter.

## Repository and publication

Work only in `/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook-website`, branch `codex/android-completion`. The original sibling playbook repository is read-only. The website origin is the private `swarnsingh/android-staff-engineer-playbook-website` repository. Existing draft PR: https://github.com/swarnsingh/android-staff-engineer-playbook-website/pull/1 . Keep main and original chapter corrections unchanged without the required owner approval.

The product implementation is at `44edf0d33433c89fb8bbc8709ca2cdc6631f36c3`. Later commits `e809b5f` and `7dc9957` record the owner's motion and article-reference preferences. The verified build for `7dc9957` succeeded: https://github.com/swarnsingh/android-staff-engineer-playbook-website/actions/runs/40398412156 . Its docs quality run also succeeded: https://github.com/swarnsingh/android-staff-engineer-playbook-website/actions/runs/40398412136 . Use the repository workflow for publication and provide GitHub URLs. Both source and preview must remain private. The current delivery is a downloadable GitHub artifact, not a live private website. Do not publish through Codex/Claude artifacts, another source repository, public Pages or a new external host as a workaround.

## Completed and verified

Android's 101 chapters and Kotlin's 22 chapters, plus two learning-path pages, use the shared design system. There are 17 authored scenes and 122 additional illustrated state figures across 107 lesson files, with 545 explicitly chosen objects. Counts describe the implementation, not a requirement for further animation. The seven KMP lesson reworks, Phase 7 staff-note improvements and candidate-review notes from the prior handover are already included.

The integrated audit passed 125 pages, 1,750 reading layouts, 9,104 illustrated-state checks, 1,808 scene-state checks and 13 motion regressions. Original preservation checked 15,572 units with zero problems and verified 125 source hashes. Documentation gates and 15 tests passed. Evidence is in `website/reviews/coverage-*.json`; read `illustrated-coverage-2026-10-27.md` and `website-experience-2026-10-27.md` for the failed sweeps and focused corrections. Do not relabel these as a fresh audit after changing the renderer.

## Latest owner decisions

Read `content-rulebook.md`, especially sections 8, 17–20. The primary overall article reference is https://swarnsingh.github.io/swaran-technical-blogs/blogs/airbridge-technical-architecture.html . It was inspected in Chrome: strong heading hierarchy, generous spacing, large readable diagrams, explanations connected to decisions, focused code, trade-offs and bounded status claims. ByteByteGo and Cloudmash remain supporting references for diagrams and interaction. This is a reference for the whole reading experience, not a request to copy transfer-system content into other topics.

Animation is optional. A beautiful static diagram is a complete result when it explains the topic clearly. Use motion only where timing, movement or changing state adds understanding. Review existing sequences and simplify unnecessary playback while preserving useful captions, alternatives and caveats. Update the illustrated-figure manifest and checks with any representation change. Do not turn all 122 figures into bespoke simulations merely to increase a count.

A blanket content rewrite is unnecessary. Refine shared presentation and selectively improve openings, transitions or explanations with demonstrated weaknesses. Original chapters remain preserved; flagged corrections need exact owner approvals. Keep Content explanations and Q&A separate, retain reading preferences and accessibility, and respect the agreed 880px sheet / 760px text measure.

## Next implementation pass

Inspect representative Android and Kotlin lessons with different needs: a mechanism, a comparison/decision, a hierarchy and a code-heavy explanation. Identify concrete gaps against the AirBridge reading experience. Implement shared layout, typography, spacing and figure improvements, then apply the appropriate visual representation across the affected lessons. Reuse existing original SVG objects and accurate illustrations. Avoid decorative movement, fake transfers, arbitrary metrics or one repeated article template for every topic. Correct technical claims against primary sources when editing them.

Work through implementation, audit, fixes and private GitHub publication autonomously. Keep progress updates concise. The owner does not want to wake up merely to send a continue prompt. Routine reversible website work is authorized; preserve the explicit boundaries around source corrections, privacy and publishing elsewhere. Do not merge the draft PR or change repository visibility as an inferred shortcut. Report a concrete blocker if an unavailable credential or owner-specific decision prevents the remaining step.

## Build and verification notes

Run from the website repository. Build with `/Users/swaransinghaulakh/AndroidStudioProjects/android-staff-engineer-playbook/venv/bin/python website/scripts/build.py`. Run that interpreter with `scripts/check_docs.py` and `-m unittest discover --start-directory scripts --pattern 'test_*.py'`. The system Python lacks the build's Markdown dependency. The build verifies actor coverage and samples scene routes for actor intersections. The CSS compiler must continue omitting aliases whose source and destination names match; self-referential aliases previously invalidated colours.

Prepare disposable browser QA with `python3 website/tools/prepare_browser_audit.py website/.cache/browser-qa`, then serve it on an available localhost port for testing only. The prior server was stopped. Use CUA for browser inspection, not an external browser driver. The full harness uses fetched HTML in iframe `srcdoc`; changing it back to repeated iframe navigation previously stalled the run. Read compact DOM result summaries and download the JSON; full accessibility snapshots of the enormous result text can time out. All product/gallery/fixture assets need versioned URLs to avoid stale runtimes. The docs checker also scans ignored cache Markdown: downloaded preview instructions were renamed to `.txt` locally to avoid a spurious thin-content error.

After changing shared presentation, audit both trees at phone, tablet and desktop widths with enlarged text, all themes and reduced motion. Verify the gallery, source preservation and appropriate motion controls. Push to the same branch, update PR #1, wait for the build to succeed, inspect the private artifact's commit metadata, and return the GitHub build and report links. Distinguish a downloadable build from live hosting in the final report.

## New owner-supplied review inputs

After this handover was written, the owner pasted two review reports and asked to continue. Read both complete files under `website/reviews/incoming/`: `2026-10-27-topic-audit.txt` and `2026-10-27-website-review.txt`, plus `2026-10-27-review-status.txt`. They cover Android/Kotlin technical claims, the SharedFlow scene, mobile targets, syntax highlighting and longer-term suggestions. They are unverified review inputs, not proof of an all-topic audit or blanket approval of original-chapter replacements. Map them to the existing findings/triage and verify each substantive claim; avoid blindly repeating categorical claims or adding a third Channel mode just to match an old heading. The confirmed SharedFlow heading was changed to name its two actual modes. Other substantive recommendations remain to assess.

The owner subsequently cancelled the `resume-playbook-refinement` heartbeat. It is PAUSED and must not be re-enabled without a new request. The owner asked to continue the review directly, fix and self-review the remaining work, then deliver a real hosted website URL rather than a downloadable package. Resume this same branch and PR #1. Check for newer instructions before acting.

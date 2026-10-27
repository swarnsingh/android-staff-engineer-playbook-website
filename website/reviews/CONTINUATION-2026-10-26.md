# Website continuation report — 2026-10-26

Start here when continuing the work from handover `09836cf`. The only website source repository is `swarnsingh/android-staff-engineer-playbook-website`, on branch `codex/android-completion`. Read [rulebook section 19](../../content-rulebook.md#19-separate-website-repository-and-publication), [the build guide](../README.md), [deployment](../DEPLOYMENT.md), and [round-4 findings](design-system-review-round4.md).

## Completed source work

- Full authored scenes for **17 lessons**: Binder; Looper; Room; WorkManager; OkHttp; Flow sharing; StateFlow/SharedFlow; coroutine suspension/resumption; Paging; Zygote; Intent resolution; broadcasts; process lifecycle; Gradle phases; KSP rounds; Compose recomposition; Media3. This covers the handover's movement candidates in four batches of four after the Binder pilot.
- **122 other state steppers** retain their controlled state sequences and text fallback. Generic active-box packets are disabled. A transfer requires authored endpoints, and `data-no-handoff` explicitly suppresses motion. Decision/comparison topics do not invent transport edges.
- Shared playback ownership across looping diagrams, scenes and legacy steppers. Next exposes Pause during a flight. Reader pause, reduced motion, document visibility and offscreen handling stop motion; manual steps remain usable under reduced motion.
- Binder track switching resets the step index. This fixes an actual exception when switching from the last synchronous step to the shorter oneway track.
- Reader mobile padding preserves the stated diagram label floors; handwritten prose wraps long identifiers. Packet labels stay inside their drawing's edges. The build emits scene captions before JavaScript, including an alternate-track no-script fallback.
- Seven formerly templated KMP lessons have concrete case explanations, contract tables and differentiated layouts: decision matrix, foundations overview, module boundaries, library ecosystem, dependency injection, Compose Multiplatform and resources.
- All fifteen Phase 7 staff notes now explain a topic-specific ownership, measurement or release decision.
- KS4, KS5, KO2 and KC8 have neutral on-page notes and primary-source follow-up records. No original replacement is applied. KS4's exact symptom and KO2's particular KMP/Xcode archive remain reproduction questions.

## Verification

The build passes: **125 pages, 15,572 original units, zero preservation problems**, all source hashes verified. Documentation links/anchors/content checks and **15 checker unit tests** pass. Browser scripts pass syntax checks. The source chapters and correction-approval data remain unchanged.

The real-runtime motion suite passes **11 checks**, recorded in [round4-motion-validation.json](round4-motion-validation.json). Binder's reading matrix covers four themes, four fonts, two body sizes, seven widths and Content/Q&A; the current result is [round4-binder-validation.json](round4-binder-validation.json). The strengthened matrix also asserts actual track/step transitions and collects runtime errors; an earlier geometry-only result is not sufficient for the track-switch fix.

The full sweep checks all 125 built documents at 320, 390, 768, 1181, 1280, 1439 and 1440px with actual 22px Shantell Sans. For every scene it also walks every track and state at four widths in all four themes, checking text floors, SVG/node bounds, step counters and runtime errors. The final outcome is recorded below when exported. Incomplete or stalled browser runs are not reported as successful audits.

These are desktop Chromium document/interaction checks, not physical-device, Safari/WebKit, screen-reader or Android runtime certification. No Apple app or Android Gradle reproduction was invented for the content review.

## Publication and privacy

The owner explicitly confirmed that **both source and preview remain private**. All LLMs must use this repository and its deployment workflow. Do not update the old Claude artifacts, create a new agent-specific Site, or push source into a second hosting repository.

[The GitHub Actions workflow](../../.github/workflows/website.yml) builds from the source commit and uploads a private artifact named `website-private-preview-<commit>`, with relative links, local-review instructions and `build-info.json` provenance. It contains no public Pages deployment job or public-publishing switch. Artifacts are retained for 14 days and can be recreated by rerunning the workflow.

A private Actions artifact is a downloadable review build, **not a live hosted website**. Live private hosting is not configured. A future runtime must deploy from this repository and enforce the owner's access requirement. GitHub Pages on a personal repository does not provide the required owner-private website access.

## Remaining approvals and external verification

The owner still needs to review Binder on phone/tablet/desktop and approve exact original-chapter corrections phase by phase. Those approval requirements are not waived by fixing the website. The KS4 and KO2 reproduction limits above remain explicit. Live private hosting requires an owner-approved runtime connected to this repository; publishing elsewhere is not an acceptable fallback.

## Final audit and publication result

Final browser and GitHub Actions outcomes are appended here after verification. This report is deliberately explicit about source completion, measured checks and hosting limits so the next LLM does not treat a local build, old preview or pending CI job as a completed live deployment.

- Final sweep: **125/125 passed**, **1,750 layout checks**, **1,808 scene-state checks**, **122/122 legacy steppers**, **17/17 scenes**, **93/93 original diagrams**, zero runtime errors. Raw evidence: [round4-browser-validation.json](round4-browser-validation.json), covering the source at `7120f9a`.
- ResizeObserver feedback warnings found by the expanded sweep were fixed by coalescing observer-driven DOM updates onto the next animation frame. No such errors remain in the passing sweep.
- Final targeted reruns: Binder **448/448 passed**, including actual mode/step assertions and runtime-error collection; motion regressions **11/11 passed** after the final resize fixes.

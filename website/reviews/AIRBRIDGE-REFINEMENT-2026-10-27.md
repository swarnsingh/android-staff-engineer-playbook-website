# AirBridge reader refinement and public publication

The owner approved a public repository and public GitHub Pages website on 27 October 2026 after the actual Pages settings reported that this personal private repository required an upgrade or public visibility. This supersedes the earlier private-source/private-preview hosting decision. All website source, design, reviews and deployment configuration remain in this repository. The original playbook repository remains private and unchanged. The scheduled restart was cancelled and remains disabled.

## Implemented presentation

The reader now uses the AirBridge reference's clear headline hierarchy, cooler light surfaces, restrained role callouts and more deliberate section spacing while keeping the 880px sheet and 760px text measure. Inter introduces articles; the book-serif reader setting remains available. A new landing page leads directly to both learning paths instead of silently choosing Kotlin. It derives chapter counts from the build's actual tree order. The original two learning-path pages and all 123 chapter pages remain available.

A reading-position bar complements the existing section scrollspy. It describes the current view's scroll position, not learning completion. It updates with scrolling, panel size and viewport changes. Code highlighting now recognizes common Kotlin annotations, modifiers and types, escaped strings, characters and comments while preserving the code's text exactly. Mobile scene and state controls have 48px touch targets; desktop numbered steps have 44px targets.

The form-factor decision, KMP pricing-rule pilot and Ktor/Retrofit migration examples are static numbered decision diagrams. Their authored explanatory captions remain visible together. The KMP figure's duplicate title was removed. The other 119 illustrated state figures and 17 temporal scenes retain their useful traces and controls. The coverage manifest follows the chosen representations, rather than treating animation counts as a requirement.

Source and curriculum links now point to the preserved snapshot in this public website repository, because the original canonical repository remains private. Source Markdown is still read-only; this changes rendered destinations, not original files. The public deployment uses the project path consistently for lessons, assets, navigation and the gallery. Build provenance is published in `build-info.json`.

## Incoming review disposition

The two pasted reports are retained as unverified review inputs. Many cited original issues are already recorded in the phase findings or Kotlin corrections triage. They are not blanket approvals of proposed replacements, and the reports' claims of comprehensive auditing are not independent evidence.

The SharedFlow heading mismatch was confirmed and fixed before this pass: its two modes are StateFlow and SharedFlow. The original `tryEmit` passage already states that its no-subscriber-only success rule is for a default unbuffered flow, so the submitted complaint does not justify duplicating or rewriting that qualification. The [API reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow/try-emit.html) explains that no-subscriber emissions return true and retain only configured replay.

The effects collector in the original lifecycle-safe section warrants a neutral review notice (SS1). Composition lifetime alone does not establish a STARTED-only collection policy. Evidence: [effect lifetime](https://developer.android.com/develop/ui/compose/side-effects) and [lifecycle-aware collection](https://developer.android.com/kotlin/flow/stateflow-and-sharedflow). The original example is preserved pending exact approval. A conditional `LaunchedEffect(Unit)` is not automatically incorrect; its entry/exit and delivery contract must establish a concrete problem before changing keys.

The pasted offset recommendation also needed precision: the lambda overload defers the state read to layout placement, rather than directly to drawing. The existing ML1 finding already identifies the chapter's contradictory advice. Evidence: [Compose phases](https://developer.android.com/develop/ui/compose/phases). No unapproved source replacement was applied. Optional Kotlin Playground integration was not added as an unrelated third-party execution feature; Android application fragments are still identified by their actual execution requirements.

## Validation and publication

The static build preserves 125 source pages and 15,572 original units and verifies 125 source hashes. The full reader, motion and Binder matrices are rerun for this shared change. Raw results and any focused corrections are recorded with the completed checks below. The landing page and gallery require additional visual and route checks because they are not original chapters.

Publication uses the existing branch and PR #1, followed by GitHub Pages from the same repository. A successful Actions build is followed by an actual deployment and live checks of the landing page, both learning paths, representative lessons, gallery assets and provenance. A ZIP is no longer presented as the final website delivery. Remaining original-chapter findings continue to be visibly marked; a source-preservation audit is not a claim that those pending technical corrections have been approved.

### Completed local checks

- Full rerun: 125/125 pages passed; 1,750 layouts across seven widths and both reading views, 1,808 full-scene states and 8,880 illustrated state checks across four widths and four themes. Evidence: `refinement-browser-validation.json`.
- The first sweep found two 320px page overflows in KMP foundations and dependency injection. Their numbered structure tables inherited the original comparison table's minimum cell width. Scoped fixed-layout tables now wrap within the diagram paper. The raw failing sweep remains in `refinement-browser-sweep.json`; the complete rerun passed after this shared fix.
- Binder: 448 checks passed. Motion: 13 behavioral checks passed, including pause, reduced motion, explicit transfers and shared motion ownership. Evidence: `refinement-binder.json`, `refinement-motion.json`.
- New page and interaction fixture: 69 checks passed, including landing/gallery at seven widths and four themes, route responses, three static decisions, code-text preservation, reading position in Content and Q&A, and phone controls. Evidence: `refinement-interactions.json`.
- Project-path publication build: 2,503 generated local references resolved within the output. All 56 checked text/role colour pairs met 4.5:1. Evidence: `refinement-project-path.json`, `refinement-colour-checks.json`.
- Documentation gates and all 15 checker unit tests passed; JavaScript syntax and diff whitespace checks passed. Static preservation checked all 15,572 source units and 125 source-page hashes. Phone landing and Binder, tablet navy styling, and desktop article/decision layouts received visual inspection in Chrome. These checks are browser viewport simulations, not a physical-device certification.

The website repository is public and Pages uses the workflow build type. Its deployment environment permits `main` and `codex/android-completion`. The original repository remains private. Deployment and live provenance results are recorded after the publishing workflow completes.

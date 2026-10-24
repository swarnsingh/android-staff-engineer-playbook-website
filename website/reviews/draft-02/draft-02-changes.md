# Draft 02: changes for the second review

This is a local design/content prototype. No migration, publishing, or replacement of the canonical coroutine chapter has occurred. A new `content-rulebook.md` was added to the repository and linked from README/CONTRIBUTING at the owner's request; it records the future authoring requirements.

## What changed from the first sample

| Claude's concern / owner's requirement | Change in this draft | Remaining qualification |
| --- | --- | --- |
| Opening jumps to staff vocabulary | A nine-section profile-screen story now develops need, concurrency, execution context, compiler mechanics, ownership, cancellation, failure policy, and production decisions. | Still a worked sample, not complete coroutine coverage. |
| Necessity is skipped | Each mechanism is introduced by a problem left by the preceding step, with an explicit bridge to the next question. | System design and other topic types have different routes in the rulebook. |
| Internals should not disappear | Continuation passing, resume state, labels, suspension marker and immediate completion are explained with a labelled Java-shaped model and primary-source links. | The generated-code sketch is pseudocode, not a claimed decompiler capture. Other internals remain in the coverage inventory. |
| Code experiment cannot show its effect | A short conceptual fragment leads to an expandable complete runnable program. A `concurrent` flag produces timestamped start/done/result traces and thread names. | Wall-clock timings are environment-dependent, not performance benchmarks. |
| runBlocking is unexplained | The console bridge is explained explicitly; Android-shaped fragments have separate labels and dependencies. | Only the complete JVM program was compiled/run during this revision. |
| Animation timing and meaning are weak | Four scenario models with Previous/Next, Play/Pause, Replay, slider, code highlights, UI-thread lane, and a static step table. | Curated teaching frames, not live Kotlin tracing. Playback pacing is for reading. |
| Cancellation incorrectly looks instantaneous | Cancellation request, observation/cleanup, and completion appear as separate steps. The lifecycle event actually clears the chosen owner. | A different owner/back stack may require a different policy. |
| Optional data needs a real policy | `supervisorScope`, expected I/O fallback, a cooperative timeout, and cancellation preservation are explained. | Supervision alone does not handle an escaped await failure. |
| Q&A hides necessary reasoning | Inline checkpoints contain answers; Q&A derives a practice view from the same DOM content. Sources and experiment entry points stay in the lesson. | Owner-requested supplemental tabs are retained. |
| Outline vanishes on tablets/focus mode | Desktop outline is retained; compact sticky outline appears at smaller widths. Curriculum becomes a modal drawer below 1180px. | Physical-device and engine testing still required. |
| Small text and poor hero contrast | Relative reader sizes scale code, captions, model labels, and table text; updated colours and a compact hero. | This is not a complete accessibility certification. |
| Drawer allows background navigation | Native modal drawer with explicit focus wrapping, scroll lock, Escape/Done, and focus return. | Screen-reader and touch-device checks remain. |
| Settings are inconsistent and hard to preview | Aa/Reading opens the same modal at every width, with live sample text; theme radios, code wrapping, OS-motion indication. | Font appearance depends on installed fonts; requested choices are preserved. |
| Lost reading position | Sticky view controls, URL view/anchors, and saved reading position for returning to Content. | Browser Back/Forward and long-session restoration warrant broader checks. |
| Search and external navigation mislead | Search scope/result announcements and explicit GitHub cues; sample keywords find the coroutine lesson. | It remains catalog search, not production full-text indexing. |

## Evidence collected

- Node syntax checks on app/model JavaScript passed.
- Pure-model assertions checked distinct success ordering, cancellation completion, required-child failure, optional fallback, valid code-highlight indices, and position bounds.
- HTML check found unique IDs and resolving local anchors/script assets.
- Representative page-width checks at 320, 390, 540, 768, 1024, and 1440px found no horizontal page overflow, with an available outline.
- At 22px base reading size: prose 22px, core code 18.04px, model caption 20.9px, table 19.8px; no page overflow in the checked 390px layout.
- Modal focus wrapping/return, scroll lock, reduced-motion manual stepping, stable focused Next control, tab keyboard selection, announced search results, and focus-mode outline/settings were exercised.
- A checked Content → Q&A → Content round trip returned to the same saved vertical position in the test browser.
- The complete Kotlin program was executed in the external playground in both modes. Concurrent output started both requests before completion and produced the profile at 848ms in that run. Sequential output started avatar after name completed and produced the profile at 1322ms in that run. These are single illustrative runs, not comparative benchmark evidence.
- Body/hero/muted-text contrast ratios were calculated from CSS tokens in all four themes. This does not verify every rendered control, code token, disabled state, or external editor colour.

## Not verified

Other browser engines, actual phones/tablets/foldables, hinge postures, touch scrolling, screen readers, browser zoom/OS text scaling, print layout, and performance have not been comprehensively tested. Java-shaped compiler pseudocode and Android fragments were not compiled as standalone programs. The entire original chapter and the full local book collection were not audited.

## Sources and provenance

The lesson cites Kotlin/Android official documentation, the Kotlin language specification and compiler source beside relevant claims. Dove Letter's compiler article is linked as a companion explanation. Relevant initial pages of the owner's local `Kotlin.pdf` were inspected; books remain local and are not included in the package.

The reference video's transcript was fetched as text and read to extract its problem/need/solution sequencing. Its script, artwork, and full transcript are not included in this package. The video is a presentation reference, not a platform-accuracy authority.

## Repository document check note

The unmodified `venv/bin/python scripts/check_docs.py` command passes link, heading, marker, answer-key, index, and currency checks, but flags two existing pip/idna `LICENSE.md` files inside the local `venv` as thin content. Running the same project-document checks with that local environment excluded passes. No quality-gate code or dependency-license files were changed to hide that unrelated scan result. `git diff --check` passes.

# Phase 1 review: fixes to apply

From the independent review subagent, 2026-10-25. All items are verified claims from the reviewer.

## P2

1. **build.py `phases()` puts Kotlin 2.4 in Phase 3.** `kotlin.md:61` links `kotlin-2-4-update.md#context-parameters-are-stable` inside Phase 3.
   - Fix: ignore links with a `#fragment` when deciding phase membership, and only let the first phase that lists a chapter claim it, for both order and group label.
   - Add a build check that phases are contiguous.
2. **Under review notes state the replacement as fact.** Kotlin precedent (K1) says "under review" only.
   - Notes affected: `activity:30`, `savedstatehandle:29`, `process-death:35`, `mvvm-vs-mvi:32`, `state-management:50,58,61`, `modularization:40,43`.
   - Teaching that states the corrected fact: `viewmodel.blend` step "Rotation starts" (app process); `savedstatehandle` 1MB/50KB figure; `state-management` diagram redraw (`collectAsState` edge replaced).
   - Decision (Claude's, consistent with K1): reduce notes to "under review; see the findings file" without the replacement. Keep neutral facts from the original's own answer key where it agrees. Move contested figures to `reviews/pending-android-teaching.blend`.
3. **`state-management.blend:7` opening contradicts itself.** `remember` doesn't survive process death. Use `rememberSaveable` in the field.
4. **`modularization.blend:32` repeats a wrong count.** "Three modules on critical path" should be four. Add original finding MO3 (line 154: 3 nodes should be 4; "three nodes more" should be 2).
5. **`viewmodel.blend:56` gets the order wrong.** Correct order: `viewModelScope` is cancelled first, then `onCleared()` (androidx `ViewModel.clear()` doc comment).
6. **`activity.blend` is missing a note.** Add `@before Answer Key :: review` for A1.

## P3

- `activity:51` and `viewmodel:26`: Back finishes the activity. Not for the root launcher activity on Android 12+. Qualify.
- `activity:64`: "before `onStop()` returns" should be "by the time its state is saved".
- `viewmodel:28`: store "new, empty" should be "new store".
- `mvvm-vs-mvi` stepper: the loading/spinner text is inconsistent. Also the torn-frame claim: the two writes have no suspension between them, so put a suspend call between them or say "observable by other collectors".
- `mvvm-vs-mvi:29` figcaption: don't attribute the Channel branch to Android guidance.
- `navigation:7` deep-link bug is never resolved (point to Answer Key 7). `navigation:20`: no root-graph entry. Figcaption at `:26` calls the activity "an entry".
- `reader.html` footer is Kotlin-specific: "Kotlin learning path" link, "with documented technical corrections". `build.py:155` part band text "What the compiler and runtime actually do".
- Findings file updates:
  - VM1: add a source link.
  - SM2: cite the Dagger HiltViewModel javadoc, "Exactly one constructor … annotated with Inject or AssistedInject".
  - A1: note that the activity lifecycle page conflicts with the multi-window page.
  - MV1: "outdated".
  - MV2: reframe as a misdiagnosis.
- New original findings to add:
  - `viewmodel.md:61,127`: the scope is closed in `clear()` before `onCleared()`.
  - `state-management.md:509`: the cutoff is after state saving, not after `onStop`.
  - `viewmodel.md:59`: Back on a root activity on Android 12+.
  - `mvvm-vs-mvi.md:208`: collection restarts at STARTED, not on resume.
  - `mvvm-vs-mvi.md:291`: `BUFFERED` is bounded at 64.
  - Activity dialog: promote to a flagged finding (an in-window `Dialog` doesn't pause).
- Concern: `savedstatehandle` keystrokes through `getStateFlow`. TextField guidance advises against async state, so add a caveat.

## Apply the same "notes don't state replacements" rule to Phases 2 and 3 (and onward)

Phase 2 notes (R1, R2, R3, RD1, DI1, C1, HK*) and Phase 3 notes (ST1, ST2, ML1, SE1) also cite the replacement. Same treatment.

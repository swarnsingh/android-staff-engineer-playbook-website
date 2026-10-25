# Phase 3 review: findings and disposition

From the review subagent, 2026-10-25. Findings ST1, ST2, ML1 and SE1 are all correct. ST1's note is in the wrong place and covers too little.

## P1

1. **modifiers-and-layout, new finding ML2.**
   - Original lines 34 and 40–44 (First Principles "Each modifier wraps the previous one"; the gift model with padding first, red outside) contradict line 21, the chapter's own diagram, and the docs. The blend teaches the correct rule.
   - Add Under review notes before First Principles and Mental Model.
   - Evidence: developer.android.com/develop/ui/compose/modifiers ("padding applied *after* clickable → whole area clickable").
2. **compose-navigation.blend:7, new finding NV1.**
   - The opening says "controller … Android-only". Wrong: JetBrains `org.jetbrains.androidx.navigation:navigation-compose` 2.10.0-rc01 works in commonMain (kotlinlang.org/docs/multiplatform/compose-navigation-routing.html).
   - Reword the opening so it doesn't depend on platform support.
   - Promote the smaller note to finding NV1 (originals at lines 210, 422 and 461), with notes before "Why This Rewrite", "Nav 2 vs Nav 3 — Side by Side" and "When To Pick Each".

## P2

- **ST1.**
  - Fix its location: the quoted sentence is at line 48, in "The Skipping Decision — Compose Compiler Output".
  - Extend its scope to lines 42–43, 103–104, 325–330 and 398–399.
  - Add notes before "The Skipping Decision…", "What's Inferred Unstable", "Reading the Compose Compiler Metrics" and "Failure Modes".
- **stability.blend.**
  - Checkpoint 3 states the ST2 correction as fact. Move it to `reviews/pending-android-teaching.blend`.
  - ImmutableList is stable only if the element type is stable. Add "if Item is stable" and the equality-cost caveat (fix-stability doc).
  - New original finding ST3 (line 215, "fully stable").
- **recomposition-and-state.blend steps 3–4.**
  - A tap invalidates the scope that read `count3` (Button content), not Counter.
  - The plain var stays 0 because nothing invalidates it.
  - Reword both steps.
- **compose-accessibility.blend opening and stepper.**
  - `clickable` on a parent auto-merges its children, and an Icon with a null description adds no semantics.
  - Change the before-state to a row with `pointerInput`/`detectTapGestures` or no click semantics, and give the image a cause that can produce "Unlabeled image".
- **form-factors-matrix, new finding FF1.**
  - The original's lines 12 and 39 say widgets can't scroll. Glance `LazyColumn` scrolls (it becomes a ListView).
  - Reword blend check 2 around live updates, not scrolling.
- **adaptive check 3.** `screenWidthDp` follows the app window in multi-window. Reword to "not the full window metrics or the component's own constraints".
- **Findings file:** make NV1 a numbered finding.

## New original findings (P3)

- `snapshot-system.md:424`: the quoted exception text doesn't exist. The real text is "Reading a state that was created after the snapshot was taken or in a snapshot that has not yet been applied".
- `snapshot-system.md:399,401`: `readable(record, this)` and `writable(record, this)` won't compile. The public API is the extensions `record.readable(state)` and `record.writable(state){}`.
- `stability.md:129–131`: blames compilation order. Inference depends on whether the module was built with the Compose compiler.
- `adaptive…md:164–168`: `shouldUseTwoPane` returns false whenever there is a separating fold, which contradicts the next sentence.
- `recomposition-and-state.md:150`: the "can't share with KMP iOS" claim was not verified.

## Optional (P3)

- `recomposition-and-state` redraw: the label changed from `collectAsState()` to `collectAsStateWithLifecycle()`. Keep the original label, or make it neutral.
- `compose-runtime.blend:24`: the final caption blames a "new object", but the stepper's Header takes a String. Make the stepper's Header take a model object, or reword.
- `adaptive.blend:13`: the docs now list five width classes. Line 21: name the mechanism behind "saved by stable ID" (hoisted state or a `SaveableStateHolder` keyed by ID).
- `custom-layout.blend:8`: "each bug breaks one clause", but the large-font bug fits no clause. Line 41: the check assumes `place` without the question saying so.
- `perf-tooling.blend:29`: the question uses the pre-strong-skipping model. Line 13: note that draw follows a layout change.
- `view-interop.blend:6`: the opening's causal claim is too strong.
- Concision: `compose-accessibility` is at 25.4%; trim it slightly.
- Checker: add self-tests for a demoted inner H1 (compose-navigation) and a missing or duplicated hero H1.

## Coordinator implementation status

The listed teaching fixes, neutral note coverage and new original findings have been implemented on `codex/android-completion`; the independent follow-up review returned the two findings recorded below. A further verification attempt was interrupted by the review-agent usage limit. The ST2 checkpoint is held in `pending-android-phase3-teaching.blend`. Original chapters and correction approvals remain unchanged. Source-unit preservation passed on all 65 rendered pages with 22 adversarial cases, including original inner H1 demotion and missing/duplicated/hidden hero titles.

The integrated 65-page browser sweep now passes; `android-completion-validation.json` records it. Further independent verification remains subject to the usage limit.

Follow-up review: the Kotlin Topics catalog now derives order from canonical phase lists and checks emitted group contiguity. The Stability Failure Modes note covers both ST1 and ST2. FF1’s replacement clause and the ST3-dependent immutable-collection comparison are withheld; the live-update checkpoint and identity-reuse comparison remain.

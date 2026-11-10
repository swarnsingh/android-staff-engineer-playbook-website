# Kotlin source resync

## Scope and source

The Kotlin tree matches the merged playbook byte for byte at source main `5d1ddda656a078a910e58abdcc5854929e1c6c91` ([source PR #85](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/85), the Kotlin primary-source and compiler-output re-review). Twenty chapters changed. `kotlin.md` and the two remaining chapters were already identical. The files were copied from exact `git show` bytes, and `source-snapshot.json` records the new hashes and the Kotlin provenance.

The other 15 trees already match `5d1ddda` and are unchanged. Source `milestones.md` also changed in #85. The website's copy is a recorded link target, not a tree, so it is left as it was.

## What the readers see

The reader shows the source's re-reviewed text:

- real `javap` listings replace hand-written bytecode;
- examples that did not compile are fixed: Comparator variance, delegation visibility, `LocationCallback()`, unique `LazyColumn` keys and assisted Hilt ViewModels in Compose;
- corrected claims cover `SupervisorJob` exception routing, `viewModelScope` cancellation before `onCleared()`, `runTest` scheduler sharing, the `flatMapMerge` default concurrency, top-level `internal` names, default-parameter binary compatibility, the context-parameter status and the Kotlin 2.4 migration checklist.

## Teaching layer

No Mermaid block changed, and every blend anchor and FigureMap still resolves.

The Kotlin blends were checked against the corrected claims. They already agree with the source on all of these points:

- `jvm-interop` says top-level `internal` functions keep their plain names;
- `coroutines` says an uncaught failure under a `SupervisorJob` reaches the uncaught-exception handler;
- `inline-functions` separates capturing from noncapturing lambdas;
- `variance` limits the safe alias to read-only `List`.

No teaching text needed a change.

The overlay retired in the previous resync stays retired. Every retired Kotlin record is still either present in the source or replaced there.

## Validation

- Build: 35,914 original units preserved in order across 295 pages; all 22 preservation tampering fixtures detected.
- Figures: 268 original and 197 teaching models, 0 problems.
- Frames: desktop and 375 px passed across 279 pages, 339 figures and 5,144 labels.
- CI: 64 website tests, 31 docs tests, 74 Computer Science Java examples, the docs gate and 15 browser-script syntax checks passed.
- Browser audits: all six suites passed:
  - 295 pages;
  - 8,908 code readability cases;
  - 1,732 Q&A pairs;
  - Binder 560, Motion 13, Refinement 69, UX 278, Q&A tampering 31.

## Limits

Phone evidence is automated, and no screenshots were taken. The chapter text itself is the owner-reviewed source. This review checked only that the website's own additions do not contradict it.

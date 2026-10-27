# Phase 2 review: findings and disposition

From the review subagent, 2026-10-25. All nine findings rows were confirmed.

## P2 (blend fixes)

1. **`paging.blend` steps 1–2 and redraw.**
   - Wrong: the mediator APPEND is requested when the local PagingSource returns `nextKey == null` (cached rows run out), not when the user is "within prefetchDistance".
   - Missing: `initialize()` defaults to `LAUNCH_INITIAL_REFRESH`, so a remote REFRESH runs on open, and APPEND/PREPEND wait for it to succeed.
   - Fix: step 1 shows the REFRESH in flight; step 2 is triggered by "the cached rows run out".
   - Sources: `PageFetcherSnapshot.kt`; `RemoteMediator.kt:107`; https://developer.android.com/topic/libraries/architecture/paging/v3-network-db
2. **`room-vs-datastore.blend` DataStore column, step 1.**
   - Wrong: "already in memory after the first read" and "DataStore starts from the complete document it holds in memory". Current DataStore re-reads from disk under the write lock (`DataStoreImpl.transformAndWrite`).
   - Fix: "reads the current document (from disk, under the write lock)", or drop the claim.
3. **`hilt-vs-koin-vs-manual-di.blend` step "Ship".**
   - Wrong: "NoBeanDefFoundException". Current Koin throws `NoDefinitionFoundException`.
   - Fix: say "a missing-definition exception".
   - New finding KO1 covers the originals: `dependency-injection.md:140`, `hilt-vs-koin…md:336,471`.
4. **`components.blend` redraw.**
   - Right: ViewComponent is a child of ActivityComponent (Dagger `ViewComponent.java`, `@DefineComponent(parent = ActivityComponent.class)`).
   - The original diagram (`components.md:53`) and line 20 draw Fragment → ViewComponent.
   - Fix: add finding C2 and Under review notes before "What's a Component?" and "The Hierarchy (Visualized)".

## P3

- `dependency-injection.blend` redraw puts Repository in ViewModelComponent, but the original's own example makes Repository `@Singleton` (original inconsistency). Redraw it as a singleton binding the ViewModel requests, or flag it (DI2).
- `components.blend` step 4: "[Dagger/MissingBinding]" should be "✗ compile error (incompatible scope)". The reviewer compiled the Dagger model: `IncompatiblyScopedBindings`.
- `room.blend:7` opening: the fallback is either on (all wiped) or off (all crash). Rewrite.
- `paging.blend` "Like a post": "without touching PagingData" should be "without mutating PagingData by hand".
- `storage…blend` opening: add "…and the system kills the app" (the grant lasts until restart or the app stops).
- Under review notes are needed before EACH later affected section:
  - `room` (Answer Key)
  - `components` (Failure Modes, Answer Key)
  - `dependency-injection` (Answer Key)
  - `hilt-vs-koin` (Failure Modes, Common Pitfalls)
- Concision is over 25%:
  - `repository-source-of-truth`: 35%
  - `storage-and-content-sharing`: 31%

  Trim the opening paragraph or a checkpoint in each.
- Findings file:
  - Add source URLs for R1, R3, DI1 and HK3.
  - RD1 also covers `room-vs-datastore.md:112`.
  - DI1/HK3 exception: `@Inject` fields in the `@HiltAndroidApp` Application are built in `onCreate`.
- New original findings:
  - `room-vs-datastore.md:424` and Ans 11: corruption is from a "partially written" file. DataStore writes to a tmp file, syncs, then renames.
  - `room-vs-datastore.md:263`: "emits on any updateData". Skipped when unchanged.
  - `datastore.md` Ans 8: IOException when "not found". A missing file returns the default.
  - `paging.md` Ans 9: `LoadResult.Error` should be `MediatorResult.Error`.
  - `scopes.md:348`, `components.md:340`: SessionManager is unscoped (should be @Singleton).
- Optional:
  - `datastore.blend` animation: `data` emits after A as well as after B.
  - `hilt-vs-koin` header comment: Koin compile checks exist (`KOIN_CONFIG_CHECK`).
  - `room-vs-datastore` opening: "three weeks later, to a one-line write" is unclear.
  - The `dependency-injection` intro wording.

## Follow-up status (2026-10-25)

All actionable items above are addressed in the teaching/review layer. Original corrections remain pending owner approval.

- P2 mediator triggers, locked DataStore read, Koin runtime name and incompatible-scope wording were already fixed in `3e8aba3`; confirmed and retained.
- C2 now has a numbered finding and notes at both affected sections. Its corrected redraw is held outside active content until approval.
- The Repository ownership discrepancy is logged as DI2; its redraw is likewise held, with notes at Architecture and Production Example.
- The Room opening, manual PagingData wording, app-stop URI story, later-section note coverage and findings sources/scoping qualifications are addressed.
- Added pending original findings RD2/RD3/DS1/PG1/SS1 and KO1, with evidence and passage-specific notes.
- Concision: repository-source-of-truth 17.5%, storage-and-content-sharing 19.8% added prose by a whitespace-word approximation excluding figures.
- Optional animation/Koin/intro items are addressed. The DataStore sequence exposes both updated states without promising every intermediate state to a slow collector.
- Original smaller notes explicitly marked as unverified remain review leads; they are not silently promoted to factual corrections.

Validation: all ten Phase 2 blend files parse, each marker resolves to an original H2 or diagram, all stepper JSON parses, and source hashes remain unchanged. Integrated build/browser checks are owned by the coordinating agent after shared edits settle.

Independent follow-up review found no new P1/P2 defect. Its two P3 wording fixes are applied: the URI animation explicitly names Photo Picker/PickVisualMedia and process termination rather than Activity.onStop, and the DI teardown step says “Activity finishes”. The follow-up review also independently rendered all 10 chapters with 1,292 original units and 0 problems.

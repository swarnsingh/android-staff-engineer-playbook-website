# Phase 2 review: fixes to apply

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

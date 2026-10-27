# Android Phase 3: possible errors in the original chapters

**Completion update, 27 October 2026:** The owner authorized the remaining corrections. The findings below are the historical incoming review; current per-finding dispositions, primary sources and validation are in [the completion report](completion/REPORT.md) and [backlog ledger](completion/backlog.json). Website corrections are rendered through the approved overlay and the same text is proposed in source PR #57. Earlier “pending/unapproved/unchanged” statements describe the original review date.


Found while writing the teaching layer for Android Phase 3 (Compose runtime and UI architecture: the thirteen chapters listed in Phase 3 of `android.md`). These are **findings for the owner's review**, not approved corrections. The original Markdown is unchanged and nothing has been added to `content/corrections-*.json`.

Each finding is shown on its page as an **Under review** note before the section that contains it, and the teaching layer avoids restating these claims.

**Verification method:** Compose framework code was not compiled. SE1 is a pure Kotlin language rule and was compiled with Kotlin 2.4.21. Everything else was checked against developer.android.com, as cited. Checked on 2026-10-25.

| ID | Chapter, section | Original says | Problem | Evidence |
|---|---|---|---|---|
| ST1 | Stability, The Skipping Decision — Compose Compiler Output; What’s Inferred Unstable; Reading the Compose Compiler Metrics; Failure Modes | "If any parameter is unstable — always re-run the child"; "A function is not skippable if any parameter is unstable" | Pre-strong-skipping rule. Since Kotlin 2.0.20 strong skipping is on by default, and unstable parameters are compared by identity, as the chapter's own Strong Skipping Mode section says | [Strong skipping mode](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping) |
| ST2 | Stability, Failure Modes | "`@Immutable` annotation has no effect — Class has a `var` somewhere" | The annotation does take effect: "Annotating a class is overriding what the compiler would otherwise infer about your class". A `var` makes the promise false, not the annotation inert | [Fix stability issues](https://developer.android.com/develop/ui/compose/performance/stability/fix) |
| ML1 | Modifiers and Layout, Failure Modes ("Recomposing Modifiers") | Labels `Modifier.offset { IntOffset(x, y) }` as bad, then recommends lambda modifiers as the fix | Self-contradictory; the lambda form is the recommended way to defer fast-changing reads to layout | [Compose phases: defer reads](https://developer.android.com/develop/ui/compose/phases) |
| SE1 | Side Effects, Production Example | `if (errorMessage != null) showSnackbar(message = errorMessage)` where `errorMessage` is `by collectAsStateWithLifecycle()` | Kotlin does not smart-cast delegated properties, so this does not compile | Compiled with Kotlin 2.4.21: "smart cast to 'String' is impossible, because 'errorMessage' is a delegated property" |

| ML2 | Modifiers and Layout, First Principles and Mental Model | Each modifier wraps the previous one; gift analogy puts padding/background in the reverse order | These claims conflict with the chapter's own diagram and the documented ordered wrapper model | [Modifier order](https://developer.android.com/develop/ui/compose/modifiers) |
| NV1 | Compose Navigation, Why This Rewrite; comparison table; When To Pick Each | Navigation 2 is Android-only and cannot compile to iOS | JetBrains publishes a Navigation Compose 2 multiplatform artifact for commonMain; platform support alone is not the ownership/migration distinction | [Compose Multiplatform navigation](https://kotlinlang.org/docs/multiplatform/compose-navigation.html) |
| ST3 | Stability, Collections: ImmutableList and PersistentList | Immutable collection types are unconditionally “fully stable” | Generic element stability still matters; a collection does not make mutable elements stable. Equality cost also matters when choosing representation | [Fix stability](https://developer.android.com/develop/ui/compose/performance/stability/fix) |
| ST4 | Stability, What’s Inferred Unstable | Cross-module stability depends on compilation order | Relevant evidence is whether the defining module was processed by the Compose compiler, not which module happened to compile first | [Fix stability: multiple modules](https://developer.android.com/develop/ui/compose/performance/stability/fix) |
| FF1 | Form Factors Matrix, The Matrix; What Each Surface Really Demands | Widgets cannot scroll | Glance LazyColumn provides a scrollable collection, traditionally translated to ListView; live-update scheduling is a separate constraint | [Glance scrollable layouts](https://developer.android.com/develop/ui/compose/glance/build-ui) |
| SN1 | Snapshot System, Real Android Patterns | readable(record, this) and writable(record, this) in CounterState | Public Kotlin APIs are extensions on StateRecord; the shown call syntax does not match that API | [Snapshot API reference](https://developer.android.com/reference/kotlin/androidx/compose/runtime/snapshots/package-summary) |
| SN2 | Snapshot System, Failure Modes | Quotes “Reading a state that is not in the current snapshot” and attributes it to leaked Snapshot references | The actual diagnostic concerns a state created after the snapshot or in an unapplied snapshot; the quoted text and blanket diagnosis are inaccurate | [Snapshot implementation](https://android.googlesource.com/platform/frameworks/support/+/androidx-main/compose/runtime/runtime/src/commonMain/kotlin/androidx/compose/runtime/snapshots/Snapshot.kt) |
| AD1 | Adaptive Compose, Foldables and Hinges | shouldUseTwoPane always rejects separating folds, then recommends panes on either side for suitable experiences | The unconditional Boolean example contradicts the following product-dependent guidance | Original lines 164–168; [folding features](https://developer.android.com/develop/ui/compose/layouts/adaptive/foldables/make-your-app-fold-aware) |
| RC1 | Recomposition and State, Tradeoffs | A Compose-runtime ViewModel cannot be shared with KMP iOS | The runtime and ViewModel have multiplatform support; platform-specific dependencies determine whether a particular ViewModel can be shared | [Shared ViewModel](https://kotlinlang.org/docs/multiplatform/compose-viewmodel.html) |

## Smaller notes (not flagged on the pages)

- **Adaptive Compose, Window Size Classes:** the example uses `WindowWidthSizeClass` constants. Recent `androidx.window` releases favour breakpoint checks. This is currency, not an error.
- **Compose Navigation:** the original contains its own top-level `# Part 1` and `# Part 2` headings. The preservation checker now treats only the page-title H1 as unique; these inner H1s are checked in place like any other heading.

## Review-fix status

The Phase 3 teaching fixes and review-note coverage are implemented locally on `codex/android-completion`. ST2’s dependent checkpoint is held in `pending-android-phase3-teaching.blend`. All findings remain proposals; none is approved or applied.

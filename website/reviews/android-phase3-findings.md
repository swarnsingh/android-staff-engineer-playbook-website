# Android Phase 3: possible errors in the original chapters

Found while writing the teaching layer for Android Phase 3 (Compose runtime and UI architecture: the thirteen chapters listed in Phase 3 of `android.md`). These are **findings for the owner's review**, not approved corrections. The original Markdown is unchanged and nothing has been added to `content/corrections-*.json`.

Each finding is shown on its page as an **Under review** note before the section that contains it, and the teaching layer avoids restating these claims.

**Verification method:** Compose framework code was not compiled. SE1 is a pure Kotlin language rule and was compiled with Kotlin 2.4.21. Everything else was checked against developer.android.com, as cited. Checked on 2026-10-25.

| ID | Chapter, section | Original says | Problem | Evidence |
|---|---|---|---|---|
| ST1 | Stability, Why Stability Matters | "If any parameter is unstable — always re-run the child"; "A function is not skippable if any parameter is unstable" | Pre-strong-skipping rule. Since Kotlin 2.0.20 strong skipping is on by default, and unstable parameters are compared by identity, as the chapter's own Strong Skipping Mode section says | [Strong skipping mode](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping) |
| ST2 | Stability, Failure Modes | "`@Immutable` annotation has no effect — Class has a `var` somewhere" | The annotation does take effect: "Annotating a class is overriding what the compiler would otherwise infer about your class". A `var` makes the promise false, not the annotation inert | [Fix stability issues](https://developer.android.com/develop/ui/compose/performance/stability/fix) |
| ML1 | Modifiers and Layout, Failure Modes ("Recomposing Modifiers") | Labels `Modifier.offset { IntOffset(x, y) }` as bad, then recommends lambda modifiers as the fix | Self-contradictory; the lambda form is the recommended way to defer fast-changing reads to layout | [Compose phases: defer reads](https://developer.android.com/develop/ui/compose/phases) |
| SE1 | Side Effects, Production Example | `if (errorMessage != null) showSnackbar(message = errorMessage)` where `errorMessage` is `by collectAsStateWithLifecycle()` | Kotlin does not smart-cast delegated properties, so this does not compile | Compiled with Kotlin 2.4.21: "smart cast to 'String' is impossible, because 'errorMessage' is a delegated property" |

## Smaller notes (not flagged on the pages)

- **Compose Navigation, "When To Pick Each" and comparison table:** says Navigation 2 is Android-only ("Nav 2 can't compile to iOS"). JetBrains publishes a multiplatform port of Navigation Compose 2 for Compose Multiplatform. Not verified for this review; it should be checked before any correction.
- **Adaptive Compose, Window Size Classes:** the example uses `WindowWidthSizeClass` constants. Recent `androidx.window` releases favour breakpoint checks. This is currency, not an error.
- **Compose Navigation:** the original contains its own top-level `# Part 1` and `# Part 2` headings. The preservation checker now treats only the page-title H1 as unique; these inner H1s are checked in place like any other heading.

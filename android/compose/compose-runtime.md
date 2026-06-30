# Compose Runtime — Composer, Slot Table, and the Engine

> Compose looks like declarative React but it's not virtual DOM. There is no diffing tree. Instead, the Compose Compiler rewrites every `@Composable` function to register itself with a hidden `Composer`, which writes into a **Slot Table** — a gap-buffered, positional-memoization data structure. Understanding the runtime is what separates "uses Compose" from "can debug a Compose perf bug." Staff-level mastery means reading skippability lambs, knowing why your function recomposes when its inputs didn't change, and predicting which sub-trees survive recomposition vs get rebuilt.

---

## Compose Has Three Layers

| Layer | What it is | Lives in |
|---|---|---|
| **Compose Compiler** | A Kotlin compiler plugin. Rewrites `@Composable` functions to take a hidden `Composer` parameter, inserts group calls, computes skippability. | `androidx.compose.compiler:compiler` |
| **Compose Runtime** | The platform-agnostic engine: `Composer`, `Recomposer`, `Slot Table`, `Snapshot system`, `CompositionLocal`. **No Android types here.** | `androidx.compose.runtime:runtime` |
| **Compose UI** | Android-specific: `Modifier`, `Layout`, `LayoutNode`, gesture system, accessibility. Implements the `Applier` interface for Android. | `androidx.compose.ui:ui` |

This separation is why Compose Multiplatform exists — JetBrains plugs a different Applier (Desktop, iOS, Web) into the same Runtime. The **Runtime is just a tree-building engine**; the UI layer happens to build a UI tree.

---

## Why a Runtime Exists (and Not Virtual DOM)

React solves "find what changed" via a virtual DOM diff every render. Compose solves it differently:

- The **compiler** marks every `@Composable` function with positional information.
- Each execution writes into the **Slot Table** keyed by position.
- On recomposition, the runtime walks the slot table at the same positions and reuses previous outputs unless inputs changed.

This is called **positional memoization**. It's how Compose achieves React-DOM-like ergonomics without paying for a virtual DOM tree.

---

## What the Compose Compiler Does to `@Composable`

You write:

```kotlin
@Composable
fun Greet(name: String) {
    Text("Hello, $name")
}
```

The compiler rewrites it (conceptually) to:

```kotlin
fun Greet(name: String, $composer: Composer, $changed: Int) {
    $composer.startRestartGroup(0x1234ABC)               // unique key per call site
    if ($changed and 0b1 == 0 || $composer.changed(name)) {
        Text("Hello, $name", $composer, 0)
    } else {
        $composer.skipToGroupEnd()                        // SKIP if inputs unchanged
    }
    $composer.endRestartGroup()?.updateScope { c, _ ->    // remember how to re-invoke
        Greet(name, c, $changed or 0b1)
    }
}
```

Three things to internalize:

1. **Every `@Composable` takes a hidden `Composer`** — `$composer` and `$changed` are inserted by the plugin. This is why `@Composable` functions can't be called outside `@Composable` scope: the `$composer` parameter isn't available.
2. **Every call site gets a unique key** — positional memoization is `key + position`. This is what lets the runtime tell apart `Text("a")` from `Text("b")` even though they're the same function.
3. **The function is `restartable`** — it registers a closure that re-runs itself when its inputs change. This is the unit of recomposition.

---

## The Composer — The Cursor Into the Slot Table

The `Composer` is the runtime's *cursor*. It moves through the slot table left-to-right as your `@Composable` functions execute. Its job:

| API | What it does |
|---|---|
| `startRestartGroup(key)` | Open a new restart-able group at the current position |
| `endRestartGroup()` | Close the group, capture invalidator for re-running |
| `startReplaceableGroup(key)` | Open a group whose contents are fully replaced on re-execution |
| `startMovableGroup(key, dataKey)` | Open a group whose position can shift (e.g., `LazyColumn` items reordered by `key`) |
| `cache(invalid, block)` | Memoize a value at this slot — basis of `remember` |
| `changed(value)` | Compare to last-stored value; record dirty bit |
| `skipToGroupEnd()` | Skip past this entire group — recomposition shortcut |
| `recordReadOf(state)` | Subscribe this group to a `MutableState` (snapshot system) |

You never call these directly — the compiler emits the calls. But knowing they exist explains your debug output.

---

## The Slot Table (Gap Buffer)

The slot table is **the** core data structure. Think of it as a flat array divided into:

- **Slots** — the actual stored values (group keys, remembered values, state objects).
- **Groups** — metadata records that describe parent-child relationships and skip ranges.

Implemented as a **gap buffer** — like the data structure most text editors use. Inserts/removes near the cursor are O(1); reads are O(1) by index. The gap moves with the cursor as composition proceeds.

```
slots: [grp0 | "Hello" | mutableState | grp1 | "World" | __gap__ | grp2 | ...]
                                              ↑ cursor here
```

When `Greet("Alice")` runs:

1. Composer enters at the group's slot index.
2. Reads the previous `name` value at slot +1: `"Bob"`.
3. Compares to current: changed → marks group dirty.
4. Re-executes the body. New `Text("Hello, Alice")` writes its own grouping marker + content at the same positions.
5. Closes the group; emits invalidation lambda.

If `name` didn't change:

1. Composer reads `"Bob"`, sees no change.
2. Calls `skipToGroupEnd()` — jumps the cursor to the next group **without re-executing anything inside**.
3. Massive perf win.

This is why **stability matters** ([`recomposition-and-state.md`](recomposition-and-state.md)) — only stable parameters can be compared with `changed()` and produce a skip.

---

## Three Kinds of Groups

| Group | When used | Behavior on change |
|---|---|---|
| **Restartable** | `@Composable` function with one or more params | Re-runs the function body; reuses sub-tree if inputs unchanged |
| **Replaceable** | Control flow (`if`/`when` branches) | Old slots discarded, new slots written |
| **Movable** | `LazyColumn`/`LazyRow` items with `key = { it.id }` | Item slots track by `dataKey`; reorder doesn't rebuild items |

```kotlin
@Composable
fun Container(items: List<Item>) {
    if (items.isEmpty()) {       // replaceable group
        EmptyState()              // sub-tree replaced if branch changes
    } else {
        LazyColumn {
            items(items, key = { it.id }) { item ->   // movable group
                Row(item)        // restartable group per row
            }
        }
    }
}
```

The `key = { it.id }` is the difference between "row 5 is reused when an item is inserted at top" and "every row from 0–4 rebuilds because item indexes shifted by 1."

---

## Restartable vs Skippable vs Irrestrictable

The Compose Compiler classifies every `@Composable` function:

| Classification | Meaning | Implications |
|---|---|---|
| **Restartable + Skippable** | Has params, all stable | Can re-run independently; **can be skipped** if inputs unchanged. The good default. |
| **Restartable, NOT Skippable** | Has params, at least one unstable | Re-runs but never skips even when inputs are visually equal. Each call rebuilds the sub-tree. |
| **NOT Restartable (Irrestrictable)** | `@Composable` returning a value, or with `@Composable` lambda parameter expected to read state at call-site | Re-runs only when its parent recomposes |

Enable the Compose Compiler metrics:

```kotlin
android {
    buildTypes {
        debug {
            kotlinOptions.freeCompilerArgs += listOf(
                "-P", "plugin:androidx.compose.compiler.plugins.kotlin:metricsDestination=${rootDir.path}/compose-metrics",
                "-P", "plugin:androidx.compose.compiler.plugins.kotlin:reportsDestination=${rootDir.path}/compose-metrics",
            )
        }
    }
}
```

After a debug build, `compose-metrics/<module>-classes.txt` lists every composable with its skippability state. Use this in a perf audit: every non-skippable `@Composable` that's called in a list / hot path is a recompose-cost source.

---

## The Recomposer

The `Recomposer` is the global scheduler. One per `Composition` (one per `setContent { }` call). Responsibilities:

- Listen for snapshot invalidations (writes to `MutableState`).
- Schedule which groups need to recompose.
- Run on the appropriate dispatcher (`Dispatchers.Main` for Android UI).
- Coordinate with the choreographer for frame timing.

```kotlin
setContent {
    // This is a Composition root.
    // A Recomposer is constructed under the hood, tied to the Activity's lifecycle.
    App()
}
```

Recomposer life:

1. **Idle** — waiting for invalidations.
2. **PendingWork** — at least one group is dirty.
3. **Composing** — actively running recompose.
4. **Applying** — pushing changes to the Applier (UI tree).
5. Back to Idle.

This whole cycle runs in **one frame** for most updates — which is why Compose is fast despite the rewrites: the runtime is engineered to do as little as possible per frame.

---

## The Applier — Bridging Runtime to UI

Compose Runtime doesn't know what a `View` is. It just calls `Applier` operations. The Android Compose UI module supplies a `UiApplier` that turns runtime operations into `LayoutNode` tree mutations:

```kotlin
interface Applier<N> {
    fun down(node: N)                 // push into a child
    fun up()                          // pop back to parent
    fun insertTopDown(index: Int, instance: N)
    fun insertBottomUp(index: Int, instance: N)
    fun remove(index: Int, count: Int)
    fun move(from: Int, to: Int, count: Int)
}
```

For Android Compose, `N = LayoutNode`. For Compose Multiplatform Desktop, `N` is a SkiaShape. For Compose Web, `N` is an HTML element. **Same runtime; different appliers.**

This is the abstraction that lets the same `Greet(name = "Alice")` code render on Android, Desktop, iOS, and Web.

---

## CompositionLocal — Implicit Tree Data

Sometimes you need to pass data (theme, current locale, content color) deeply through the tree without threading it through every parameter:

```kotlin
val LocalCurrentUser = compositionLocalOf<User> { error("No user") }

@Composable
fun App() {
    CompositionLocalProvider(LocalCurrentUser provides currentUser) {
        AppContent()
    }
}

@Composable
fun ProfileBadge() {
    val user = LocalCurrentUser.current   // reads from the nearest provider above
    Text(user.name)
}
```

Two flavors:

| Variant | Behavior |
|---|---|
| `compositionLocalOf { default }` | Reads are tracked. Recomposes any `@Composable` that reads it when the value changes. |
| `staticCompositionLocalOf { default }` | Reads are NOT tracked. Cheaper. But changing the value **invalidates the entire sub-tree** under the provider. Use for values that change rarely (e.g., once at app start). |

Wrong choice = perf bug:

- `compositionLocalOf` for a frequently-changing value with many readers → every reader recomposes per change. Fine, this is what you want.
- `staticCompositionLocalOf` for a frequently-changing value → entire sub-tree invalidates. Catastrophic.
- `compositionLocalOf` for a rarely-changing value with no readers (or one reader) → wasted tracking overhead.

`MaterialTheme.colors` is `staticCompositionLocalOf` — colors rarely change, the sub-tree invalidation is acceptable. Your custom `LocalCurrentScroll` should probably be `compositionLocalOf` — readers must recompose individually.

---

## `remember` Under the Hood

```kotlin
val counter = remember { mutableStateOf(0) }
```

is roughly:

```kotlin
val counter = $composer.cache(invalid = false) { mutableStateOf(0) }
```

`cache(invalid, block)`:

1. Read the slot at the current cursor position.
2. If it has a previous value AND `invalid` is false → return that value.
3. Otherwise run `block`, store the result, return it.

`remember(key1) { ... }` adds a keyed invalidation:

```kotlin
val parsed = remember(jsonString) { parseJson(jsonString) }
// = $composer.cache(invalid = $composer.changed(jsonString)) { parseJson(jsonString) }
```

When `jsonString` changes, the cache is invalidated; the block re-runs; the result is stored in the same slot. **The slot stays at the same position** — that's why positional memoization works across recompositions.

The corollary: don't put `remember` inside a conditional that changes its position:

```kotlin
// BAD
@Composable
fun Bad(show: Boolean) {
    if (show) {
        val state = remember { mutableStateOf(0) }   // disappears when show=false
        Text(state.value.toString())
    }
}
```

When `show` flips true → false → true, the `remember` slot is destroyed on `false` and a new one is allocated on the next `true`. State is lost. Move it outside the conditional, or use `rememberSaveable` if you want it to survive process death.

---

## `derivedStateOf` — Compute Once Per Real Change

```kotlin
val isLongList by remember {
    derivedStateOf { items.size > 100 }
}
```

`derivedStateOf` reads multiple state objects and produces a new state that emits only when the *derived value* changes:

- `items` change from 95 → 96 → 97 → 99: `isLongList` doesn't emit (still `false`).
- `items` change from 100 → 101: `isLongList` doesn't emit (still `true`).
- `items` change from 99 → 100: `isLongList` emits once (`false` → `true`).

Without `derivedStateOf`, any change to `items` would invalidate every reader of `isLongList`. With it, only meaningful changes propagate. Use for expensive computations or boolean flags derived from larger structures.

---

## Side Effects in the Runtime

`LaunchedEffect`, `DisposableEffect`, `SideEffect`, `rememberCoroutineScope` — these are all built on top of the runtime's slot table. See [`side-effects.md`](side-effects.md) for the detailed guide; from a runtime perspective:

- **`LaunchedEffect(keys) { … }`** — stores a coroutine `Job` in a slot. When `keys` change, cancels old job + launches new one.
- **`DisposableEffect(keys) { onDispose { … } }`** — stores a disposer in a slot. Runs `onDispose` when keys change or composition exits.
- **`SideEffect { … }`** — runs the block on every successful composition. No slot allocation. Use for syncing to non-Compose state.

All three are positional-memoized like any other call.

---

## Compose Multiplatform Touch Points

Same runtime, different applier:

```kotlin
// Common code (KMP shared module)
@Composable
fun Greet(name: String) { Text("Hello, $name") }

// Android UI
setContent { Greet("Alice") }              // Android Applier → LayoutNode

// iOS UI
ComposeUIViewController { Greet("Alice") }  // iOS Applier → UIView

// Desktop
application { Window { Greet("Alice") } }  // Desktop Applier → Skia
```

Your `@Composable` is platform-agnostic. The runtime engine is platform-agnostic. Only the Applier differs.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Composable recomposes when nothing seems to change | Unstable parameter (`List<T>`, `var`, lambda allocated per recomposition) | Annotate `@Immutable` / `@Stable`; pass stable types; use `ImmutableList` |
| Function never skippable per compose metrics | One unstable parameter | Find the offender; refactor to stable or annotate |
| State lost on recomposition | `remember` inside conditional that re-enters | Move outside the conditional, or use `rememberSaveable` |
| Entire screen recomposes on theme color change | `staticCompositionLocalOf` for frequently-changing value | Switch to `compositionLocalOf` |
| Tracking overhead for rarely-changing global | `compositionLocalOf` for rare-change value | Switch to `staticCompositionLocalOf` |
| `derivedStateOf` block runs constantly | Reading state outside `remember { derivedStateOf { ... } }` | Wrap in `remember` to position-memoize the derived state |
| Items in LazyColumn rebuild on insert | No `key = { it.id }` | Provide stable keys |
| Compose performance regression after upgrading compiler | New stability rules made existing types unstable | Re-run compose metrics; annotate or refactor |
| `LaunchedEffect(Unit)` runs forever in loop | Body modifies state read by an ancestor → triggers recomposition → new LaunchedEffect | Move state read above `LaunchedEffect`; use proper keys |
| Slot table corruption / crash | `@Composable` called from non-composable context (very rare) | Compiler usually catches; ensure no reflective invocation |
| Memory leak in `remember` | Stored a `Context` or `Activity` reference | `remember` holds across recompositions; clear in `DisposableEffect.onDispose` |
| Two Composables with the same `key()` in LazyColumn | Duplicate keys | Make IDs globally unique within the list |
| Custom `Modifier` factory recomposes everything | Modifier creates new instance per recomposition | Use `Modifier.composed { ... }` carefully; prefer Modifier.Node for new modifiers |
| Sub-tree unexpectedly survives screen switch | Composition is still active in a SubcompositionLayout | Manage parent composition lifetime; clear with `Recomposer.cancel()` |

---

## Common Pitfalls

- **Treating `@Composable` like a regular function.** It's a function with a hidden `Composer` argument and positional registration; can only be called from a `@Composable` context.
- **Calling `@Composable` inside non-composable lambdas.** `list.forEach { Text(it) }` is fine because `forEach`'s lambda is inline; but `flow.collect { Text(it) }` is not — `collect`'s lambda is not `@Composable`.
- **Reading state outside `remember { derivedStateOf { ... } }`.** Re-evaluates on every recomposition.
- **Storing state in module-level variables.** Compose's positional memoization is per-composition; module-level state evades it and creates leaks.
- **Heavy work in composition.** Compose runs your `@Composable` body many times. Filesystem I/O, network calls, JSON parsing in `@Composable` = jank. Move into `LaunchedEffect`, `ViewModel`, or `remember { ... }`.
- **Forgetting that `Modifier.padding(8.dp)` allocates.** A new `Modifier` chain allocation per recomposition is rarely a problem at small scale, but in a `LazyColumn` row Composable called thousands of times, it becomes one. Hoist via `remember { Modifier.padding(8.dp) }` for static modifiers (rarely needed; profile first).
- **Side effects outside `LaunchedEffect`.** Calling `analytics.track()` in the function body fires on every recomposition. Wrap in `LaunchedEffect(key)`.
- **Misusing `key()`.** `key(unstableKey) { ... }` forces full recreation of the sub-tree every time the key changes. Useful but overuse defeats memoization.
- **`SubcomposeLayout` everywhere.** It's an escape hatch; runs a separate composition per measurement pass. Expensive. Use only when needed (typically rare custom layouts).

---

## Probing Questions

1. Walk through the rewrite the Compose Compiler applies to `@Composable fun Greet(name: String)`. What hidden parameters get added, and what does each do?
2. Explain "positional memoization." How is it different from React's virtual DOM diffing?
3. The Slot Table is a gap buffer. Why a gap buffer rather than an array or linked list?
4. Compare `compositionLocalOf` vs `staticCompositionLocalOf`. Give a use case where each is right and where each is wrong.
5. Walk through what `remember { mutableStateOf(0) }` becomes after compilation. Where is the `0` actually stored?
6. Why is the rule "don't put `remember` inside an `if` whose condition changes" — what specifically goes wrong?
7. Restartable, Skippable, Irrestrictable — walk through what each classification means and when a function falls into which.
8. The Compose Multiplatform story: how does the same `Greet("Alice")` work on Android, iOS, and Desktop? Where's the platform-specific code?
9. `derivedStateOf` — why does it need `remember { }` around it? What goes wrong without?
10. The Recomposer lifecycle — Idle → PendingWork → Composing → Applying → Idle. Where does Choreographer fit in?
11. Three group types (Restartable, Replaceable, Movable) — give a concrete example of each.
12. Compose Compiler metrics output shows your function as "not skippable." Walk through your debugging.
13. Your custom Modifier causes every Composable that uses it to recompose. How do you diagnose and fix?

---

## Further Reading

- [`recomposition-and-state.md`](recomposition-and-state.md) — `MutableState`, stability, skipping rules.
- [`side-effects.md`](side-effects.md) — `LaunchedEffect`, `DisposableEffect`, `SideEffect`.
- [`modifiers-and-layout.md`](modifiers-and-layout.md) — `Modifier.Node` and the layout phase.
- [`compose-navigation.md`](compose-navigation.md) — `NavHost` builds on the same runtime.
- [`../architecture/viewmodel.md`](../architecture/viewmodel.md) — state lifting from Composables to ViewModel.
- [`../../kotlin/data-classes.md`](../../kotlin/data-classes.md) — `@Stable` / `@Immutable` for skippability.
- [`../../kotlin/sealed-classes.md`](../../kotlin/sealed-classes.md) — UI state modeling.
- [`../../kotlin/delegation.md`](../../kotlin/delegation.md) — `by remember { mutableStateOf(...) }` mechanics.
- [Jetpack Compose internals — Jorge Castillo](https://jorgecastillo.dev/book-jetpack-compose-internals) — the canonical deep dive.
- [Leland Richardson — Under the hood of Jetpack Compose (KotlinConf 2019)](https://www.youtube.com/watch?v=Q9MtlmmN4Q0) — Compose architect's talk.
- [Android Developers — Compose architecture](https://developer.android.com/jetpack/compose/architecture) — official.
- [Compose Compiler stability metrics](https://developer.android.com/jetpack/compose/performance/stability) — how to read the report.
- [Chris Banes — Composable metrics](https://chris.banes.dev/composable-metrics/) — practitioner's perf-audit guide.
- [JetBrains — Compose Multiplatform](https://www.jetbrains.com/lp/compose-multiplatform/) — same runtime, different appliers.

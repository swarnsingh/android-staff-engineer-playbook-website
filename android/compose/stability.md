# Compose Stability — `@Stable`, `@Immutable`, and Why Your UI Recomposes

> Skippable recomposition is the difference between a buttery 60fps Compose UI and a stuttery one. The compiler decides what's skippable based on **stability**. Most perf bugs in production Compose apps trace to a single unstable parameter forcing an entire sub-tree to recompose every frame. Staff-level mastery is reading the Compose compiler metrics, knowing exactly which types are inferred stable, knowing when to annotate `@Immutable` vs `@Stable`, and using `ImmutableList` for collections — all without breaking the cache.

---

## Why Stability Matters

Compose's smart recomposition decision rule:

> When a parent recomposes, for each child `@Composable` call:
> 1. Are all parameters **stable** types?
> 2. If yes — compare each with `equals()` to its previous value.
> 3. If none changed — **skip** the child's body entirely.
> 4. If any parameter is unstable — **always re-run** the child, regardless.

That last point is the killer. **One unstable parameter forces every recomposition.** A `LazyColumn` with 1000 rows that pass an unstable `List` will recompose every row, every frame, every time anything changes.

Smart recomposition is what makes Compose performant. Stability is what unlocks it. Get this wrong and Compose performs worse than the View system you migrated from.

---

## The Skipping Decision — Compose Compiler Output

Every `@Composable` function ends up in one of these classifications (visible in `compose-metrics/<module>-classes.txt`):

| Classification | Re-runs when parent recomposes? | Re-runs when own state changes? |
|---|---|---|
| **Restartable + Skippable** | Only if any input changed via `equals` | Yes |
| **Restartable, NOT Skippable** | **Always** (any time parent runs) | Yes |
| **Not Restartable / Inline** | When call site recomposes | n/a — inlined into parent |

The goal: **every `@Composable` with parameters should be both restartable AND skippable**.

A function is **not skippable** if any parameter is unstable.

---

## What's Inferred Stable

The Compose compiler classifies these as stable **without any annotation**:

### Primitives + `String`

```kotlin
@Composable fun Greet(name: String, age: Int, active: Boolean) { /* skippable ✅ */ }
```

`Int`, `Long`, `Double`, `Float`, `Boolean`, `Char`, `Byte`, `Short`, `String` — all stable. `String` is included because it's immutable.

### Function types without captures

```kotlin
@Composable fun Button(onClick: () -> Unit) { /* depends */ }
```

If `onClick` is a method reference (`vm::onClick`) or a stable function (`{ navigate() }` with no captures of unstable state), it's stable. If it captures a `var`, an unstable `List`, or a state object directly, it can become unstable.

Pro tip: pass method references (`vm::processIntent`) instead of lambdas (`{ vm.processIntent(it) }`). Method references are stable; lambdas allocated per recomposition aren't.

### Data classes where every property is stable

```kotlin
data class User(val id: String, val name: String, val age: Int)
// → Inferred STABLE
```

Two strict requirements:
- All properties are `val` (not `var`).
- All property types are themselves stable (primitives, `String`, other stable classes).

### Objects

```kotlin
object Constants { const val PI = 3.14 }
// → Stable; no state to track
```

### `MutableState<T>` and `State<T>`

The state holders themselves are annotated `@Stable`. Their wrapped values are tracked separately via the snapshot system.

---

## What's Inferred Unstable

### Interfaces and abstract types

```kotlin
@Composable fun ItemRow(items: List<Item>) { /* NOT skippable ❌ */ }
@Composable fun Lookup(map: Map<String, User>) { /* NOT skippable ❌ */ }
```

The compiler can't see the implementation of `List`, `Map`, `Set`. Anything could be a mutable subclass. Conservatively classified as unstable.

This is the **#1 source of unintentional unstable params**. Every `LazyColumn(items: List<T>)` you write is potentially the unstable parameter killing your perf.

### `var` properties

```kotlin
data class User(val id: String, var name: String)   // NOT stable due to `var name`
```

A mutable property means the value can change at any time — compose can't trust `equals()` returns will stay consistent. The entire class becomes unstable.

### Mutable collections

```kotlin
data class Cart(val items: MutableList<Item>)   // NOT stable
```

`MutableList`, `MutableMap`, `MutableSet`, `mutableSetOf()`, etc. — all unstable.

### Types from other modules (sometimes)

If `User` is defined in `:core:model` and Compose Compiler hasn't seen it yet when compiling `:feature:cart:impl`, it may be conservatively treated as unstable depending on the Compose compiler version.

Most apps fix this by annotating exported types in `:core:model` with `@Immutable` so the stability decision doesn't depend on compilation order.

### Lambda that captures unstable

```kotlin
@Composable
fun Row(item: Item, onClick: () -> Unit) { /* depends on onClick */ }

// At call site:
Row(item, onClick = { items.add(it); save() })   // captures `items` (mutable) → onClick unstable
```

Refactor: pass the necessary stable state through other params; keep lambdas tiny and free of mutable captures.

---

## The Two Annotations

### `@Immutable`

```kotlin
@Immutable
data class User(val id: String, val tags: List<String>)
```

**Tells the compiler:** "Every property here, even though it might look unstable to you, can be treated as immutable. Trust me."

When to use:
- The class has a `List<T>` / `Set<T>` / `Map<K, V>` that you *promise* never to mutate after construction.
- You construct new instances with new lists rather than mutating existing ones.
- You can guarantee `equals()` is consistent across recompositions.

If you lie — e.g., you annotate `@Immutable` but your code mutates the internal list — you'll get stale UI and Compose won't recompose when you want.

### `@Stable`

```kotlin
@Stable
interface State<out T> {
    val value: T
}
```

**Tells the compiler:** "Properties may change, but the change is observable through the snapshot system. `equals()` returns are still reliable."

When to use:
- An interface or class that *does* have mutable state, but the mutation is tracked properly (via `MutableState` or similar).
- A function that returns a stable value (e.g., `@Stable fun Modifier.padding(8.dp)` declares the resulting modifier as stable).

`@Stable` is a weaker guarantee than `@Immutable`. Most app code wants `@Immutable`; framework / library code uses `@Stable` for stateful but observable interfaces.

### Pick by table

| Annotation | Guarantees | Use when |
|---|---|---|
| `@Immutable` | All properties never change after construction | You have a UI state class with `List<T>` you don't mutate |
| `@Stable` | `equals()` is reliable; mutation is properly observed by Compose | You have a custom state holder interface |
| (neither) | Compose infers from the structure | All properties are primitives + `String` + stable types |

---

## Strong Skipping Mode (Compose Compiler 1.5.4+)

Modern Compose Compiler ships with **Strong Skipping Mode**, enabled by default in Compose 1.7+.

Key change: **Composable functions become skippable even with unstable parameters, as long as those parameters are equal to their previous value via `equals()`.**

What this means in practice:

| Before Strong Skipping | After Strong Skipping |
|---|---|
| `@Composable fun List(items: List<Item>)` — never skips | Skips when `items.equals(previousItems)` |
| Lambdas capturing unstable state — never stable | Stable as long as their equality is stable |
| Required `@Immutable` annotations for `List<T>` use cases | Often unnecessary |

This is a huge improvement and significantly reduces the need for `@Immutable` annotations on every domain type. **Verify your Compose Compiler version supports it before relying on it.**

Even with Strong Skipping, deeply unstable types still cost — the `equals()` check has to run, and if the unstable parameter is recomputed per recomposition (a new `List` allocated each time), it still won't skip.

---

## Collections: `ImmutableList` and `PersistentList`

`kotlinx.collections.immutable` provides truly immutable collection types that Compose treats as fully stable:

```kotlin
import kotlinx.collections.immutable.ImmutableList
import kotlinx.collections.immutable.PersistentList
import kotlinx.collections.immutable.persistentListOf
import kotlinx.collections.immutable.toImmutableList

@Composable
fun TagList(tags: ImmutableList<String>) {   // ← guaranteed-stable parameter
    LazyRow { items(tags) { Text(it) } }
}

// Usage
val tags = persistentListOf("urgent", "review", "draft")
TagList(tags = tags)
```

| Type | Use when |
|---|---|
| `ImmutableList<T>` (interface) | API surface |
| `PersistentList<T>` (subtype) | Need efficient `add`/`remove` returning new instances |
| `List<T>` annotated `@Immutable` parent class | Domain types where you control all construction |
| Plain `List<T>` | App-internal code where Strong Skipping covers you |

```kotlin
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-collections-immutable:0.3.7")
}
```

For `:core:model` types, use `ImmutableList` in `data class` properties. Now the entire class is fully stable without `@Immutable` annotation.

---

## Stability Config Files

For third-party types you can't annotate (Java types, libraries without Compose support), use a stability config file:

```
// app/compose_stability_config.conf
java.time.LocalDate
java.time.LocalDateTime
java.util.UUID
com.somelibrary.OpaqueType
```

```kotlin
android {
    composeCompiler {
        stabilityConfigurationFiles.addAll(
            project.layout.projectDirectory.file("compose_stability_config.conf")
        )
    }
}
```

Listed types are treated as stable. Use for value-types from libraries that you've verified are immutable but the Compose Compiler can't see.

---

## Reading the Compose Compiler Metrics

Enable per-module metrics:

```kotlin
// build-logic/convention/.../ComposeMetrics.kt
tasks.withType<KotlinCompile>().configureEach {
    if (System.getenv("ENABLE_COMPOSE_METRICS") == "true") {
        kotlinOptions.freeCompilerArgs += listOf(
            "-P", "plugin:androidx.compose.compiler.plugins.kotlin:metricsDestination=${rootDir.path}/compose-metrics/${project.name}",
            "-P", "plugin:androidx.compose.compiler.plugins.kotlin:reportsDestination=${rootDir.path}/compose-metrics/${project.name}",
        )
    }
}
```

Run a build with `ENABLE_COMPOSE_METRICS=true ./gradlew :app:assembleRelease`. Inspect:

### `<module>-classes.txt`

```
stable class User {
  stable val id: String
  stable val name: String
}

unstable class Cart {
  stable val id: String
  unstable val items: List<CartItem>  ← culprit
}
```

### `<module>-composables.txt`

```
restartable skippable scheme("[androidx.compose.ui.UiComposable]") fun Greet(
  stable name: String
)

restartable fun CartScreen(   ← NOT skippable!
  unstable cart: Cart            ← culprit
)
```

The audit is mechanical: find every `restartable fun X(` that's missing the `skippable` keyword. Each one is a perf opportunity.

### `<module>-module.json`

Aggregate metrics: number of composables, % skippable, % stable classes. Track this over time as a build-output. A regression means someone introduced an unstable parameter.

---

## Real Android Patterns

### Pattern 1: UI state as `@Immutable` data class with `ImmutableList`

```kotlin
@Immutable
data class CartUiState(
    val items: ImmutableList<CartItem> = persistentListOf(),
    val total: Money = Money.ZERO,
    val isLoading: Boolean = false,
    val error: String? = null,
)

@Composable
fun CartScreen(state: CartUiState) {
    // ← fully skippable; state.equals() compared on every recomposition
}
```

### Pattern 2: Method reference for `onClick`

```kotlin
@Composable
fun CartScreen(vm: CartViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    CartContent(
        state = state,
        onAddItem = vm::addItem,    // ← method reference; stable
        onRemoveItem = vm::removeItem,
    )
}
```

Pre-allocating the lambdas in the parent and passing references through stays skippable.

### Pattern 3: Stable accessor function

```kotlin
@Stable
fun formatPrice(cents: Long): String = NumberFormat.getCurrencyInstance().format(cents / 100.0)
```

Marks the return as stable so wrap-then-pass patterns don't break skipping.

### Pattern 4: Wrapper for inherently-unstable third-party types

```kotlin
// Wrap a 3rd-party type you can't annotate
@Immutable
data class OkHttpRequestWrapper(val request: Request)
```

Crude but effective. Or use the stability config file.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| LazyColumn re-renders every row on any change | `items` parameter is `List<T>` (unstable) | `ImmutableList<T>` or `@Immutable` wrapper |
| Compose metrics show "NOT skippable" everywhere | All public APIs use `List` / `Map` | Migrate to `ImmutableList`; annotate model types |
| Frame rate drops after upgrading Compose Compiler | New stability rules made previously-stable types unstable | Re-run metrics; check `var` properties and 3rd-party deps |
| `@Immutable` annotation has no effect | Class has a `var` somewhere | Cannot mix `@Immutable` and `var`; refactor to `val` |
| Performance regression after migrating to `kotlinx.collections.immutable` | Excessive copying when building lists | Use `PersistentList` builder pattern |
| Compose metrics output is empty | Plugin args not added to module's kotlinc | Verify `freeCompilerArgs` in build-logic |
| Strong Skipping Mode doesn't kick in | Compiler version too old | Update to Compose Compiler 1.5.4+ / Compose 1.7+ |
| State change in ViewModel doesn't update UI | Used `@Stable` annotation but class isn't truly stable | Re-audit — `@Stable` is a contract you must keep |
| Recomposition skip works locally but not in release | R8 may strip `@Stable` annotations | Add `consumerProguardFiles` rule to keep them |
| `LocalContext.current` reads cause cascading recomposition | Reading too high in the tree | Move read closer to the consuming Composable |
| `derivedStateOf` doesn't reduce recomposition | Block accessed mutable state outside it | Move all reads inside `derivedStateOf { }` |
| `@Composable` with `Modifier` param recomposes every frame | Custom modifier creates new instance per recomposition | Use `Modifier.composed { }` carefully; `remember { }` static modifiers |
| Cross-module type shows unstable | `@Immutable` not present on the model | Annotate in the `:api` module or use stability config |
| `Composable` lambda parameter shows unstable | Lambda captures unstable state | Hoist captures; pass needed state as parameters |

---

## Common Pitfalls

- **Annotating `@Immutable` without enforcing it.** If your "immutable" `User` has a `MutableList<String>` you populate later — Compose's assumption breaks; UI shows stale state.
- **Adding `@Stable` to fix metrics output.** Don't bandage. Ask: *why* is this unstable? Often the fix is `var` → `val` or `List` → `ImmutableList`.
- **Mutating an `ImmutableList`.** It's actually immutable — operations return new instances. `list.add(x)` doesn't exist; use `list + x` or `PersistentList.Builder`.
- **Per-row inline `onClick = { onItem(item) }`.** Allocates a new lambda per row per recomposition. Pre-allocate or use `key { onClick = { onItem(item) } }`.
- **Reading `vm` properties inside a `@Composable` instead of `by state.collectAsStateWithLifecycle()`.** Direct ViewModel reads cause leaks and don't participate in recomposition properly.
- **Putting state directly in a `var` field.** Compose can't observe non-`State` mutations.
- **Forgetting to instrument compose-metrics in CI.** Without trend tracking, stability regressions go unnoticed for months.
- **Trusting Strong Skipping Mode to fix everything.** It helps, but truly recomputed-every-time values (a freshly allocated `List`) still won't skip.
- **Stability config file for types you don't control + then those types change.** You promised stability; the type now mutates; you have a latent bug. Re-audit after every upgrade.
- **Annotating every type `@Immutable` "just to be safe."** Confuses readers; provides false security if any property is actually `var`.

---

## Probing Questions

1. Walk through Compose's smart recomposition decision flow. What happens at each step when a parent recomposes?
2. Why is `List<T>` inferred as unstable but `String` is stable? Walk through the reasoning.
3. Compare `@Immutable` vs `@Stable`. Give an example where you'd pick each.
4. Strong Skipping Mode (Compose 1.7+) — what changed, and where does it still fall short?
5. `ImmutableList` vs `@Immutable data class Foo(val items: List<T>)` — both work. When pick each?
6. Read this `<module>-composables.txt` snippet and identify the perf bug: `restartable fun Row(stable id: String, unstable tags: List<String>)`.
7. Why is `onClick = { vm.process(item) }` worse than `onClick = vm::process` in a `LazyColumn`?
8. A `@Composable` recomposes 60 times per second despite no apparent input changes. Walk through your debugging.
9. Stability config file — when do you reach for it instead of `@Immutable`?
10. `MutableState<T>` is `@Stable` even though it's mutable. Explain why this is consistent.
11. Why does `data class User(val id: String, var name: String)` (note the `var`) ruin stability for the entire class?
12. Track skippability % over time in CI. Walk through your dashboard design and what regression looks like.

---

## Further Reading

- [`compose-runtime.md`](compose-runtime.md) — the runtime that uses stability decisions.
- [`recomposition-and-state.md`](recomposition-and-state.md) — the state side of the system.
- [`side-effects.md`](side-effects.md) — interactions between effects and stability.
- [`modifiers-and-layout.md`](modifiers-and-layout.md) — `Modifier` stability.
- [`../../kotlin/language-core/data-classes.md`](../../kotlin/language-core/data-classes.md) — stable `data class` requirements.
- [`../../kotlin/language-core/null-safety.md`](../../kotlin/language-core/null-safety.md) — `var` traps that ruin stability.
- [`../architecture/mvvm-vs-mvi.md`](../architecture/mvvm-vs-mvi.md) — UI state design with stability in mind.
- [Compose Compiler — Stability documentation](https://developer.android.com/jetpack/compose/performance/stability) — official.
- [Strong Skipping Mode — Compose 1.7+](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping) — official.
- [Chris Banes — Composable metrics](https://chris.banes.dev/composable-metrics/) — practitioner's audit guide.
- [kotlinx.collections.immutable](https://github.com/Kotlin/kotlinx.collections.immutable) — `ImmutableList` / `PersistentList`.
- [Jorge Castillo — Jetpack Compose Internals (book)](https://jorgecastillo.dev/book-jetpack-compose-internals) — chapter on stability and skipping.

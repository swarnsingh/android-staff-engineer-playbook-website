# Locality of Reference

## Overview

**Locality of reference** is the observation that things accessed together tend to be accessed close together — in time, in space, or both. It originated in CPU cache design in the 1960s: when a program reads a memory address, the hardware brings nearby addresses into the cache because they're likely to be read next. Subsequent reads hit the cache instead of slow main memory, making the program faster by orders of magnitude.

The principle has two flavors:

- **Temporal locality**: if you accessed something recently, you'll probably access it again soon. Foundation of caches, LRU eviction, prefetching.
- **Spatial locality**: if you accessed something at one address, you'll probably access nearby addresses soon. Foundation of cache lines, contiguous arrays, page prefetching.

In software architecture, the principle generalizes to **"things that change together should live together"** — what Robert Martin calls the *Common Closure Principle*. Code that's modified for the same reason should be packaged together so the change is local. Code that's modified for unrelated reasons should be separated so changes don't ripple. The mobile-engineering payoff: a "feature module" you can read and modify in one folder is dramatically easier to evolve than the same logic spread across `ui/`, `viewmodel/`, `repository/`, `network/` siloed by layer.

This file covers locality at three layers: **CPU caches** (where the term originates), **state and data layout** (Compose state, primitive arrays, packed structs), and **code organization** (package-by-feature, modularization, the common-closure principle). All three reduce the cost of "going far away" — for the CPU, far means a cache miss; for a developer, far means jumping across the codebase.

---

## Why It Exists

Two costs drive the principle:

1. **Hardware: memory access has a hierarchy of costs.** Cache and memory latency depend on the processor, frequency, access pattern and contention. Storage is a separate I/O path. Spatial and temporal locality can keep a useful working set near the CPU, but there is no universal cycle table or speedup.
2. **Cognition: navigating a distant codebase is expensive.** When you change a feature, you should be able to read and modify the relevant code in one place. If the "feature" is spread across `ui/login/`, `viewmodels/auth/`, `data/repositories/`, and `network/auth_api/`, every change requires four cognitive jumps. The literature calls this *closeness* or *cohesion*; the practical effect is identical to cache locality — the closer your working set, the cheaper the work.

The principle exists because both costs are universal. Hardware can never eliminate latency to distant memory; humans can never eliminate friction navigating distant code. The best response is to colocate what's accessed together.

---

## Historical Context

1. **Belady's MIN algorithm (1966).** Bélády studied replacement policies; the ideal MIN policy evicts the page whose next use is farthest in the future. That is not LRU (evict least recently used), nor a proof that every workload has locality. MIN is a comparison bound that needs future knowledge.
2. **Denning's working set model (1968).** Peter Denning formalized the *working set* as the set of pages a process accesses in a recent time window. Programs that respect spatial and temporal locality have small working sets and run efficiently in limited memory; those that don't thrash.
3. **CPU cache hierarchies (1970s+).** Hardware engineers built increasingly deep cache hierarchies (L1, L2, L3) specifically to exploit locality. Modern x86 processors have ~64-byte cache lines — read one byte and you get 63 neighbors for free.
4. **Mike Acton, *Data-Oriented Design* (2014).** A C++ game-engine talk arguing that for performance-critical code, the *layout of data* matters more than object-oriented modeling. Cache misses are the dominant cost in modern CPUs.
5. **Robert C. Martin, *Common Closure Principle* (1990s).** The architectural side: classes that change for the same reason belong in the same package. Functional cohesion is the human analog of cache locality.
6. **Android modularization (2018+).** Google formally endorsed package-by-feature and gradle module-per-feature as the path to scalable Android codebases. The driving rationale was build performance (only changed modules recompile) and cognitive locality (everything for one feature is in one folder).
7. **Jetpack Compose state hoisting (2021+).** Compose tracks state reads in composition, layout and drawing. Read placement, restart scopes and skipping determine work; the declaration's distance alone does not.

The arc: from hardware (caches) to systems (working sets) to code organization (cohesion, modularization), with each layer recognizing the same underlying truth that locality reduces cost.

---

## First Principles

### 1. Temporal locality

If you access X at time T, you'll likely access X again at time T+1, T+2, …

**Why it's true.** Loops re-read the same variables. Functions re-call the same helpers. Users navigate to the same screen multiple times in a session. Hot data dominates request patterns; cold data is rare.

**Architectural consequence.** Caches work. LRU eviction works. Memoization works. Connection pooling works. Long-lived objects in scopes that match their access patterns work.

### 2. Spatial locality

If you access address X, you'll likely access X+1, X+2, … soon after.

**Why it's true.** Arrays are iterated in order. Structs have fields read together. Image pixels are processed neighbor-to-neighbor. Database rows on the same page are queried together.

**Architectural consequence.** Cache lines fetch neighbors for free. Contiguous arrays beat linked lists. Struct-of-arrays often beats array-of-structs. Database indices group related rows on disk pages.

### 3. Common closure (the code-organization analog)

If two pieces of code tend to be modified together (for the same business reason), they should live together.

**Why it's true.** Features have boundaries. A "checkout" change affects the checkout UI, the checkout viewmodel, the checkout API client, the checkout database table. If those live in one folder, the change is local. If they're scattered, you spend cognitive cycles assembling the change graph.

**Architectural consequence.** Package-by-feature beats package-by-layer for large codebases. Gradle modules per feature beat one monolithic module. Compose state lives at the closest common ancestor.

### 4. The corollary: separation of unrelated change

The flip side of "things that change together live together" is "things that change for different reasons live apart." Mixing unrelated change axes in one file forces every reason-to-change to touch the same file, raising contention and review cost.

**Architectural consequence.** Splitting `Utils.kt` into `StringUtils.kt`, `DateUtils.kt`, `CollectionUtils.kt` is locality work — strings and dates change for different reasons.

---

## Mental Model

Think of locality as **proximity reducing cost**. The CPU's cost model: the closer the data is to the registers, the faster it's accessed. The developer's cost model: the closer the code is to what you're already reading, the faster you can modify it.

The wrong default — for both CPUs and developers — is to scatter things "logically" by category. Sorting all `*.viewmodel.kt` files into a `viewmodels/` folder feels organized, but it forces every working session to jump between folders. The same is true at the hardware level: storing fields of a struct in different memory regions "by type" wrecks cache locality even though the type-grouping looks tidy.

The right default is **co-location by access pattern**. What does the work session touch? Put it together. What does the inner loop touch? Lay it out contiguously. The pattern of *use* dictates the layout, not the pattern of *taxonomy*.

A useful analogy: a **toolbox vs a categorized shelving system**. If you're a plumber going on a job, your toolbox holds wrenches, plumber's tape, fittings, and a flashlight — everything you need for a plumbing job, even though they're different "categories." A shelving system that sorts by "metal tools," "plastic tools," "lights" would force you to walk between shelves for every task. The toolbox is *organized by access pattern* — what gets used together.

---

## Internal Mechanics

### CPU cache lines and how they reward spatial locality

Caches transfer data in lines; 64 bytes is a useful illustrative size, not a universal device contract. Nearby reads may reuse a resident line, while eviction, contention, prefetching and the cache hierarchy determine actual hits and latency.

For sequential access, this is essentially free:

```kotlin
val xs = IntArray(1_000_000)
for (i in xs.indices) {
    sum += xs[i]   // sequential primitive reads; actual misses depend on caches and prefetching
}
```

For random access, it's expensive:

```kotlin
val xs = IntArray(1_000_000)
val indices = (0 until 1_000_000).shuffled()
for (i in indices) {
    sum += xs[i]   // indirect access; measure this separately from shuffling/boxing costs
}
```

This sketch contrasts access patterns, not measured results. The shuffled index list also adds boxing, allocations and indirection; isolate those effects in a representative benchmark.

### Array of structs vs struct of arrays

Consider 1 million points:

```kotlin
// Array of structs (AoS)
data class Point(val x: Float, val y: Float, val z: Float, val label: String)
val points: Array<Point> = ...

// Struct of arrays (SoA)
class PointCollection(
    val xs: FloatArray,
    val ys: FloatArray,
    val zs: FloatArray,
    val labels: Array<String>
)
```

If a loop needs only x-coordinates, a `FloatArray` avoids following a reference for each `Point` and avoids loading unrelated fields from those objects' cache lines. On Kotlin/JVM, `Array<Point>` is an array of object references, not packed C structs. SoA may help this access pattern; actual density and speed depend on object layout, runtime and hardware.

For mobile, this matters in: image processing, video decoding, ML inference, physics simulation. For UI/business logic, AoS is fine.

### Object headers and reference chasing

In the JVM, every object has a header (8-16 bytes on 64-bit) holding metadata (class pointer, hash, GC state). `Array<Point>` is actually an array of *references* to heap-allocated Points scattered across memory:

```
xs: [ref][ref][ref][ref] ...
     ↓    ↓    ↓    ↓
    Point Point Point Point     <- scattered in heap
```

Iterating `xs` chases each reference — each Point access is potentially a cache miss. `FloatArray` is a single contiguous buffer with no headers per element:

```
xs: [4][8][12][16][20][24][28] ...   <- raw bytes, contiguous
```

This is why Kotlin's `IntArray`, `LongArray`, `FloatArray`, etc. are not just "primitive arrays" — they're a locality tool.

### Code organization: package-by-feature vs package-by-layer

```mermaid
flowchart TD
    app["com.example.app/"] --> ui["ui/"]
    ui --> screens["LoginScreen.kt<br/>CheckoutScreen.kt<br/>ProfileScreen.kt"]
    app --> vm["viewmodel/"]
    vm --> viewmodels["LoginViewModel.kt<br/>CheckoutViewModel.kt<br/>ProfileViewModel.kt"]
    app --> repo["repository/"]
    repo --> repositories["LoginRepository.kt<br/>CheckoutRepository.kt<br/>ProfileRepository.kt"]
    app --> network["network/"]
    network --> apis["LoginApi.kt<br/>CheckoutApi.kt<br/>ProfileApi.kt"]
```

Working on Login? Jump between 4 folders.

```mermaid
flowchart TD
    app["com.example.app/"] --> login["login/"]
    login --> loginFiles["LoginScreen.kt<br/>LoginViewModel.kt<br/>LoginRepository.kt<br/>LoginApi.kt"]
    app --> checkout["checkout/<br/>checkout UI, state, data, and API"]
    app --> profile["profile/<br/>profile UI, state, data, and API"]
```

Working on Login? Stay in one folder.

The layer view has its place — `core/`, `common/`, `theme/`, `network/` shared across features — but the dominant axis should match the dominant change axis, which is feature.

### Compose state locality

Compose tracks snapshot-state reads by the scope and phase in which they execute. A changed value can invalidate composition, layout or draw work; the declaration location alone does not determine recomposition:

```kotlin
// Low locality: state hoisted too high
@Composable
fun App() {
    var textInput by remember { mutableStateOf("") }   // state lives at App level
    Column {
        Header()
        ContentArea()
        TextField(value = textInput, onValueChange = { textInput = it })
    }
}
```

A keystroke invalidates the restart scope that read `textInput` during composition. Unchanged child calls can be skipped; declaring the state in `App` does not force every descendant to execute.

```kotlin
// High locality: state co-located with consumer
@Composable
fun App() {
    Column {
        Header()
        ContentArea()
        LocalInput()
    }
}

@Composable
fun LocalInput() {
    var textInput by remember { mutableStateOf("") }   // state lives here
    TextField(value = textInput, onValueChange = { textInput = it })
}
```

The read is now inside `LocalInput`'s scope. This can narrow work while preserving local ownership, but state read phase, parameters and skipping still govern execution.

---

## Architecture

```mermaid
flowchart TB
    subgraph CPU["CPU layer: spatial + temporal locality"]
        L1["L1 cache"]
        L2["L2 cache"]
        L3["L3 cache"]
        Main["Main memory"]
        L1 --> L2 --> L3 --> Main
    end

    subgraph Data["Data layer: layout choices"]
        AoS["Array of structs: scattered fields"]
        SoA["Struct of arrays: contiguous fields"]
        Refs["Reference graph: pointer chasing"]
        Primitive["Primitive arrays: contiguous bytes"]
    end

    subgraph Code["Code layer: common closure"]
        Layer["Package by layer: scattered feature"]
        Feature["Package by feature: cohesive feature"]
        Hoisted["Broad composition reads"]
        Local["Narrower read scopes"]
    end

    CPU -. enables .-> Data
    Data -. mirrors .-> Code
```

---

## Production Example

### Image processing: Packed pixel buffer for cache efficiency

An Android `Bitmap.getPixels` processing path can use a packed ARGB `IntArray`; this does not describe every Coil, Glide or native decoding implementation:

```kotlin
val pixels = IntArray(width * height)
bitmap.getPixels(pixels, 0, width, 0, 0, width, height)

for (i in pixels.indices) {
    val argb = pixels[i]
    val gray = ((argb shr 16 and 0xFF) + (argb shr 8 and 0xFF) + (argb and 0xFF)) / 3
    pixels[i] = (argb and 0xFF000000.toInt()) or (gray shl 16) or (gray shl 8) or gray
}
```

The pixel buffer is contiguous; each iteration touches 4 bytes. With the illustrative 64-byte cache lines used earlier, sequential access can reuse each fetched line. An object-per-pixel layout adds reference and object overhead; measure the difference rather than assuming a multiplier.

### Compose recomposition: hoisting to the right level

In a checkout screen with line items and a total:

```kotlin
@Composable
fun CheckoutScreen(vm: CheckoutViewModel) {
    val state by vm.uiState.collectAsStateWithLifecycle()
    Column {
        ItemList(items = state.items, onChange = vm::updateQuantity)
        // Total recomputes when state changes; that's correct
        Total(amount = state.total)
        CheckoutButton(
            enabled = state.canCheckout,
            onClick = vm::submit
        )
    }
}
```

`state` is read at `CheckoutScreen` and passed down. Compose's recomposer tracks the read and recomposes the screen when state changes. Children receive parameter slices and may be skipped when eligible and unchanged. They do not independently subscribe to slices of the parent state merely because parameters were passed. This is high-locality state passing.

### Gradle modules per feature for build locality

```text
:app
:feature:login
:feature:checkout
:feature:profile
:core:network
:core:database
:core:design-system
```

A contained implementation change can avoid downstream compilation when ABI and dependency rules allow. Task inputs, generated code, variants, API exposure and caches determine actual invalidation. Kotlin incremental compilation also works inside a single module; neither layout guarantees bounded build time.

---

## Android Example

### Primitive arrays for sensor data buffers

A common Android pattern is high-frequency sensor data (accelerometer, gyroscope, audio):

```kotlin
// Single-owner, fixed-capacity buffer: reject overflow rather than corrupting indices.
class AccelerometerBuffer(capacity: Int) {
    init { require(capacity > 0) }
    private val xs = FloatArray(capacity)
    private val ys = FloatArray(capacity)
    private val zs = FloatArray(capacity)
    private val timestamps = LongArray(capacity)
    private var size = 0

    fun add(x: Float, y: Float, z: Float, ts: Long) {
        check(size < xs.size) { "Buffer full; drain or reset before adding" }
        xs[size] = x
        ys[size] = y
        zs[size] = z
        timestamps[size] = ts
        size++
    }

    fun magnitudes(): FloatArray = FloatArray(size) { i ->
        sqrt(xs[i] * xs[i] + ys[i] * ys[i] + zs[i] * zs[i])
    }
}
```

Four contiguous primitive arrays. Iterating them is cache-friendly. A naïve `data class Sample(val x, val y, val z, val ts)` collection would be cleaner code but allocate per-sample, fragment the heap, and miss cache lines on every access. Choose the layout from measured allocation and processing cost; 100 Hz is not a universal crossover.

### State hoisting to a feature module

A feature module owns its state. Cross-module navigation passes serializable arguments; cross-module data sharing goes through small, explicit APIs:

```kotlin
// :feature:checkout exposes only what other features need
object CheckoutFeature {
    fun navGraph(): NavGraph = ...
    fun startCheckout(navController: NavController, orderId: OrderId) {
        navController.navigate("checkout/$orderId")
    }
}

// internal to :feature:checkout
internal class CheckoutViewModel(...) { ... }
internal data class CheckoutUiState(...) { ... }
internal class CheckoutRepository(...) { ... }
```

Other features see only `CheckoutFeature`. The state, viewmodel, repository, and database access stay local to the module — and so does the cost of changing them.

### Database row layout for query locality

SQLite uses configurable pages (commonly 4 KiB); Android/runtime configurations can differ. B-tree cells store some payload locally and can use overflow pages for large records, so a large BLOB does not mean each row occupies exactly one page. Separating rarely read payloads can improve hot-query density, but covering indexes, projections and query plans also matter.

```kotlin
// Locality-aware schema
@Entity
data class User(
    @PrimaryKey val id: Long,
    val name: String,
    val email: String,
    val createdAt: Long
)

// Avatar blobs stored separately
@Entity
data class UserAvatar(
    @PrimaryKey val userId: Long,
    val data: ByteArray
)
```

Querying user names doesn't pull avatar bytes through the SQLite page cache. Common queries stay local; rare avatar fetches are explicit.

---

## Tradeoffs

**Advantages**

- **Performance.** Contiguous data layouts can be an order of magnitude faster than scattered references for numerical workloads.
- **Reduced build times.** Modular codebases recompile only changed modules.
- **Easier reasoning.** Code that lives together is read and changed together — lower cognitive overhead.
- **Targeted recomposition.** Compose state at the right level minimizes redraw scope.

**Disadvantages**

- **SoA loses abstraction.** A `PointCollection` with parallel arrays is harder to reason about than a `List<Point>`. Reserve for hot paths.
- **Package-by-feature creates duplication.** Each feature reinvents date formatting, API client wiring, etc. Avoided by a thin `:core:` module for genuinely shared utilities.
- **Feature modules add Gradle overhead.** Each module has its own `build.gradle.kts`, config, dependencies. Too many tiny modules slow Gradle's configuration phase.
- **State locality can fight test simplicity.** Hoisting state to the lowest level can make end-to-end tests harder because the test has to navigate to find the state.

**When not to apply**

- For one-time scripts or throwaway prototypes — layout and structure cost doesn't pay back.
- For shared utilities — don't force a `:string-utils:` module per string utility class; group reasonable taxonomies.
- For business logic where clarity matters more than nanosecond cache efficiency.

---

## Failure Modes

**`:core:` or `:common:` becomes a dumping ground.** Every feature needs "just one shared thing" and dumps it into `:core:`. Soon `:core:` depends on half the codebase and has multi-axis change reasons, defeating locality. Mitigation: partition `:core:` by axis (`:core:network`, `:core:design-system`, `:core:logging`) and review additions strictly.

**Scattered Compose state forces broad recomposition.** Only a changed state value invalidates its readers; restart scopes and skipping determine descendant execution. Mitigation: move state to the closest common ancestor of readers; use `remember` at the lowest level possible.

**Pointer-chasing iteration over object arrays.** A hot path iterates `Array<Item>` where each `Item` is heap-allocated; potential extra cache misses and reference loads. Mitigation: convert to primitive arrays where possible, and benchmark the result; `Sequence` does not fix pointer locality.

**Package-by-layer in a 100-module codebase.** Every feature change touches 4 modules. Build times balloon. Mitigation: feature modules first, layer modules within (`:feature:checkout/data`, `:feature:checkout/ui`).

**Feature module with no boundary.** A "feature" module that exposes its `internal class` as `public` to other features, becoming a shared library. Mitigation: enforce module boundaries via `internal` discipline and `api-validator` tools; the feature should expose a small, documented surface only.

**State hoisting taken too literally.** Lifting input field state to the ViewModel for "purity" forces a recomposition trip through the ViewModel on every keystroke. Mitigation: ephemeral UI state stays local (`remember { TextFieldValue("") }`); business-meaningful state goes to the ViewModel.

---

## Performance Considerations

- **Profile the relevant target.** Cache misses, stalls and allocation can matter, but no single mechanism dominates every hot path. Primitive-array layout can help numerical loops; JVM boxing may reuse objects or be optimized, so it is not necessarily one fresh allocation per read.
- **Compare layouts by access pattern.** SoA can help column-wise work; row-wise work can favor other layouts. A `Sequence` may reduce intermediate allocations but does not make referenced objects contiguous.
- **Measure Gradle tasks and invalidation.** Module count and graph shape affect configuration, parallelism and recompilation; there is no linear formula or universal best module count.
- **Inspect Compose read scopes and phases.** Layout or draw reads can skip composition, and unchanged children may be skipped after a parent restarts. Do not infer redraw count from where `remember` appears.

## Reliability Considerations

- **A module is a build/API boundary.** `internal` limits Kotlin source access within a module; it is not a runtime fault, memory or process boundary. Shared mutable objects and uncaught failures can cross features.
- **A coroutine scope is a lifetime boundary.** It does not imply a single thread. Use confinement, immutable state or synchronization for shared mutation.
- **Select tests from affected contracts.** Cross-feature integration and release validation can still be necessary after a local change. Baseline-profile coverage depends on affected user journeys and release artifacts, not module names alone.

## Security Considerations

- **Use an actual security boundary for secrets.** Android Keystore can protect supported cryptographic key material; it does not protect arbitrary application buffers from every side channel.
- **Visibility helps prevent accidental misuse.** `internal`, R8 and module layout do not provide authorization or isolation against code executing in the same process. Enforce sensitive operations at the trusted boundary.
- **Scan the release inputs.** Feature folders can aid ownership, but secret scanning must cover the whole build and its dependencies; there is no intrinsic reliability gain from module count.

## Observability

- **Build evidence.** Measure per-task configuration/execution, cache hits and critical paths before changing module boundaries.
- **Runtime evidence.** Inspect cache/memory counters where supported and interpret them with CPU utilization and instructions/cycles. Memory stalls tend to increase cycles per instruction; low CPI alone is not proof of cache thrashing.
- **Compose evidence.** Android Studio Layout Inspector reports recomposition and skip counts. Combine those with traces and frame timing; counts alone do not establish user-visible cost.

## Staff Engineer Thinking

**Choose the dominant change axis and organize around it.** For most apps, that axis is *feature*, not *layer*. Layers exist within features, not the other way around.

**Treat `:core:` as a tool of restraint.** A shared module should be small, stable, and explicitly cohesive. When `:core:` starts depending on `:feature:*`, it has become a god module. Refactor before adding more.

**Default Compose state to the smallest scope that works.** Hoist only when a sibling component genuinely needs to read or change the state. Premature hoisting creates broad recomposition.

**Apply data-oriented design selectively.** For ML, video, audio, image, ray-tracing, animation — yes, lay out data contiguously and accept the abstraction cost. For business logic — no, write the clean abstraction.

**Treat module boundaries as API design.** What you `public` from a module is your commitment to other modules. Keep it small and intentional. `internal` is the default; promote only on demand.

**Locality and Demeter reinforce each other.** Things that talk frequently should live near each other. The Law of Demeter says don't reach far; locality says don't make far reaches necessary in the first place.

**Optimize build locality with caching and parallelism.** Gradle build/configuration caches and suitable parallel task execution can help eligible builds. Benchmark JVM/GC settings and graph changes on representative clean and incremental workloads.

---

## Common Misconceptions

**"Locality is only for low-level performance code."** No — code organization is also locality. Package-by-feature is locality applied to humans.

**"More modules means better locality."** Configuration overhead can outweigh isolation benefits; the crossover depends on the project and build tooling, not a universal 50-module threshold. Locality serves you, not the other way around.

**"Hoisting all state to the top is good for testability."** It's good for *one kind* of testability (end-to-end); it's bad for locality and bad for recomposition cost. Hoist only as much as needed.

**"Object-oriented design contradicts data-oriented locality."** They serve different goals. OO is for *change management*; DOD is for *performance*. Most code is OO; hot paths can be DOD; use both as fits.

**"`IntArray` and `List<Int>` are interchangeable."** They are not — `List<Int>` is an interface with multiple implementations; JVM generic storage normally involves boxed values, which can be cached or optimized. For large primitive collections, the difference can be significant; measure it.

**"Modularization is just for build time."** Build time is the *easiest-to-measure* benefit. The bigger benefit is cognitive locality and enforced boundaries.

---

## Probing Questions

1. Why can summing an `IntArray` be cheaper than summing a `List<Int>` on Android, and why must the difference be measured?
2. What's the difference between temporal and spatial locality? Give a code example of each.
3. Why does `data class Pixel(val r: Int, val g: Int, val b: Int)` in an `Array<Pixel>` have worse cache behavior than three `IntArray` columns?
4. A Compose `var state by remember { mutableStateOf(0) }` lives at the top of an app. The state changes on every keystroke from a deeply-nested TextField. What happens, and how do you fix it?
5. What's the rationale for package-by-feature over package-by-layer in a large Android codebase?
6. When does the Common Closure Principle conflict with the Single Responsibility Principle? How do you decide?
7. Your `:core:` module has 18 sub-packages and depends on three feature modules. What's wrong, and how do you untangle it?
8. SQLite uses configurable pages and overflow pages for large payloads. How does row width affect query locality? Why might splitting a table into "hot fields" and "cold blob" tables help?
9. A Gradle build with 100 small modules is slower than the same code in 10 large modules. What's the failure mode, and where's the sweet spot?
10. You profile an Android app and see L1 cache misses dominating CPU time in a render loop. What questions do you ask about data layout?

---

## Answer Key

1. **Why can summing an `IntArray` be cheaper than summing a `List<Int>` on Android, and why must the difference be measured?**
   `IntArray` stores primitive ints contiguously in memory, allowing the CPU cache to fetch multiple values per read. `List<Int>` has multiple implementations; JVM generic collections typically use boxed values and references. Allocation reuse, runtime optimization, working-set size and access pattern determine the actual cost, so no fixed multiplier or miss per item follows.
2. **What's the difference between temporal and spatial locality? Give a code example of each.**
   Temporal locality means accessing the same item again soon (e.g., a loop counter). Spatial locality means accessing nearby items soon (e.g., iterating sequentially through an array).
3. **Why does `data class Pixel(val r: Int, val g: Int, val b: Int)` in an `Array<Pixel>` have worse cache behavior than three `IntArray` columns?**
   `Array<Pixel>` scatters `Pixel` objects in the heap and includes object header overhead, requiring pointer chasing. Three `IntArray`s (SoA) lay out the R, G, and B components contiguously, maximizing cache line utilization during sequential processing.
4. **A Compose `var state by remember { mutableStateOf(0) }` lives at the top of an app. The state changes on every keystroke from a deeply-nested TextField. What happens, and how do you fix it?**
   A changed value invalidates the composition scopes that read it, with unchanged children potentially skipped. To fix it, hoist the state down to the closest common ancestor of its readers, or keep it inside the `TextField` composable if it's purely local UI state.
5. **What's the rationale for package-by-feature over package-by-layer in a large Android codebase?**
   Package-by-feature co-locates related UI, data, and domain logic, reducing cognitive overhead (jumping between folders) and aligning the module structure with how business requirements actually change, unlike package-by-layer which scatters feature logic.
6. **When does the Common Closure Principle conflict with the Single Responsibility Principle? How do you decide?**
   The Common Closure Principle groups things that change together, while the Single Responsibility Principle separates things that change for different reasons. You balance them by grouping code by business stakeholder (feature), but separating distinct technical concerns within that boundary.
7. **Your `:core:` module has 18 sub-packages and depends on three feature modules. What's wrong, and how do you untangle it?**
   A core-to-feature dependency may reverse the intended layering, but is a cycle only if a path leads back to core. Package count alone does not establish low cohesion. It should be split into smaller, focused modules (e.g., `:core:network`, `:core:design`) based on distinct technical axes to prevent widespread rebuilds.
8. **SQLite uses configurable pages and overflow pages for large payloads. How does row width affect query locality? Why might splitting a table into "hot fields" and "cold blob" tables help?**
   Page size is configurable, and large payloads can occupy overflow pages. Separating rarely accessed BLOBs can make hot records denser, but projections, covering indexes and access patterns affect what is read. Inspect the schema and query plan and benchmark the workload.
9. **A Gradle build with 100 small modules is slower than the same code in 10 large modules. What's the failure mode, and where's the sweet spot?**
   The failure mode is Gradle configuration overhead, which grows with module count and can dominate build times. The sweet spot balances build caching/parallelism benefits against configuration cost, typically avoiding micro-modules that contain only a few classes.
10. **You profile an Android app and see L1 cache misses dominating CPU time in a render loop. What questions do you ask about data layout?**
    Is the data laid out contiguously? Are we iterating over an array of object references instead of primitives? Can we switch from an Array of Structs (AoS) to a Struct of Arrays (SoA) for this hot loop?

## Further Reading

In this repository:

- [`simplicity.md`](simplicity.md) — locality is one form of structural simplicity.
- [`coupling-vs-cohesion.md`](../engineering-fundamentals/coupling-vs-cohesion.md) — common-closure is high cohesion at the package level.
- [`single-responsibility.md`](single-responsibility.md) — SRP at file level; locality at module level.
- [`../engineering-fundamentals/caching.md`](../engineering-fundamentals/caching.md) — temporal locality is the foundation of all caches.
- [`../android/compose/recomposition-and-state.md`](../android/compose/recomposition-and-state.md) — state locality and recomposition scopes.
- [`../android/build-tooling/gradle-and-build-systems.md`](../android/build-tooling/gradle-and-build-systems.md) — module boundaries and build performance.

External:

- Peter Denning, *"The Working Set Model for Program Behavior"* (1968) — original formalization of program locality.
- Robert C. Martin, *"Granularity"* and *"The Common Closure Principle"* (1996) — the architectural framing.
- Mike Acton, *"Data-Oriented Design and C++"* (CppCon 2014, YouTube) — the canonical talk on cache-friendly layout.
- Ulrich Drepper, *"What Every Programmer Should Know About Memory"* (2007) — exhaustive treatment of memory hierarchies.
- Google Android Developers, *"Guide to App Architecture"* (developer.android.com) — package-by-feature recommendations.
- Joaquim Verges, *"Now in Android: Multi-module architecture"* — official Google sample exemplifying feature modules.
- [Denning: working-set model (original paper)](https://denninginstitute.com/pjd/PUBS/WSModel_1968.pdf)
- [SQLite file format and overflow pages](https://www.sqlite.org/fileformat.html)
- [Kotlin primitive arrays](https://kotlinlang.org/docs/arrays.html)
- [Compose read phases](https://developer.android.com/develop/ui/compose/phases)
- [Compose strong skipping](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping)
- [Compose Layout Inspector](https://developer.android.com/develop/ui/compose/tooling/debug)
- [Gradle build performance](https://docs.gradle.org/current/userguide/performance.html)
- [Android modularization patterns](https://developer.android.com/topic/modularization/patterns)

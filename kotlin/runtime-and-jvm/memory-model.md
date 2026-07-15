# The Memory Model (JVM, ART, and Android Leaks)

> Memory is the most expensive resource in Android. The Garbage Collector is *not* magic — every wasted allocation buys you back jank and OOM crashes. Staff-level mastery means you can reason about the Stack vs the Heap, predict when boxing happens, know the four reference strengths (strong/weak/soft/phantom), recognize the six classic Android leak patterns by sight, and use LeakCanary + the Memory Profiler to find leaks that don't reproduce locally.

---

## Overview

The JVM (and Android's ART runtime) split memory into:

- **Stack** — per-thread, fast, automatic cleanup. Holds primitives and references.
- **Heap** — shared, slower, garbage-collected. Holds all objects.
- **Native heap** — outside the JVM, used by C/C++ code (Bitmaps, OpenGL surfaces, FFmpeg, etc.).

Where your code allocates determines whether the user sees a smooth UI or a stutter. Where references *outlive* their intended owner determines whether the app leaks until OOM.

---

## Why It Matters (Android Context)

- A 16ms frame budget (60Hz) — any GC pause longer than ~10ms drops a frame.
- An Activity reference held past `onDestroy` keeps the whole view hierarchy alive — easily 5–50 MB per leak.
- Android limits app heap (e.g., 256 MB on many devices). OOM crashes are a real production failure mode.
- The single biggest Crashlytics bucket for many apps after NPE is `OutOfMemoryError`.

Memory bugs ship invisible. The user sees a "weird app that gets slow over time." You see it in the crash dashboard a quarter later.

---

## First Principles

1. **Stack memory is free** — allocated on function entry, gone on function return.
2. **Heap memory costs** — allocation + bookkeeping + eventual GC.
3. **Generic types are erased** → `List<Int>` boxes every `Int` to `java.lang.Integer` on the heap.
4. **Reachable from a GC root = alive.** No matter how indirectly.
5. **Lifecycle longer than yours = leak source.** A static field outlives any Activity that touches it.

---

## Stack vs Heap

```kotlin
fun computeArea() {
    val width: Int = 10        // STACK (JVM primitive `int`)
    val height: Int = 20       // STACK
    val name: String = "Box"   // STACK holds the *reference*; HEAP holds the String
    val area = width * height  // STACK (primitive arithmetic)
}
```

- **Local primitives** (like variables in a function) may live on the stack or in registers. Non-null primitives *inside objects* live on the heap as part of their parent object.
- **All object references** live on the stack or in registers; the actual objects they point to live on the heap.
- **Closures** that capture a `var` cause that variable to live on the heap (so it can outlive the call).

### Boxing — the silent perf killer

The JVM has eight primitive types (`int`, `long`, etc.). Anything else — including any nullable primitive (`Int?`) and any generic (`List<Int>`) — must be a heap object:

```kotlin
val a: Int = 30        // primitive `int` — stack
val b: Int? = 30       // boxed `java.lang.Integer` — heap
val c: List<Int> = listOf(1, 2, 3)   // each Int boxed into Integer — heap × 3
val d: IntArray = intArrayOf(1, 2, 3)   // raw int[] — single heap allocation
```

For perf-critical code, prefer `IntArray` / `LongArray` / `FloatArray` over `List<Int>` / `List<Long>` / `List<Float>`. The difference is huge: a `List<Int>` of 100k items is **100k+1** heap objects; an `IntArray` of 100k items is **1** heap object holding contiguous ints.

### Escape analysis

Optimizing compilers can sometimes eliminate an allocation entirely — if the compiler proves the object never escapes the method, it can replace the object with its fields and never touch the heap:

```kotlin
fun area(): Int {
    val box = Rect(0, 0, 10, 20)   // looks like a heap allocation
    return box.width * box.height   // ...but the compiler may eliminate it entirely
}
```

The mechanism differs by runtime, and the difference matters on Android:

- **HotSpot (server JVM)** does aggressive escape analysis with scalar replacement in the C2 JIT — this is the behavior most JVM blog posts describe.
- **ART** (both JIT and AOT `dex2oat`) has its own escape analysis (`compiler/optimizing/escape.cc`), used by the load-store-elimination pass to remove allocations of non-escaping "singleton" objects and to sink partially-escaping allocations closer to their escape points. It is real, but considerably more conservative than HotSpot's — an object that is stored to the heap, passed to another method, or returned is never eliminated.

Either way the engineering conclusion is the same: **you can't rely on escape analysis** — write code that doesn't allocate in hot paths, and don't expect the compiler to bail you out. Verify with the Memory Profiler / allocation tracking, not with assumptions about what the JIT "should" do.

---

## Reference Strengths (the Four Kinds)

The Garbage Collector reclaims any object **not reachable from a GC root**. A "GC root" is something whose lifetime exceeds any normal object — static fields, thread stacks, JNI references, the application class.

How an object becomes reachable matters. There are four reference strengths:

| Reference | Prevents GC? | Use case |
|---|---|---|
| **Strong** (default `val x = Foo()`) | Yes | Normal references |
| **Soft** (`SoftReference<T>`) | Until memory pressure | In-memory caches that can be regenerated |
| **Weak** (`WeakReference<T>`) | No (cleared on next GC) | Listener back-references, observers, caches keyed by lifecycle |
| **Phantom** (`PhantomReference<T>`) | No (cleared even before finalize) | Native-resource cleanup hooks |

### Strong references — the default trap

```kotlin
class Singleton private constructor() {
    var currentActivity: Activity? = null    // ← strong reference

    companion object {
        val instance = Singleton()
    }
}
```

If you ever do `Singleton.instance.currentActivity = this` inside `Activity.onCreate`, the singleton (alive for the app's lifetime) holds the activity forever. The activity can't be GC'd. The activity holds its entire view tree. The view tree holds Bitmaps. You leak megabytes per screen.

### Weak references — break the chain

```kotlin
class AnalyticsBus {
    private val listeners = mutableListOf<WeakReference<Listener>>()

    fun register(listener: Listener) {
        listeners.add(WeakReference(listener))
    }

    fun fire(event: Event) {
        listeners.forEach { it.get()?.onEvent(event) }
        listeners.removeAll { it.get() == null }   // drop dead entries
    }
}
```

The bus doesn't keep listeners alive. When the activity dies, the GC reclaims it; the bus's WeakReference becomes `null`. No leak.

### Soft references — caching with backpressure

```kotlin
class BitmapCache {
    private val cache = mutableMapOf<String, SoftReference<Bitmap>>()

    fun get(key: String): Bitmap? = cache[key]?.get()
    fun put(key: String, bmp: Bitmap) { cache[key] = SoftReference(bmp) }
}
```

The bitmap stays cached until memory pressure forces the GC to reclaim soft-reachable objects. Better than holding strong references and risking OOM; worse than a proper LRU cache with explicit eviction policies.

In modern Android, **`LruCache`** (with hard size limits in bytes) is generally preferred over soft-reference caching — it's more predictable.

### Phantom references — finalize replacement

Mostly seen in framework code (Coil, Glide, FFmpeg bindings) that needs to know when a Java object is collected so it can release a native resource. Rarely written by app developers.

---

## Android's GC: ART vs Dalvik

| Dalvik (pre-Android 5) | ART (Android 5+) |
|---|---|
| Just-in-time only | AOT (5/6) -> AOT + JIT PGO (7+) |
| Mark-and-sweep GC | Concurrent generational GC (Android 8+) |
| Long stop-the-world pauses (~50ms+) | Sub-5ms pauses typically |
| ~1ms allocation cost | ~100ns allocation cost (TLAB) |
| No Large Object Space | Separate LOS for Bitmaps |

ART introduced **generational GC** — most objects die young (short-lived locals), so the GC sweeps a small "young generation" frequently and the long-lived "old generation" rarely. Bitmaps go to a separate Large Object Space.

What this means for your code:

- **Allocations are cheap in modern ART.** Don't micro-optimize away every `String` concatenation.
- **GC pauses are short** but still measurable. A burst of allocations during a list scroll can stack pauses and drop frames.
- **Bitmaps still hurt.** They're large, often go to LOS, and frequently allocated to native heap (`Bitmap.Config.HARDWARE`) where the GC can't see them at all.

---

## The Six Classic Android Leak Patterns

### 1. Static field holding an Activity / Context

```kotlin
object Logger {
    var context: Context? = null   // ← if assigned an Activity, leak forever
}

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Logger.context = this   // LEAK
    }
}
```

**Fix:** use `applicationContext` for app-lifetime storage, or hold a `WeakReference`.

### 2. Non-static inner class / lambda capturing the outer

```kotlin
class MainActivity : AppCompatActivity() {
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handler.postDelayed({
            updateUi()   // ← lambda captures `this` (the Activity)
        }, 60_000)
    }
}
```

If the user leaves the screen before 60 seconds, the runnable still holds the activity until the message fires.

**Fix:**
```kotlin
override fun onDestroy() {
    handler.removeCallbacksAndMessages(null)
    super.onDestroy()
}
```

Or better: use `viewModelScope.launch` with `delay(60_000)`, which auto-cancels.

### 3. Listener registered, never unregistered

```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    locationManager.requestLocationUpdates(provider, 1000L, 1f, this)
}
// ← if no onPause/onDestroy unregister, the manager holds the Activity
```

**Fix:** pair every `register` with `unregister` in the matching lifecycle callback. Better: use a `DefaultLifecycleObserver` and register/unregister automatically.

### 4. Coroutine escaping the lifecycle

```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        GlobalScope.launch {       // ← lives as long as the app process
            delay(10_000)
            updateUi()              // captures `this`
        }
    }
}
```

**Fix:** always use `lifecycleScope` / `viewModelScope` / `repeatOnLifecycle`. See [`coroutines.md`](../coroutines-and-flow/coroutines.md).

### 5. Holding a View past `onDestroyView`

```kotlin
class CartFragment : Fragment() {
    private lateinit var binding: FragmentCartBinding

    override fun onCreateView(/*...*/): View {
        binding = FragmentCartBinding.inflate(/*...*/)
        return binding.root
    }
    // ← onDestroyView fires; `binding` still holds every view
}
```

**Fix:** the `_binding` lifecycle pattern from [`null-safety.md`](../language-core/null-safety.md):
```kotlin
private var _binding: FragmentCartBinding? = null
private val binding get() = _binding!!

override fun onDestroyView() {
    _binding = null
    super.onDestroyView()
}
```

### 6. Singleton DI / Service holding a screen-scoped object

```kotlin
@Singleton
class Analytics @Inject constructor() {
    var currentScreen: Screen? = null   // injected from Activity each time
}
```

A `@Singleton` Hilt component lives as long as the process. Storing screen-scoped state inside is a leak by definition. Use a scoped component (`@ActivityScoped`, `@ViewModelScoped`) or `WeakReference`.

---

## Bitmap Memory — The Special Case

A 4K image (3840 × 2160) at `ARGB_8888` is **33.2 MB** in memory regardless of file size. Six full-screen photos = your heap is gone.

```kotlin
val opts = BitmapFactory.Options().apply { inSampleSize = 4 }   // downsample 4×
val bmp = BitmapFactory.decodeResource(resources, R.drawable.huge, opts)
```

In modern Android:

- Use **Coil 3** / **Glide 4+** — they handle downsampling, off-heap, LRU, and lifecycle integration.
- Pass `Bitmap.Config.HARDWARE` where possible — stored in graphics memory, not Java heap. Caveat: can't be read back to a `Pixel[]`.
- `BitmapDrawable` caching — only if you know the bitmap size and have a memory budget.

For large image lists (RecyclerView, LazyColumn): never load full-size bitmaps; always use a sampling decoder.

---

## Detecting Leaks: LeakCanary + Memory Profiler

### LeakCanary

```kotlin
// app/build.gradle.kts
debugImplementation("com.squareup.leakcanary:leakcanary-android:2.13")
```

That's it. LeakCanary installs as a `ContentProvider`, watches every `Activity` and `Fragment` for `onDestroy`, waits a few seconds, forces a GC, then checks if the destroyed object is still reachable. If yes, it dumps the heap, walks the reference chain to the GC root, and shows you exactly which field points where.

A typical LeakCanary report:

```
┬───
│ GC Root: System class
│
├─ android.app.ActivityThread instance
│    Leaking: NO (a singleton)
│    ↓ ActivityThread.mActivities
├─ android.util.ArrayMap instance
│    ↓ ArrayMap[1]
├─ android.app.LocalActivityManager$LocalActivityRecord instance
│    ↓ LocalActivityRecord.activity
├─ com.yourapp.MainActivity instance
│      Leaking: YES (Activity#mDestroyed is true and ObjectWatcher was watching this)
```

Read the chain bottom-up: "MainActivity is held by LocalActivityRecord, which is in an ArrayMap, which is in ActivityThread, which is a GC root." Trace each hop to find which of *your* references caused it.

### Android Studio Memory Profiler

For leaks LeakCanary misses (non-Activity/Fragment leaks), or for OOM debugging:

1. Run the app, open Profiler, attach the Memory tab.
2. Reproduce the scenario several times (open screen → close → repeat 5x).
3. Click "Force GC" → "Capture heap dump."
4. Filter by your app's package.
5. Sort by "Allocations" — anything with 5+ instances after a Force GC of a screen-scoped class is a leak.
6. Click the instance → Reference tab → walk up to a GC root.

---

## Java Memory Model — Multithreading Semantics

The JMM defines what one thread sees of another thread's writes. Critical primitives:

| Primitive | Effect |
|---|---|
| `@Volatile` | Reads/writes have happens-before semantics across threads; no caching in CPU registers |
| `synchronized` / `Mutex.withLock` | Mutual exclusion + memory barrier |
| `AtomicReference` / `AtomicInteger` | Lock-free atomic ops + memory barrier |
| `final` fields | Safely published after constructor completes |

### Double-checked locking (the canonical idiom)

```kotlin
class Manager private constructor() {
    companion object {
        @Volatile private var INSTANCE: Manager? = null

        fun get(): Manager = INSTANCE ?: synchronized(this) {
            INSTANCE ?: Manager().also { INSTANCE = it }
        }
    }
}
```

`@Volatile` is non-negotiable. Without it, one thread can see `INSTANCE != null` but the object's fields not yet initialized (instruction reordering). Welcome to two days of "impossible" bugs.

In Kotlin, prefer `lazy(LazyThreadSafetyMode.SYNCHRONIZED)` over hand-rolled double-checked locking — same semantics, less ceremony.

### `volatile` on Android in 2025

Most application code should not need `@Volatile` directly. Coroutines + StateFlow give you correctness without writing your own threading. Reach for `@Volatile` only when working at framework / SDK level (custom thread pools, low-level event buses, native callbacks).

---

## OOM and the Heap Limit

Android limits app heap per device (typically 192–512 MB). Hitting it = `OutOfMemoryError` = app crash.

Common OOM patterns:

| Pattern | Why | Fix |
|---|---|---|
| Loading large bitmap full-size | 1 image = 30 MB+ | Downsample, use image loader |
| Infinite list in memory | Holds every item ever scrolled | Paging 3 + Room |
| String concatenation in tight loop | Every `+` allocates a new String | `StringBuilder` |
| Boxing in numeric loops | Every iteration boxes | Primitive arrays |
| Unbounded cache | No size limit | `LruCache(maxSizeBytes)` |
| Singletons retaining Bitmaps | Process-lifetime hold | Pass Application context only; clear on `onTrimMemory` |
| Static field accumulating per-call | List grows unboundedly | Use `WeakHashMap` or explicit clear |
| Leaked Activity × N | Each leak holds 5–50 MB | LeakCanary; fix root cause |

`Runtime.getRuntime().maxMemory()` reports the limit. `Debug.MemoryInfo` reports current usage. Production apps should listen to `onTrimMemory()` and shed caches.

---

## Native Memory and JNI

Some objects live outside the JVM heap:

- **Bitmaps with `Config.HARDWARE`** — in GPU memory.
- **`ByteBuffer.allocateDirect(N)`** — native heap.
- **NDK code** allocations.
- **Cursor and SQLite handles** — kernel resources.

The GC can't see these. Leaking them shows up as "the app uses 800 MB according to RSS but only 80 MB heap." Profile with the **Native Memory Profiler** (Android Studio) or `dumpsys meminfo <pkg>`.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Frame drop during list scroll | Allocation in `onBindViewHolder` | Pre-allocate; reuse Paint/Path |
| Slow over time, eventually OOM | Activity leak | LeakCanary → fix reference chain |
| Crash: `java.lang.OutOfMemoryError` on photo screen | Loading full-size bitmap | Downsample + Coil/Glide |
| App uses 300 MB but heap shows 50 MB | Native memory leak | Native profiler; check Bitmap.Config, JNI |
| Singleton retains Activity | Static field assignment | Application context or WeakReference |
| Coroutine leak | GlobalScope used | Always lifecycle scopes |
| Inner class lambda holds outer | Non-static or capturing reference | Lifecycle observer / `removeCallbacks` in onDestroy |
| ViewBinding NPE in Fragment | View destroyed but binding retained | `_binding = null` in onDestroyView |
| Two `Toast` displays leak Activity | Pre-API 30 Toast view holds Context | `Toast.makeText(applicationContext, …)` |
| LeakCanary points at framework class | False positive (or framework leak) | Sometimes it's a known platform issue; check leakcanary-known-leaks |
| Mystery slowness only on user devices | Production GC patterns differ | Add memory profiler in QA builds; ship Crashlytics OOM tracking |
| Bitmap cache evicts too aggressively | Soft references too loose | Switch to `LruCache` with explicit byte budget |

---

## Staff Engineer Lens

When reviewing for memory:

1. **Hunt static state.** Any `companion object var` holding a `Context`, `Activity`, `View`, `Fragment`, `Callback`, or `Listener` is a leak unless wrapped in WeakReference.
2. **`onDestroy` pairing.** Every `register*` / `addCallback` / `subscribe` needs a matching unregister. Lifecycle observers automate this; favor them.
3. **`GlobalScope.launch` and `Thread { }`** — never approved without justification.
4. **List-of-primitives in hot paths.** `List<Int>` for an audio buffer is a junior mistake. `IntArray`.
5. **`onDraw` allocations.** Any `new` / constructor call inside a draw or layout pass is a hard reject. Pre-allocate, reuse.
6. **Singletons holding scoped state.** `@Singleton Analytics.currentScreen` is a leak by construction. Use `@ActivityScoped` or `WeakReference`.
7. **Bitmap handling.** Direct `BitmapFactory.decodeResource` in app code is a smell — always go through Coil/Glide.
8. **No `onTrimMemory` handler.** A serious app should release caches on system memory pressure.
9. **No LeakCanary in debug.** Add it. Free leak detection.
10. **OOM Crashlytics signal ignored.** Set up a Crashlytics OOM panel; track week-over-week.

---

## Common Misconceptions

- **"GC is fast, allocations don't matter."** Modern ART is fast but not free. Burst allocations stack pauses; jank is the result.
- **"Kotlin `Int` is always a primitive."** False. `Int?`, `List<Int>`, `Int` returned from a generic function — all box.
- **"WeakReference solves all leaks."** No. Leaks live deeper — a strong reference somewhere holds the chain.
- **"`System.gc()` will fix my leak."** No. Force-GC reproduces the bug; it doesn't fix the reference chain. Real leak = something points where it shouldn't.
- **"OOM means out of memory."** Not exactly — Android limits app heap; you can OOM with the device having 4GB free.
- **"Bitmaps are in the Java heap."** Pre-Oreo: yes. Post-Oreo: native heap by default (Glide/Coil exploit this).
- **"The Memory Profiler shows everything."** It shows the Java/Kotlin heap. Native memory needs the Native Memory Profiler. NDK code needs different tooling entirely.

---

## Probing Questions

1. Walk through what happens at the JVM level when you write `val x: Int? = 5`. Where does `5` live?
2. `List<Int>` of 100,000 items vs `IntArray` of 100,000 items — concretely, what's the memory footprint difference?
3. Explain the four reference strengths. Give one real Android use case for each (except phantom).
4. A user reports the app "slowly gets sluggish over the day, then crashes." Walk through your first 30 minutes of investigation.
5. LeakCanary points to MainActivity held by `ActivityThread.mActivities → ArrayMap → LocalActivityRecord`. How do you decide whether to fix it or mark as platform bug?
6. Why is `BitmapFactory.decodeResource(huge_image)` dangerous? What's the safer pattern?
7. Walk through a textbook double-checked locking singleton. Why does `@Volatile` matter?
8. Singleton DI vs activity-scoped DI — why does scope matter for memory?
9. `GlobalScope.launch` vs `viewModelScope.launch` — what's the memory difference?
10. A Fragment's `View` is destroyed in `onDestroyView` but the Fragment isn't. Why is `_binding = null` necessary?
11. ART generational GC: explain "young generation" vs "old generation" and what it means for your code.
12. Bitmap with `Config.HARDWARE` — what changes in memory tracking, and what's the trade-off?
13. You see the app use 600 MB RSS but only 80 MB Java heap. Where's the missing memory and how do you find it?

---

## Further Reading

- [`coroutines.md`](../coroutines-and-flow/coroutines.md) — structured concurrency as leak prevention.
- [`null-safety.md`](../language-core/null-safety.md) — `_binding = null` lifecycle pattern.
- [`delegation.md`](../language-core/delegation.md) — `by lazy` semantics + thread-safe modes.
- [`inline-functions.md`](../compiler-features/inline-functions.md) — preventing Lambda heap allocations.
- [`../android/performance/memory-management-and-leaks.md`](../../android/performance/memory-management-and-leaks.md) — Android-specific leak catalog.
- [`../android/concurrency/synchronization-and-mutex.md`](../../android/concurrency/synchronization-and-mutex.md) — JMM concurrency primitives.
- [`../android/os-internals/art-and-dalvik.md`](../../android/os-internals/art-and-dalvik.md) — ART runtime internals.
- [Android Developers — Manage your app's memory](https://developer.android.com/topic/performance/memory) — official guide.
- [LeakCanary docs](https://square.github.io/leakcanary/) — the tool every Android app should ship.
- [Pierre-Yves Ricau — "A small leak will sink a great ship"](https://medium.com/square-corner-blog/) — LeakCanary author's deep-dive.
- [JEP 197 — Segmented Code Cache](https://openjdk.org/jeps/197) — JIT / generational GC background.
- [Romain Guy — "Memory and tracing"](https://www.curious-creature.com/) — long-time Android graphics engineer's profiling notes.

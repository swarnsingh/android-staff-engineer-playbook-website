# Arrays and Strings

## Overview

Arrays and strings are the most basic data structures, but they are also where many mobile performance bugs start. An array gives you indexed access to contiguous memory. A string gives you immutable text, usually backed by an array-like sequence of code units. Together they power JSON parsing, protobuf buffers, image byte streams, search boxes, RecyclerView lists, Compose state lists, analytics payloads, and almost every interview problem.

Staff-level understanding is not "know two pointers." It is knowing how representation affects CPU cache locality, allocation rate, Unicode correctness, API contracts, and the difference between a cheap linear scan and an accidental main-thread ANR.

---

## Why It Matters

Android devices are constrained by frame deadlines, heap limits, and battery. Arrays and strings sit on the hot path:

1. **UI lists are arrays in disguise.** `List<T>` in Kotlin is commonly backed by `ArrayList<T>`. Diffing, sorting, filtering, and paging all operate over indexed sequences.
2. **Text is not simple.** Kotlin `Char` is a UTF-16 code unit, not a user-visible character. Emoji, accents, Indic scripts, and flags can occupy multiple code units.
3. **Allocations are visible.** Chaining `filter`, `map`, and `sorted` can allocate several intermediate collections. In a scroll path, that becomes GC pressure and jank.
4. **Parsing is linear until you make it quadratic.** Repeated substring creation, string concatenation in loops, or nested scans can turn O(n) input handling into O(n^2).

The Staff lens: arrays and strings are not "easy"; they are where low-level representation leaks into product quality.

---

## First Principles

### Arrays

An array stores elements in contiguous slots:

```text
index:  0   1   2   3   4
value: [A] [B] [C] [D] [E]
```

This gives:

- `get(index)`: O(1)
- `set(index)`: O(1)
- append to dynamic array: amortized O(1)
- insert/remove at front or middle: O(n), because elements shift
- scan: O(n)

Kotlin/Java distinctions matter:

| Type | Storage | Use |
|---|---|---|
| `Array<T>` | references to objects | Generic object arrays |
| `IntArray`, `LongArray`, `ByteArray` | primitive contiguous values | Numeric hot paths, bytes, media, crypto |
| `List<T>` | read-only interface, often `ArrayList` | API boundaries |
| `MutableList<T>` | mutable interface | Internal builders, rarely public API |

Prefer primitive arrays for large numeric data. `List<Int>` boxes each value into an object; `IntArray` stores raw ints.

### Strings

Kotlin `String` is immutable. Operations that appear to "modify" a string create new strings:

```kotlin
var s = ""
repeat(10_000) {
    s += "x"       // O(n^2) total: repeatedly copies previous content
}
```

Use `StringBuilder` for repeated appends:

```kotlin
val builder = StringBuilder()
repeat(10_000) {
    builder.append('x')
}
val result = builder.toString()
```

### Unicode Reality

This is a trap:

```kotlin
val text = "👨‍👩‍👧‍👦"
println(text.length)
```

The value is one visible family emoji, but `length` counts UTF-16 code units, not grapheme clusters. For product code involving cursor positions, truncation, display length, SMS limits, search normalization, or accessibility labels, use platform-aware text APIs rather than assuming `String.length` equals "characters the user sees."

---

## Core Patterns

### Two Pointers

Two pointers shrink or expand a search range without nested loops.

```kotlin
fun hasPairWithSum(sorted: IntArray, target: Int): Boolean {
    var left = 0
    var right = sorted.lastIndex

    while (left < right) {
        val sum = sorted[left] + sorted[right]
        when {
            sum == target -> return true
            sum < target -> left++
            else -> right--
        }
    }
    return false
}
```

Use when the input is sorted or can be processed from both ends: pair sums, palindrome checks, merging, partitioning, and in-place compaction.

### Sliding Window

Sliding window maintains a contiguous range and updates it incrementally.

```kotlin
fun longestSubstringWithoutRepeats(s: String): Int {
    val lastSeen = mutableMapOf<Char, Int>()
    var start = 0
    var best = 0

    for (end in s.indices) {
        val c = s[end]
        val previous = lastSeen[c]
        if (previous != null && previous >= start) {
            start = previous + 1
        }
        lastSeen[c] = end
        best = maxOf(best, end - start + 1)
    }
    return best
}
```

Use for "longest/shortest contiguous segment" problems: search throttling windows, analytics burst detection, rate-limit buckets, and text scanning.

### Prefix Sums

Prefix sums precompute cumulative totals so range queries become O(1).

```kotlin
class PrefixSum(values: IntArray) {
    private val prefix = LongArray(values.size + 1)

    init {
        for (i in values.indices) {
            prefix[i + 1] = prefix[i] + values[i]
        }
    }

    fun sumInclusive(left: Int, right: Int): Long {
        require(left <= right)
        return prefix[right + 1] - prefix[left]
    }
}
```

Use when many range queries hit immutable or rarely-changing data: chart windows, telemetry buckets, offline stats, and local report generation.

### Difference Arrays

When many range updates happen before final materialization, update only boundaries:

```kotlin
fun applyRangeAdds(size: Int, updates: List<Triple<Int, Int, Int>>): IntArray {
    val diff = IntArray(size + 1)
    for ((left, right, delta) in updates) {
        diff[left] += delta
        if (right + 1 < diff.size) diff[right + 1] -= delta
    }

    val result = IntArray(size)
    var running = 0
    for (i in 0 until size) {
        running += diff[i]
        result[i] = running
    }
    return result
}
```

Use for batched calendar availability, feature exposure windows, timeline overlays, and local simulation.

---

## Kotlin and Android Details

### `List` Is Not Deeply Immutable

```kotlin
data class UiState(val items: List<Item>)
```

This protects the reference type, not the underlying object. If `items` is backed by a mutable list and another owner mutates it, Compose may miss changes or recompose unpredictably.

Staff rule: expose `List<T>`, own mutation internally, and emit a new list instance when state changes.

```kotlin
private val items = mutableListOf<Item>()

fun add(item: Item): UiState {
    items += item
    return UiState(items.toList())
}
```

For high-volume immutable collections, consider persistent collections where available.

### Avoid Intermediate Lists in Hot Paths

```kotlin
val names = users
    .filter { it.active }
    .map { it.name }
    .sorted()
```

Readable, but each stage can allocate. Fine for small bounded lists; risky in tight UI loops or 50K-row sync processing. Options:

- Use sequences for lazy pipelines when the chain is long and data is large.
- Use a single loop for hot paths.
- Move heavy transformations off the main thread.
- Measure before "optimizing" readability away.

### Byte Arrays Are Protocol Boundaries

`ByteArray` appears in crypto, compression, image decoding, protobuf, file I/O, and network bodies. Treat it as mutable binary data:

- Do not expose internal `ByteArray` directly from immutable-looking models.
- Copy at trust boundaries if callers might mutate.
- Prefer streaming for large data instead of loading entire files into memory.
- Avoid logging raw bytes; they may contain secrets or PII.

### Strings and Locale

Never lowercase, uppercase, sort, or compare user-facing text without thinking about locale.

```kotlin
val normalized = input.lowercase(Locale.ROOT) // protocol keys, not user text
```

Use `Locale.ROOT` for protocol identifiers, cache keys, and case-insensitive internal matching. Use user locale/collation for user-facing sorting and search.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| ANR while filtering a list | O(n) or O(n log n) work on main thread over large input | Move to worker dispatcher; page; index |
| Jank during scroll | Allocating temporary lists/strings per frame | Precompute, memoize, use stable models |
| Wrong text truncation | Cutting by UTF-16 code units | Use text layout / grapheme-aware APIs |
| OOM parsing payload | Read entire response into `String` or `ByteArray` | Stream, page, set payload limits |
| Compose row does not update | Mutated same list instance | Emit new immutable state |
| Search misses accents/case | No normalization/collation policy | Normalize deliberately; test locales |

---

## Staff Engineer Thinking

1. **Ask for bounds.** Is the array 20 items or 2 million? Complexity only matters against real upper limits.
2. **Prefer boring data layouts.** Contiguous arrays are CPU-cache friendly and often beat pointer-heavy structures.
3. **Own mutability.** Public mutable collections create invisible coupling and state bugs.
4. **Treat text as international.** A string algorithm that works only for ASCII is not production-ready.
5. **Measure allocation, not only CPU.** On Android, GC churn can be more visible than arithmetic cost.

---

## Probing Questions

1. Why is `ArrayList.removeAt(0)` O(n)?
2. When would `IntArray` be materially better than `List<Int>`?
3. Why is string concatenation in a loop O(n^2)?
4. What does `String.length` count on the JVM?
5. How does sliding window turn a nested-loop problem into O(n)?
6. Why can mutating a list inside `UiState` break Compose updates?
7. How would you process a 500MB file without a 500MB `ByteArray`?
8. When is a simple O(n) scan better than a hash map?

## Further Reading

- [`../engineering-fundamentals/complexity-analysis.md`](../engineering-fundamentals/complexity-analysis.md)
- [`hashing.md`](hashing.md)
- [`../kotlin/runtime-and-jvm/memory-model.md`](../kotlin/runtime-and-jvm/memory-model.md)
- [`../mobile-system-design/typeahead-autocomplete-search.md`](../mobile-system-design/typeahead-autocomplete-search.md)

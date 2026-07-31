# Sorting and Searching

## Overview

Sorting and searching are the operations that turn raw collections into usable systems. Sorting imposes order. Searching finds a target inside that order. Every feed, search box, local database query, autocomplete, analytics dashboard, and cache eviction policy depends on these ideas.

At Staff level, the question is rarely "can you implement quicksort." It is "which ordering contract does this feature need, how large can the data get, where should the work run, and what invariants make the search correct?"

---

## Why It Matters

1. **Sorting can block frames.** Sorting 50K objects on the main thread is a product bug.
2. **Comparator bugs are production bugs.** Non-transitive comparators can produce inconsistent order or runtime failures.
3. **Binary search only works with invariants.** The data must be sorted according to the same comparator used by the search.
4. **Database indexes are search structures.** A Room query with an index is a search over a B-tree, not magic.
5. **User-facing text sorting is locale-sensitive.** Protocol order and human order are different.

---

## Sorting Basics

| Algorithm | Average | Worst | Stable | Notes |
|---|---:|---:|---|---|
| Insertion sort | O(n^2) | O(n^2) | Yes | Great for tiny/nearly sorted data |
| Merge sort | O(n log n) | O(n log n) | Yes | Uses O(n) extra space |
| Quick sort | O(n log n) | O(n^2) | No | Fast in practice with good pivots |
| Heap sort | O(n log n) | O(n log n) | No | O(1) extra space |
| Counting sort | O(n + k) | O(n + k) | Yes | When values are small bounded ints |
| Radix sort | O(d * (n + k)) | O(d * (n + k)) | Yes | Fixed-width integers/strings |

Kotlin/JVM usually delegates object sorting to JDK sorting implementations. The details vary by platform/version, so rely on the contract, not an implementation rumor. If stability matters, test it or use APIs that guarantee it for your target.

---

## Comparator Contracts

A comparator must be:

- **Antisymmetric:** if `a < b`, then `b > a`.
- **Transitive:** if `a < b` and `b < c`, then `a < c`.
- **Consistent enough for your collection:** equal comparison should match your dedupe/grouping expectations.

Bad:

```kotlin
val comparator = Comparator<User> { a, b ->
    if (a.isPremium) -1 else 1 // never returns 0; violates equality behavior
}
```

Better:

```kotlin
val comparator = compareByDescending<User> { it.isPremium }
    .thenBy { it.lastActiveAtMillis }
    .thenBy { it.id }
```

Always add deterministic tie-breakers for feeds, tests, and pagination.

---

## Binary Search

Binary search halves the search space each step:

```kotlin
fun lowerBound(values: IntArray, target: Int): Int {
    var left = 0
    var right = values.size

    while (left < right) {
        val mid = left + (right - left) / 2
        if (values[mid] < target) {
            left = mid + 1
        } else {
            right = mid
        }
    }
    return left
}
```

`lowerBound` returns the first index whose value is `>= target`.

```kotlin
fun upperBound(values: IntArray, target: Int): Int {
    var left = 0
    var right = values.size

    while (left < right) {
        val mid = left + (right - left) / 2
        if (values[mid] <= target) {
            left = mid + 1
        } else {
            right = mid
        }
    }
    return left
}
```

`upperBound` returns the first index whose value is `> target`.

These two functions solve range counting:

```kotlin
fun countInRange(sorted: IntArray, min: Int, max: Int): Int {
    return upperBound(sorted, max) - lowerBound(sorted, min)
}
```

---

## Search Variants

### Linear Search

O(n), but often best for small bounded lists:

```kotlin
fun findSelected(tabs: List<Tab>): Tab? = tabs.firstOrNull { it.selected }
```

Do not build a hash map for 5 tabs.

### Hash Search

O(1) average lookup:

```kotlin
val byId = users.associateBy { it.id }
val user = byId[userId]
```

Use when you perform many lookups by key. Avoid rebuilding the map repeatedly in a hot path.

### Tree / Index Search

O(log n), ordered:

```sql
CREATE INDEX index_messages_conversation_time
ON messages(conversation_id, created_at);
```

Use when you need range queries, ordered scans, or prefix constraints.

### Full-Text Search

For text search, substring scanning does not scale. Use FTS indexes, tries, token indexes, or server-backed search depending on size and freshness.

---

## Android Examples

### Stable Feed Ordering

Feeds must be deterministic. If two items have the same score, add a tie-breaker:

```kotlin
val feedOrder = compareByDescending<Post> { it.score }
    .thenByDescending { it.createdAtMillis }
    .thenBy { it.id }
```

Without `id`, pagination can duplicate or skip items because the backend and client disagree on equal-score ordering.

### DiffUtil and Sorting

If you sort UI items differently between emissions, DiffUtil sees moves. Excessive moves cause jank and confusing animations. Make order explicit and stable.

### Search Suggestions

For local typeahead:

- Small list: linear scan with debounce is fine.
- Medium list: sorted list + binary prefix range.
- Large dictionary: trie or SQLite FTS.
- Remote data: server search + local cache + cancellation.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| ANR sorting large list | Main-thread O(n log n) | Sort off main; page; push to DB |
| Flaky order in tests | Missing tie-breaker | Add deterministic final key |
| Binary search misses item | Data sorted by different comparator | Use same comparator/invariant |
| Pagination duplicates | Non-stable order across pages | Add unique cursor/tie-breaker |
| Wrong user-facing order | ASCII compare for localized text | Use locale-aware collation |
| Rebuilding index repeatedly | `associateBy` inside loop/composition | Build once; memoize |

---

## Staff Engineer Thinking

1. **Sorting is a contract.** Write down the ordering rule and own tie-breakers.
2. **Move work to the data owner.** If SQLite can sort/filter with an index, do not load everything and sort in Kotlin.
3. **Know when O(n) is enough.** A linear scan over 12 items is clearer and faster than complex indexing.
4. **Binary search is an invariant test.** If the invariant is fuzzy, binary search is wrong.
5. **Locale is product behavior.** Sorting user names is not the same as sorting cache keys.

---

## Probing Questions

1. Why is binary search O(log n)?
2. What invariant must hold before using binary search?
3. Why do stable tie-breakers matter for pagination?
4. When would you prefer a linear scan over a hash map?
5. What makes a comparator invalid?
6. Why should large sorts avoid the main thread?
7. How does a SQLite index change search complexity?
8. Why is user-facing string sort different from protocol string sort?

## Answer Key

1. **Why is binary search O(log n)?**
   Because it halves the search space at each step, requiring at most log₂(n) comparisons to find the target or determine it doesn't exist.
2. **What invariant must hold before using binary search?**
   The array must be strictly sorted according to the exact same comparator that the binary search algorithm uses.
3. **Why do stable tie-breakers matter for pagination?**
   Without them, items with equal scores can shift positions arbitrarily between requests, causing missing or duplicated items across page boundaries.
4. **When would you prefer a linear scan over a hash map?**
   For very small datasets (e.g., 5-20 items) where the constant-factor overhead of allocating, hashing, and traversing a map outweighs a simple O(n) array traversal.
5. **What makes a comparator invalid?**
   If it violates antisymmetry or transitivity, or if it fails to return 0 for items that should be treated as equal by the collection's deduplication logic.
6. **Why should large sorts avoid the main thread?**
   Sorting large datasets takes significant CPU time, which blocks the main thread, drops frames, and causes Application Not Responding (ANR) errors.
7. **How does a SQLite index change search complexity?**
   It converts an O(n) full table scan into an O(log n) tree search (typically a B-tree).
8. **Why is user-facing string sort different from protocol string sort?**
   User-facing strings must respect locale-specific language and collation rules, whereas protocol strings usually require deterministic ASCII or root-locale ordering.

## Further Reading

- [`arrays-and-strings.md`](arrays-and-strings.md)
- [`trees.md`](trees.md)
- [`hashing.md`](hashing.md)
- [`../android/data-and-di/room.md`](../android/data-and-di/room.md)
- [`../mobile-system-design/search.md`](../mobile-system-design/search.md)

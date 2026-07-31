# Heaps and Priority Queues

## Overview

A **priority queue** returns the most important item first, not necessarily the oldest or newest. A **heap** is the usual data structure behind a priority queue. It keeps the minimum or maximum element at the root while allowing efficient insertion and removal.

Heaps show up in scheduling, top-K queries, timers, pathfinding, retry queues, merge pipelines, and "what should run next?" decisions. For Android engineers, the concept is everywhere: dispatchers, choreographers, image request priorities, cache eviction candidates, notification ranking, and background work scheduling.

---

## Why It Matters

Many systems are not FIFO. They need priority:

- Render visible images before off-screen images.
- Retry urgent sync before low-value telemetry.
- Keep the top 20 search suggestions without sorting all candidates.
- Pick the next shortest route candidate in Dijkstra/A*.
- Merge multiple sorted streams from disk/network/cache.

Sorting every time is often O(n log n) when a heap gives O(log n) updates and O(1) peek.

---

## First Principles

### Heap Property

In a min-heap, every parent is less than or equal to its children:

```text
          3
        /   \
       7     5
      / \   / \
     9  11 8  10
```

The smallest element is always at the root.

### Array Representation

Binary heaps are usually stored in arrays:

```text
index: 0  1  2  3   4  5   6
value: 3, 7, 5, 9, 11, 8, 10
```

For index `i`:

- left child: `2 * i + 1`
- right child: `2 * i + 2`
- parent: `(i - 1) / 2`

This avoids node allocations and keeps memory contiguous.

### Complexity

| Operation | Binary heap |
|---|---:|
| Peek min/max | O(1) |
| Insert | O(log n) |
| Remove min/max | O(log n) |
| Build heap from n items | O(n) |
| Remove arbitrary item | O(n) unless indexed |
| Search by value | O(n) |

The heap is optimized for the top item, not for arbitrary lookup.

---

## Kotlin PriorityQueue

```kotlin
import java.util.PriorityQueue

data class Task(
    val id: String,
    val priority: Int,
    val createdAtMillis: Long
)

val queue = PriorityQueue<Task>(
    compareByDescending<Task> { it.priority }
        .thenBy { it.createdAtMillis }
)

queue += Task("sync", priority = 10, createdAtMillis = 100)
queue += Task("analytics", priority = 1, createdAtMillis = 101)

val next = queue.poll() // highest priority, oldest within same priority
```

Important: Java/Kotlin `PriorityQueue` is not stable unless you add an explicit tiebreaker.

---

## Core Patterns

### Top K

Keep the top K items using a min-heap of size K:

```kotlin
fun topK(values: IntArray, k: Int): List<Int> {
    require(k >= 0)
    if (k == 0) return emptyList()

    val heap = PriorityQueue<Int>() // smallest of top K at root
    for (value in values) {
        if (heap.size < k) {
            heap += value
        } else if (value > heap.peek()) {
            heap.poll()
            heap += value
        }
    }
    return heap.toList().sortedDescending()
}
```

Complexity: O(n log k), better than sorting O(n log n) when k is small.

Use for search suggestions, largest files, top slow traces, top crash signatures, and leaderboard snippets.

### Merge K Sorted Lists

```kotlin
data class CursorItem(
    val value: Int,
    val listIndex: Int,
    val itemIndex: Int
)

fun mergeSorted(lists: List<List<Int>>): List<Int> {
    val heap = PriorityQueue<CursorItem>(compareBy { it.value })
    val result = mutableListOf<Int>()

    for (i in lists.indices) {
        if (lists[i].isNotEmpty()) {
            heap += CursorItem(lists[i][0], i, 0)
        }
    }

    while (heap.isNotEmpty()) {
        val item = heap.poll()
        result += item.value
        val nextIndex = item.itemIndex + 1
        val list = lists[item.listIndex]
        if (nextIndex < list.size) {
            heap += CursorItem(list[nextIndex], item.listIndex, nextIndex)
        }
    }
    return result
}
```

Use for merging paged local results, multiple sorted event streams, or sharded query responses.

### Dijkstra's Algorithm

Priority queue drives shortest-path exploration:

```kotlin
fun shortestPath(
    graph: Map<String, List<Pair<String, Int>>>,
    start: String
): Map<String, Int> {
    val dist = mutableMapOf<String, Int>().withDefault { Int.MAX_VALUE }
    val pq = PriorityQueue<Pair<String, Int>>(compareBy { it.second })

    dist[start] = 0
    pq += start to 0

    while (pq.isNotEmpty()) {
        val (node, current) = pq.poll()
        if (current != dist.getValue(node)) continue

        for ((next, weight) in graph[node].orEmpty()) {
            val candidate = current + weight
            if (candidate < dist.getValue(next)) {
                dist[next] = candidate
                pq += next to candidate
            }
        }
    }
    return dist
}
```

This lazy duplicate approach avoids needing decrease-key support, which Java `PriorityQueue` does not provide.

---

## Android Examples

### Image Loading Priority

Visible images should outrank prefetches:

```kotlin
enum class ImagePriority { VISIBLE, PREFETCH }

data class ImageRequest(
    val url: String,
    val priority: ImagePriority,
    val sequence: Long
)

val requests = PriorityQueue<ImageRequest>(
    compareBy<ImageRequest> { it.priority.ordinal }
        .thenBy { it.sequence }
)
```

But priority queues are not enough by themselves:

- Cancel requests for views that left the screen.
- Deduplicate by URL/cache key.
- Bound concurrency.
- Avoid priority inversion where a low-priority request holds a scarce resource.

### Retry Scheduling

Retry queues often sort by next eligible time:

```kotlin
data class RetryJob(
    val id: String,
    val nextRunAtMillis: Long,
    val attempt: Int
)

val retryQueue = PriorityQueue<RetryJob>(compareBy { it.nextRunAtMillis })
```

In production, persist this in a database. A heap in memory is a scheduling helper, not durable storage.

---

## Tradeoffs

| Structure | Strength | Weakness |
|---|---|---|
| Heap | Fast top item and updates | No fast arbitrary lookup |
| Sorted list | Fast iteration in order | Insert/remove O(n) |
| Balanced tree | Ordered lookup and range queries | More overhead; not stdlib-friendly in Kotlin |
| Hash map | O(1) lookup | No priority/order |

If you need priority plus lookup/removal by ID, use a heap plus an index map or a tree structure. Do not pretend a plain heap can do both.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Non-deterministic ordering | Comparator lacks tie-breaker | Add sequence/time/id |
| Stale tasks execute | Queue cannot remove arbitrary old items cheaply | Use cancellation flag or index map |
| Memory leak | Retaining old tasks with captured `Context` | Store IDs/data, not heavy references |
| Priority inversion | Low-priority task holds shared resource | Bound resources per priority; preempt/cancel |
| Lost retries | In-memory heap only | Persist retry state |
| Wrong comparator | Comparator violates transitivity | Test ordering invariants |

---

## Staff Engineer Thinking

1. **Priority is a product policy.** Define it explicitly; do not hide it in comparator magic.
2. **Add deterministic tie-breakers.** Reproducible scheduling makes bugs explainable.
3. **Separate scheduling from durability.** A heap decides next; storage remembers what exists.
4. **Watch cancellation.** Priority queues are bad at arbitrary deletion; design for stale entries.
5. **Measure fairness.** A high-priority stream can starve low-priority work forever.

---

## Probing Questions

1. Why is heap peek O(1) but arbitrary search O(n)?
2. How do you implement top K without sorting all N items?
3. Why does Java `PriorityQueue` need a tiebreaker for deterministic behavior?
4. How does Dijkstra use a priority queue?
5. What goes wrong if retry state is stored only in memory?
6. How would you prevent visible image loads from being blocked by prefetches?
7. When is a sorted list better than a heap?
8. How do you handle cancellation when `PriorityQueue.remove(item)` is O(n)?

## Answer Key

1. **Why is heap peek O(1) but arbitrary search O(n)?**
   A heap strictly maintains the minimum (or maximum) at the root, but the rest of the elements only guarantee parent-child relationships, not a total order, requiring a full scan for arbitrary elements.
2. **How do you implement top K without sorting all N items?**
   By maintaining a min-heap of size K. Iterate over the N items, pushing to the heap, and if the heap size exceeds K, pop the minimum element.
3. **Why does Java `PriorityQueue` need a tiebreaker for deterministic behavior?**
   Because it is not a stable structure; items with equal priorities can be ordered arbitrarily depending on their insertion history without an explicit tiebreaker.
4. **How does Dijkstra use a priority queue?**
   It uses a min-heap to efficiently and lazily fetch the next unvisited node with the shortest tentative distance from the start node.
5. **What goes wrong if retry state is stored only in memory?**
   If the application is killed by the OS or the device restarts, the in-memory heap is destroyed and all scheduled retries are permanently lost.
6. **How would you prevent visible image loads from being blocked by prefetches?**
   Use a priority queue (or prioritized thread pool) that strictly ranks visible UI image requests above background prefetches, while limiting overall concurrency.
7. **When is a sorted list better than a heap?**
   When you need fast in-order iteration, binary search capabilities, or rapid range queries, which a heap cannot provide.
8. **How do you handle cancellation when `PriorityQueue.remove(item)` is O(n)?**
   Use lazy deletion by marking the item as cancelled (e.g., with a boolean flag) and simply ignoring or discarding it when it naturally pops to the top of the heap.

## Further Reading

- [`graphs.md`](graphs.md)
- [`sorting-and-searching.md`](sorting-and-searching.md)
- [`../mobile-system-design/image-loading.md`](../mobile-system-design/image-loading.md)
- [`../android/concurrency/workmanager.md`](../android/concurrency/workmanager.md)

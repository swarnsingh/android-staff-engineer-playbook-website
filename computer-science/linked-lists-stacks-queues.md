# Linked Lists, Stacks, and Queues

## Overview

Linked lists, stacks, and queues are sequence structures defined less by storage and more by access pattern.

- A **linked list** stores nodes connected by references.
- A **stack** is last-in, first-out (LIFO).
- A **queue** is first-in, first-out (FIFO).
- A **deque** supports efficient operations at both ends.

In Android product code, you rarely need a hand-written linked list. But you constantly use stack and queue ideas: navigation back stacks, undo stacks, BFS queues, work queues, event buffers, retry queues, LRU caches, log buffers, and coroutine channels.

---

## Why It Matters

These structures teach ownership of order:

1. **Back stack is a stack.** Navigation correctness is stack discipline: push, pop, replace, restore.
2. **Work scheduling is queue discipline.** Uploads, sync operations, analytics events, and image requests need predictable ordering.
3. **LRU caches combine a hash map and a doubly linked list.** O(1) lookup plus O(1) recency updates.
4. **Linked lists are not automatically faster.** Pointer chasing is cache-unfriendly and allocation-heavy on mobile CPUs.

Staff engineers should recognize when a queue is the architecture, not just a data structure.

---

## First Principles

### Linked List

```text
head -> [A | next] -> [B | next] -> [C | null]
```

Singly linked list operations:

| Operation | Complexity | Note |
|---|---:|---|
| Insert after known node | O(1) | If you already have the node |
| Remove after known node | O(1) | Singly linked limitation |
| Find by value | O(n) | Must scan |
| Get by index | O(n) | No random access |
| Append without tail pointer | O(n) | Must walk |

Doubly linked list adds `prev`, making removal of a known node O(1), at the cost of more memory and more pointer maintenance.

### Stack

```kotlin
class Stack<T> {
    private val data = ArrayDeque<T>()
    fun push(value: T) = data.addLast(value)
    fun pop(): T = data.removeLast()
    fun peek(): T = data.last()
    fun isEmpty(): Boolean = data.isEmpty()
}
```

Use for nested scopes, undo, DFS, expression parsing, and navigation.

### Queue

```kotlin
class Queue<T> {
    private val data = ArrayDeque<T>()
    fun enqueue(value: T) = data.addLast(value)
    fun dequeue(): T = data.removeFirst()
    fun isEmpty(): Boolean = data.isEmpty()
}
```

Use for BFS, producer/consumer pipelines, work ordering, and buffering.

### Ring Buffer

A ring buffer stores a fixed-size queue in an array and wraps indices:

```kotlin
class RingBuffer<T>(private val capacity: Int) {
    private val values = arrayOfNulls<Any?>(capacity)
    private var start = 0
    private var size = 0

    init {
        require(capacity > 0)
    }

    fun add(value: T) {
        val index = (start + size) % capacity
        if (size == capacity) {
            values[start] = value
            start = (start + 1) % capacity
        } else {
            values[index] = value
            size++
        }
    }

    @Suppress("UNCHECKED_CAST")
    fun toList(): List<T> =
        List(size) { i -> values[(start + i) % capacity] as T }
}
```

Use for recent logs, last N analytics breadcrumbs, frame timing samples, and bounded event buffers.

---

## Kotlin and Android Details

### Prefer `ArrayDeque` Over `java.util.LinkedList`

On the JVM, `LinkedList` allocates a node object per element and pointer-chases through memory. `ArrayDeque` uses a resizable array and is usually faster due to cache locality.

Use `ArrayDeque` for stacks and queues unless you need stable node references or O(1) removal from the middle with a known node.

### LRU Cache: Hash Map + Doubly Linked List

An LRU cache needs:

- O(1) lookup by key.
- O(1) move-to-front when a key is used.
- O(1) eviction of least-recently used item.

That is exactly:

```text
HashMap<K, Node<K,V>> + DoublyLinkedList<Node<K,V>>
```

Android's `LruCache` hides this. The lesson is architectural: two simple structures compose into a stronger one.

### Navigation Back Stack

```text
Home -> Search -> Details
pop()
Home -> Search
```

Back stack bugs are stack bugs:

- Duplicate destinations from repeated taps.
- Losing nested stack state on bottom navigation.
- Deep links that push the wrong parent chain.
- Process death restoring an invalid stack.

Treat navigation as data, not as a series of side effects.

### Work Queues and Durability

An in-memory queue is not enough for important work:

```kotlin
val queue = ArrayDeque<Upload>()
```

This dies with the process. For uploads, sync, and analytics with delivery guarantees, persist the queue in Room or use WorkManager/outbox patterns. The queue is a concept; durability is a separate requirement.

---

## Common Patterns

### BFS With a Queue

```kotlin
fun <T> bfs(start: T, neighbors: (T) -> Iterable<T>): List<T> {
    val seen = mutableSetOf(start)
    val queue = ArrayDeque<T>()
    val order = mutableListOf<T>()
    queue.addLast(start)

    while (queue.isNotEmpty()) {
        val node = queue.removeFirst()
        order += node
        for (next in neighbors(node)) {
            if (seen.add(next)) queue.addLast(next)
        }
    }
    return order
}
```

Use for nearest-match discovery, dependency levels, graph traversal, and tree level-order traversal.

### DFS Without Recursion

```kotlin
fun <T> dfsIterative(start: T, neighbors: (T) -> Iterable<T>): List<T> {
    val seen = mutableSetOf<T>()
    val stack = ArrayDeque<T>()
    val order = mutableListOf<T>()
    stack.addLast(start)

    while (stack.isNotEmpty()) {
        val node = stack.removeLast()
        if (!seen.add(node)) continue
        order += node
        for (next in neighbors(node)) stack.addLast(next)
    }
    return order
}
```

Use when recursion depth may overflow the call stack.

### Monotonic Queue

Maintains candidates in sorted order for sliding-window min/max:

```kotlin
fun maxSlidingWindow(nums: IntArray, k: Int): IntArray {
    val deque = ArrayDeque<Int>() // indices, values decreasing
    val result = IntArray(nums.size - k + 1)

    for (i in nums.indices) {
        while (deque.isNotEmpty() && deque.first() <= i - k) deque.removeFirst()
        while (deque.isNotEmpty() && nums[deque.last()] <= nums[i]) deque.removeLast()
        deque.addLast(i)
        if (i >= k - 1) result[i - k + 1] = nums[deque.first()]
    }
    return result
}
```

Useful for streaming metrics, rolling maxima, and rate-window calculations.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Slow "linked list" code | Pointer chasing and allocation overhead | Use `ArrayDeque` or `ArrayList` |
| Lost uploads after process death | In-memory queue | Persistent outbox / WorkManager |
| Stack overflow | Recursive DFS over untrusted/deep input | Iterative stack |
| Memory leak in queue | Consumer slower than producer, unbounded queue | Backpressure, limits, drop policy |
| Duplicate navigation | Multiple pushes for same event | Debounce, single-flight, model stack as state |
| LRU cache never evicts | Missing size accounting | Define weight: bytes, rows, entries |

---

## Staff Engineer Thinking

1. **Access pattern first.** Do you need random access, FIFO, LIFO, priority, or recency?
2. **Durability is not implied.** A queue can be in memory, in SQLite, in WorkManager, or on the server. Pick based on loss tolerance.
3. **Bound every buffer.** Unbounded queues convert temporary downstream slowness into OOM.
4. **Prefer arrays for CPU locality.** Linked structures are elegant but often slow on real devices.
5. **Model stacks explicitly.** Navigation and undo are easier to test as data structures than as scattered side effects.

---

## Probing Questions

1. Why is `ArrayDeque` usually better than `LinkedList` for a queue on Android?
2. How does an LRU cache achieve O(1) lookup and O(1) eviction?
3. When does a recursive traversal become a reliability risk?
4. Why is an in-memory upload queue insufficient for offline sync?
5. What backpressure policy would you choose for analytics events?
6. How is bottom-navigation state a multiple-stack problem?
7. What data structure would you use for "last 100 logs"?
8. Why does removing the first item from `ArrayList` cost O(n)?

## Answer Key

1. **Why is `ArrayDeque` usually better than `LinkedList` for a queue on Android?**
   Because `ArrayDeque` is backed by a contiguous array resulting in excellent CPU cache locality, whereas `LinkedList` incurs heavy allocation overhead and cache misses from pointer chasing.
2. **How does an LRU cache achieve O(1) lookup and O(1) eviction?**
   By combining a hash map for O(1) key lookups and a doubly linked list for O(1) removals and recency updates.
3. **When does a recursive traversal become a reliability risk?**
   When processing deeply nested or adversarial inputs that can overflow the JVM call stack, causing a StackOverflowError.
4. **Why is an in-memory upload queue insufficient for offline sync?**
   In-memory queues do not survive process death, leading to permanent data loss if the app is killed before the sync completes.
5. **What backpressure policy would you choose for analytics events?**
   Apply a bounded queue size and define a drop policy (like dropping the oldest events) to prevent memory leaks and out-of-memory (OOM) errors on slow networks.
6. **How is bottom-navigation state a multiple-stack problem?**
   Each bottom navigation tab requires its own independent back stack, so the system must preserve and restore individual stacks rather than relying on one global stack.
7. **What data structure would you use for "last 100 logs"?**
   A ring buffer (or circular array), which natively enforces a fixed size and provides O(1) additions by wrapping around and overwriting the oldest entries.
8. **Why does removing the first item from `ArrayList` cost O(n)?**
   Because all `n - 1` subsequent elements must be shifted one index to the left to fill the vacated slot.

## Further Reading

- [`arrays-and-strings.md`](arrays-and-strings.md)
- [`graphs.md`](graphs.md)
- [`../android/architecture/navigation.md`](../android/architecture/navigation.md)
- [`../mobile-system-design/offline-sync.md`](../mobile-system-design/offline-sync.md)

# Recursion and Backtracking

## Overview

**Recursion** solves a problem by calling the same logic on smaller subproblems. **Backtracking** is recursive search with undo: choose, explore, undo, try the next choice.

These tools show up in tree traversal, graph DFS, parsers, layout trees, dependency resolution, route exploration, combinatorial search, and interview problems. In production Android, recursion must be used with care because the call stack is finite and user-controlled input can be maliciously deep.

---

## Why It Matters

1. **UI and data are often recursive.** View trees, Compose trees, JSON/XML trees, file systems, comment threads, and navigation graphs.
2. **Backtracking teaches state discipline.** Mutate, recurse, restore. Missing restoration creates subtle bugs.
3. **Stack overflow is real.** Deep trees or adversarial input can crash the app.
4. **Exponential search needs pruning.** Brute-force recursion can explode instantly.

Staff-level use means knowing when recursion expresses the domain beautifully and when it must be replaced by an explicit stack.

---

## Recursion First Principles

Every recursive function needs:

1. **Base case:** when to stop.
2. **Progress:** each call moves closer to the base case.
3. **Combination:** how subproblem results produce the answer.

```kotlin
fun factorial(n: Int): Long {
    require(n >= 0)
    return if (n <= 1) 1 else n * factorial(n - 1)
}
```

This is correct but not how you should compute factorial in production. It is a teaching example for structure.

---

## Tree Traversal

```kotlin
data class Node(
    val id: String,
    val children: List<Node> = emptyList()
)

fun countNodes(root: Node): Int {
    var count = 1
    for (child in root.children) {
        count += countNodes(child)
    }
    return count
}
```

Readable, but dangerous for unbounded depth. Convert to iterative traversal when input depth is not controlled:

```kotlin
fun countNodesIterative(root: Node): Int {
    val stack = ArrayDeque<Node>()
    var count = 0
    stack.addLast(root)

    while (stack.isNotEmpty()) {
        val node = stack.removeLast()
        count++
        for (child in node.children) stack.addLast(child)
    }
    return count
}
```

---

## Backtracking Pattern

Backtracking explores a decision tree:

```text
choose option
explore deeper
undo option
try next option
```

Example: generate subsets.

```kotlin
fun subsets(values: IntArray): List<List<Int>> {
    val result = mutableListOf<List<Int>>()
    val current = mutableListOf<Int>()

    fun dfs(index: Int) {
        if (index == values.size) {
            result += current.toList()
            return
        }

        // Exclude
        dfs(index + 1)

        // Include
        current += values[index]
        dfs(index + 1)
        current.removeAt(current.lastIndex)
    }

    dfs(0)
    return result
}
```

Complexity: O(2^n). For n = 30, that is over a billion subsets. Correct does not mean feasible.

---

## Permutations

```kotlin
fun permutations(values: IntArray): List<List<Int>> {
    val result = mutableListOf<List<Int>>()
    val used = BooleanArray(values.size)
    val current = mutableListOf<Int>()

    fun dfs() {
        if (current.size == values.size) {
            result += current.toList()
            return
        }

        for (i in values.indices) {
            if (used[i]) continue
            used[i] = true
            current += values[i]
            dfs()
            current.removeAt(current.lastIndex)
            used[i] = false
        }
    }

    dfs()
    return result
}
```

Complexity: O(n!). This is only acceptable for small n or with strong pruning.

---

## Pruning

Pruning cuts branches that cannot produce a valid answer.

```kotlin
fun combinationSum(values: IntArray, target: Int): List<List<Int>> {
    val sorted = values.sorted()
    val result = mutableListOf<List<Int>>()
    val current = mutableListOf<Int>()

    fun dfs(start: Int, remaining: Int) {
        if (remaining == 0) {
            result += current.toList()
            return
        }
        for (i in start until sorted.size) {
            val value = sorted[i]
            if (value > remaining) break // pruning because sorted
            current += value
            dfs(i + 1, remaining - value)
            current.removeAt(current.lastIndex)
        }
    }

    dfs(0, target)
    return result
}
```

Sorting enables early exit. Without the sorted invariant, `break` would be wrong.

---

## Kotlin Tail Recursion

Kotlin can optimize tail recursion when marked `tailrec`:

```kotlin
tailrec fun gcd(a: Int, b: Int): Int {
    return if (b == 0) kotlin.math.abs(a) else gcd(b, a % b)
}
```

The recursive call must be the final operation. This will not optimize:

```kotlin
fun sum(n: Int): Int =
    if (n == 0) 0 else n + sum(n - 1) // not tail-recursive
```

Staff rule: `tailrec` is useful, but explicit loops are often clearer for production hot paths.

---

## Android Examples

### Recursive UI Trees

Comments, categories, settings sections, and file explorers are recursive. Keep depth bounded and avoid unbounded recursive composition for hostile data.

### Parsing Nested JSON

An attacker can send deeply nested JSON to trigger stack overflow in recursive parsers. Set depth limits.

### Dependency Graph DFS

Gradle modules, DI dependencies, and navigation graphs all use DFS-like traversal. Detect cycles with a visiting set.

```kotlin
enum class Mark { Visiting, Done }

fun hasCycle(graph: Map<String, List<String>>): Boolean {
    val marks = mutableMapOf<String, Mark>()

    fun visit(node: String): Boolean {
        when (marks[node]) {
            Mark.Visiting -> return true
            Mark.Done -> return false
            null -> Unit
        }
        marks[node] = Mark.Visiting
        for (next in graph[node].orEmpty()) {
            if (visit(next)) return true
        }
        marks[node] = Mark.Done
        return false
    }

    return graph.keys.any { visit(it) }
}
```

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Stack overflow | Deep recursion | Iterative stack or depth limit |
| Infinite recursion | No progress toward base case | Prove decreasing input |
| Wrong backtracking result | Forgot undo step | Pair every mutation with restore |
| Exponential blowup | Brute-force search | Prune, memoize, constrain input |
| Duplicate permutations | Duplicate input without skip logic | Sort and skip equal choices |
| UI freeze | Search on main thread | Move off main; stream/cancel |

---

## Staff Engineer Thinking

1. **Bound the tree.** If user/server controls depth, recursion is a risk.
2. **Make state restoration obvious.** Backtracking code should visually pair choose/undo.
3. **Prune with proof.** A pruning rule is only valid if its invariant is documented.
4. **Prefer iterative traversal for infrastructure.** Build tools, parsers, and sync engines should not crash on deep input.
5. **Cancel long searches.** Recursive work in mobile apps must respect lifecycle and cancellation.

---

## Probing Questions

1. What are the three required parts of a recursive function?
2. Why can recursive DFS crash on a valid but deep graph?
3. What is the choose/explore/undo pattern?
4. Why is subset generation O(2^n)?
5. Why is permutation generation O(n!)?
6. When does Kotlin optimize `tailrec`?
7. How do you detect cycles in DFS?
8. What makes a pruning rule correct?

## Further Reading

- [`trees.md`](trees.md)
- [`graphs.md`](graphs.md)
- [`dynamic-programming.md`](dynamic-programming.md)
- [`../android/build-tooling/gradle-and-build-systems.md`](../android/build-tooling/gradle-and-build-systems.md)

# Dynamic Programming

## Overview

**Dynamic programming (DP)** solves problems by reusing answers to overlapping subproblems. It is not a bag of memorized patterns. It is a discipline for turning exponential recursion into polynomial work when the same states repeat.

In mobile engineering, DP appears in text diffing, edit distance, layout optimization, route scoring, media algorithms, compression, spell correction, and any feature that asks, "what is the best result up to this point?"

---

## Why It Matters

1. **DP explains real libraries.** Diff algorithms, spell checkers, and sequence alignment are DP-adjacent.
2. **It teaches state design.** The hardest part is not the loop; it is choosing the state that fully describes the subproblem.
3. **It exposes space tradeoffs.** Many O(n*m) tables can become O(min(n, m)) memory.
4. **It prevents brute-force explosions.** Reusing subproblems converts repeated recursive work into cached work.

Staff engineers do not need to recite 100 DP problems. They need to recognize when repeated state exists and design a bounded, testable state space.

---

## First Principles

A problem is a DP candidate when it has:

1. **Overlapping subproblems:** the same smaller question appears many times.
2. **Optimal substructure:** the best answer for a larger problem can be built from best answers to smaller problems.

Example Fibonacci:

```kotlin
fun fibSlow(n: Int): Long {
    return if (n <= 1) n.toLong() else fibSlow(n - 1) + fibSlow(n - 2)
}
```

This recomputes the same values repeatedly. Memoization fixes it:

```kotlin
fun fib(n: Int): Long {
    val memo = LongArray(n + 1) { -1 }

    fun solve(i: Int): Long {
        if (i <= 1) return i.toLong()
        if (memo[i] != -1L) return memo[i]
        memo[i] = solve(i - 1) + solve(i - 2)
        return memo[i]
    }

    return solve(n)
}
```

Tabulation removes recursion:

```kotlin
fun fibTab(n: Int): Long {
    if (n <= 1) return n.toLong()
    var prev = 0L
    var curr = 1L
    repeat(n - 1) {
        val next = prev + curr
        prev = curr
        curr = next
    }
    return curr
}
```

---

## Memoization vs Tabulation

| Approach | Shape | Strength | Weakness |
|---|---|---|---|
| Memoization | Top-down recursion + cache | Natural from recurrence | Stack depth; cache overhead |
| Tabulation | Bottom-up loops | Predictable memory/time | Requires iteration order |
| Space-optimized tabulation | Keep only needed rows/states | Lower memory | Easier to get wrong |

Use memoization to discover the recurrence. Use tabulation when performance, memory, or stack safety matters.

---

## State Design

A DP state must contain all information needed to answer the subproblem.

For edit distance:

```text
dp[i][j] = minimum edits to transform first i chars of a into first j chars of b
```

That state is complete: the future does not need to know the exact edit sequence, only the cost so far.

Bad state design either:

- misses information and gives wrong answers, or
- includes too much information and explodes memory.

---

## Classic Examples

### 1D DP: House Robber

```kotlin
fun maxNonAdjacentSum(values: IntArray): Int {
    var skip = 0
    var take = 0

    for (value in values) {
        val newTake = skip + value
        val newSkip = maxOf(skip, take)
        take = newTake
        skip = newSkip
    }
    return maxOf(skip, take)
}
```

State:

- `take`: best sum if current item is taken.
- `skip`: best sum if current item is skipped.

### 2D DP: Edit Distance

```kotlin
fun editDistance(a: String, b: String): Int {
    val dp = Array(a.length + 1) { IntArray(b.length + 1) }

    for (i in 0..a.length) dp[i][0] = i
    for (j in 0..b.length) dp[0][j] = j

    for (i in 1..a.length) {
        for (j in 1..b.length) {
            val cost = if (a[i - 1] == b[j - 1]) 0 else 1
            dp[i][j] = minOf(
                dp[i - 1][j] + 1,      // delete
                dp[i][j - 1] + 1,      // insert
                dp[i - 1][j - 1] + cost // replace/match
            )
        }
    }
    return dp[a.length][b.length]
}
```

Use in spell correction, fuzzy search, diffing concepts, and text similarity.

### Knapsack

```kotlin
data class Item(val weight: Int, val value: Int)

fun knapsack(capacity: Int, items: List<Item>): Int {
    val dp = IntArray(capacity + 1)

    for (item in items) {
        for (w in capacity downTo item.weight) {
            dp[w] = maxOf(dp[w], dp[w - item.weight] + item.value)
        }
    }
    return dp[capacity]
}
```

The reverse loop matters. Forward looping would allow using the same item multiple times.

---

## Android and Systems Examples

### Diffing

List diffing asks for an edit script between old and new sequences. Android's DiffUtil uses Myers' algorithm rather than a simple O(n*m) DP table, but the mental model is related: compute a minimal set of insert/delete/move-like changes instead of redrawing everything.

### Text Input and Search

Edit distance can rank typo-tolerant local suggestions. Staff caution: full edit distance over a large dictionary is expensive. Use indexes, tries, candidate pruning, or server search.

### Layout and Rendering

Some layout and line-breaking algorithms use DP to choose visually optimal breaks. Mobile UI often chooses faster greedy approximations when full optimality costs too much.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Memory blowup | O(n*m) table for large inputs | Rolling rows, pruning, approximate algorithm |
| Stack overflow | Recursive memoization over deep state | Tabulation |
| Wrong answer | State missing required dimension | Redefine state carefully |
| Reusing item twice | Wrong loop direction in 0/1 knapsack | Iterate capacity downward |
| Timeout | DP state space too large | Bound input, use greedy/heuristic |
| Main-thread freeze | Heavy DP in UI path | Move off main, cancel, chunk |

---

## Staff Engineer Thinking

1. **Name the state in English.** If you cannot describe `dp[i][j]`, you do not understand it.
2. **Estimate memory before coding.** `100_000 x 100_000` is impossible.
3. **Prefer approximate when product allows.** Fuzzy search and ranking often do not need exact optimality.
4. **Use DP to understand libraries.** You may not write DiffUtil, but you should know why it exists.
5. **Test boundaries.** Empty input, one item, repeated values, and maximum sizes find DP bugs quickly.

---

## Probing Questions

1. What are overlapping subproblems?
2. What is optimal substructure?
3. When would you choose memoization over tabulation?
4. Why can a 2D DP table be a mobile memory problem?
5. Explain edit distance state `dp[i][j]`.
6. Why does 0/1 knapsack iterate capacity backward?
7. How is list diffing related to dynamic programming?
8. When should you choose a greedy approximation over DP?

## Answer Key

1. **What are overlapping subproblems?**
   When a recursive algorithm encounters and solves the exact same smaller problem instances multiple times.
2. **What is optimal substructure?**
   When the globally optimal solution to a problem can be constructed directly from the optimal solutions of its subproblems.
3. **When would you choose memoization over tabulation?**
   When the state space is sparse (not all states need to be computed) or when translating a recursive mathematical recurrence directly is easier.
4. **Why can a 2D DP table be a mobile memory problem?**
   Allocating an O(n*m) array for large inputs can consume hundreds of megabytes, leading to OutOfMemory (OOM) errors on constrained mobile devices.
5. **Explain edit distance state `dp[i][j]`.**
   It represents the minimum number of edit operations needed to transform the first `i` characters of one string into the first `j` characters of the other.
6. **Why does 0/1 knapsack iterate capacity backward?**
   To ensure each item is only used once; forward iteration would allow a newly updated state to be reused within the same item's loop.
7. **How is list diffing related to dynamic programming?**
   Algorithms like Myers' diff compute the shortest edit script (insertions/deletions) between two sequences, operating on the same principles as the longest common subsequence DP problem.
8. **When should you choose a greedy approximation over DP?**
   When the optimal DP solution is computationally or memory prohibitive given the input size, and a slightly suboptimal greedy result is acceptable for the product.

## Further Reading

- [`recursion-backtracking.md`](recursion-backtracking.md)
- [`arrays-and-strings.md`](arrays-and-strings.md)
- [`../android/performance/jank.md`](../android/performance/jank.md)
- [`../mobile-system-design/search.md`](../mobile-system-design/search.md)

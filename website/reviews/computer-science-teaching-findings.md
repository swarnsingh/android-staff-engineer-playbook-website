# Computer Science teaching layer: possible errors in the original chapters

Findings for the owner's review, not approved corrections. The original Markdown is unchanged and nothing has been added to `content/corrections-*.json`. Per the owner decision of 28 October 2026, published pages carry no review notices, and the publication gate rejects them. Findings are tracked here only. The teaching layer does not restate the claim.

| ID | Chapter, section | Original says | Problem | Evidence |
|---|---|---|---|---|
| SC1 | System Complexity: Why It Exists, point 2 | "A function with cyclomatic complexity 20 has roughly 4x the defect rate of one with complexity 5 — not 4x, exponentially worse." | The sentence states a 4x ratio and then denies it in the same breath, and no source is given for either figure. The surrounding point (defects correlate with complexity metrics) can stand without a specific ratio | Internal consistency; no cited study for the 4x figure |

This review covered only claims the teaching layer touches. A full fact-check of the Computer Science tree has not been done yet.

## Claims the teaching layer makes, and what they were checked against

These are the technical statements added by the layer. None restates SC1.

| Chapter | Claim in the layer | Checked against |
|---|---|---|
| Hashing | Java's `HashMap` turns a heavily collided bucket into a balanced tree, limiting that bucket's search to O(log n) when keys are comparable; resizing rehashes entries and keeps inserts amortized O(1) | OpenJDK `java.util.HashMap` implementation notes (treeified bins, `TREEIFY_THRESHOLD`, resize) |
| Hashing | A key whose `hashCode` changes while it is in a map usually becomes unfindable | `java.util.Map` contract: behaviour is unspecified if a key's equality-relevant state changes while it is a key |
| Heaps | `PriorityQueue`: `peek` O(1); `offer`/`poll` O(log n); `remove(Object)` and `contains` linear; iteration is not in priority order | `java.util.PriorityQueue` class documentation (implementation note and `iterator()` description) |
| Heaps | Building a heap from an existing collection is O(n) | Standard bottom-up heap construction (`PriorityQueue(Collection)` heapifies) |
| Sorting | Kotlin `sortedBy` and `sortedWith` are stable | kotlinlang.org API reference: "The sort is stable" |
| Sorting | An inconsistent comparator can make the sort throw "Comparison method violates its general contract!" | `java.util.Arrays.sort` / `List.sort` documentation: may throw `IllegalArgumentException` if the comparator violates the `Comparator` contract |
| Sorting | `List.binarySearch` returns `-(insertionPoint) - 1` when the element is absent | kotlinlang.org `binarySearch` reference |
| Sorting | `(lo + hi) / 2` can overflow; `lo + (hi - lo) / 2` or `ushr 1` cannot | Integer arithmetic; widely documented binary-search overflow bug |
| Recursion | `tailrec` applies only when the recursive call is the last operation; otherwise the compiler warns and keeps ordinary recursion | kotlinlang.org Functions reference, tail-recursive functions |
| Graphs | BFS gives fewest hops on unweighted graphs; Dijkstra needs non-negative weights and runs in O((V + E) log V) with a binary heap; Kahn's algorithm leaves nodes unprocessed exactly when a cycle exists | Standard algorithm definitions (CLRS) |
| Trees | Red-black trees back Java's `TreeMap`; a plain BST built from sorted keys degenerates to height n | `java.util.TreeMap` documentation; BST definition |
| Dynamic programming | Coins {1, 3, 4}, amount 6: optimum 2 coins (3 + 3); greedy picks 4 + 1 + 1 | Worked by hand |
| Greedy | Earliest-end selection is optimal for the most non-overlapping intervals; the shortest-first counterexample [1, 5], [4, 7], [6, 10] | Exchange argument; counterexample worked by hand |
| System complexity | Cyclomatic complexity is roughly decision points plus one; cognitive complexity counts a flat `switch`/`when` once and adds a nesting increment for nested structures | McCabe (1976); SonarSource *Cognitive Complexity* white paper (G. Ann Campbell) |

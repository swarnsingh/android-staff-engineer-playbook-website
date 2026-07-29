# Computer Science

## Purpose

A focused computer-science tree for Android engineers. This repo does not optimize for LeetCode cramming; it teaches the structures and algorithms that explain real mobile architecture, performance, reliability, and interview fundamentals.

## Why It Matters

You will rarely write a custom hash table, but you will frequently decide between a hash-based and tree-based structure for an LRU cache. Big-O appears in capacity-planning conversations. Graph reasoning appears in dependency-resolution and routing. Arrays, queues, heaps, sorting, recursion, dynamic programming, and intervals explain the performance shape of real product features.

## What This Folder Helps You Do

- Build the algorithmic vocabulary needed for senior Android interviews without turning the repo into a puzzle catalog.
- Connect data structures to real mobile systems: DiffUtil, RecyclerView/Compose lists, caches, dependency graphs, routing, search, typeahead, sync queues, and local indexes.
- Estimate CPU, memory, and latency costs before choosing a collection, algorithm, database query, or module graph shape.
- Recognize when an algorithmic pattern is the right tool and when product constraints, persistence, or network behavior dominate the problem.

## Guided Reading Sequence

Prerequisite: [Engineering Fundamentals](engineering-fundamentals.md). Read the structures before the algorithms that operate on them; finish by reconnecting algorithmic cost to production systems.

1. [Big-O](computer-science/big-o.md) — bridge file; canonical mechanics live in [Complexity Analysis](engineering-fundamentals/complexity-analysis.md).
2. [Arrays and Strings](computer-science/arrays-and-strings.md)
3. [Linked Lists, Stacks, and Queues](computer-science/linked-lists-stacks-queues.md)
4. [Hashing](computer-science/hashing.md)
5. [Trees](computer-science/trees.md)
6. [Graphs](computer-science/graphs.md)
7. [Heaps and Priority Queues](computer-science/heaps-and-priority-queues.md)
8. [Sorting and Searching](computer-science/sorting-and-searching.md)
9. [Recursion and Backtracking](computer-science/recursion-backtracking.md)
10. [Dynamic Programming](computer-science/dynamic-programming.md)
11. [Greedy Algorithms and Intervals](computer-science/greedy-and-intervals.md)
12. [System Complexity](computer-science/system-complexity.md) — how data-structure choices shape real systems.

**Next:** continue to [Kotlin](kotlin.md).

## What This Tree Avoids

A giant catalog of puzzle variants. Each file teaches the reusable mental model, Kotlin/Android implications, failure modes, and Staff-level tradeoffs. Practice problems are useful, but they are not the product of this repository.

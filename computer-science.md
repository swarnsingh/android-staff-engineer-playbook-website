# Computer Science

## Purpose

A deliberately lean tree. This repo explicitly does NOT optimize for LeetCode cramming — a Staff Mobile Platform Engineer is differentiated by systems thinking, not by memorizing graph traversals. This tree covers only the foundational pieces that inform architecture.

## Why It Matters

You will rarely write a custom hash table, but you will frequently decide between a hash-based and tree-based structure for an LRU cache. Big-O appears in capacity-planning conversations. Graph reasoning appears in dependency-resolution and routing. This tree teaches the structures as architectural primitives.

## Learning Order

Big-O first (it's the language everything else uses), then the structures (hashing, trees, graphs), then `system-complexity` which ties data-structure choice to real-system performance.

## Topics

- [Big-O](computer-science/big-o.md) — short stub; canonical is [`engineering-fundamentals/complexity-analysis.md`](engineering-fundamentals/complexity-analysis.md)
- [Hashing](computer-science/hashing.md)
- [Trees](computer-science/trees.md)
- [Graphs](computer-science/graphs.md)
- [System Complexity](computer-science/system-complexity.md) — how data-structure choices shape real systems

## What's Deliberately NOT Here

A full LeetCode-pattern tree (arrays, linked-lists, sliding-window, binary-search as separate study files). That is interview cramming relabeled, and it contradicts this repo's stated goal. If a specific structure becomes relevant to a real topic, it gets a short canonical file then — not preemptively.

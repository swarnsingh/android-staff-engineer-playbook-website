# Principles

## Purpose

Decision heuristics. Distinct from patterns — patterns are *implementations*; principles are the *heuristics a Staff engineer reaches for when deciding*.

## Boundary

"Determinism" as a decision heuristic (prefer deterministic designs) is a principle and lives here. "How determinism works mechanically" is a fundamental and lives in [`engineering-fundamentals/`](engineering-fundamentals.md). Same word, two homes, two angles — link between them, don't duplicate.

## Why It Matters

You can't memorize the right answer to every design question. You can internalize the heuristics that make the right answer reachable.

## What This Folder Helps You Do

- Build judgment that transfers across technologies instead of memorizing framework-specific rules.
- Explain why a design is simple, cohesive, failure-aware, evolvable, deterministic, or deletion-friendly.
- Use principles as review tools: identify when a module has too many reasons to change, when knowledge leaks across boundaries, and when an abstraction hides more than it helps.
- Balance principles against each other, because Staff-level decisions often involve choosing which good rule matters most in a specific context.

## Guided Reading Sequence

Prerequisites: [Engineering Fundamentals](engineering-fundamentals.md) and the language/API-design portion of [Kotlin](kotlin.md). Apply each principle to a design you already know before continuing.

1. [Simplicity](principles/simplicity.md)
2. [Single Responsibility](principles/single-responsibility.md)
3. [Least Knowledge (Law of Demeter)](principles/least-knowledge.md)
4. [Composition over Inheritance](principles/composition-over-inheritance.md)
5. [Make Invalid States Impossible](principles/make-invalid-states-impossible.md)
6. [Locality of Reference](principles/locality-of-reference.md)
7. [Progressive Disclosure](principles/progressive-disclosure.md)
8. [Prefer Deletion](principles/prefer-deletion.md)
9. [Design for Failure](principles/design-for-failure.md)
10. [Determinism](principles/determinism.md) — reused by idempotency and offline sync.
11. [Optimize for Change](principles/optimize-for-change.md)

**Next:** continue to [Patterns](patterns.md), then [Android](android.md).

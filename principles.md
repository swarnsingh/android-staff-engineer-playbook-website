# Principles

## Purpose

Decision heuristics. Distinct from patterns — patterns are *implementations*; principles are the *heuristics a Staff engineer reaches for when deciding*.

## Boundary

"Determinism" as a decision heuristic (prefer deterministic designs) is a principle and lives here. "How determinism works mechanically" is a fundamental and lives in [`engineering-fundamentals/`](engineering-fundamentals.md). Same word, two homes, two angles — link between them, don't duplicate.

## Why It Matters

You can't memorize the right answer to every design question. You can internalize the heuristics that make the right answer reachable.

## Learning Order

The simplest first — Simplicity, Single Responsibility, Composition over Inheritance — then the operational ones — Design for Failure, Prefer Deletion — then the more abstract ones — Determinism, Optimize for Change.

## Topics

- [Simplicity](principles/simplicity.md)
- [Least Knowledge (Law of Demeter)](principles/least-knowledge.md)
- [Single Responsibility](principles/single-responsibility.md)
- [Composition over Inheritance](principles/composition-over-inheritance.md)
- [Prefer Deletion](principles/prefer-deletion.md)
- [Make Invalid States Impossible](principles/make-invalid-states-impossible.md)
- [Locality of Reference](principles/locality-of-reference.md)
- [Optimize for Change](principles/optimize-for-change.md)
- [Design for Failure](principles/design-for-failure.md)
- [Determinism](principles/determinism.md) — referenced from `airbridge/deterministic-resume.md`, `distributed-systems/idempotency.md`, `mobile-system-design/offline-sync.md`
- [Progressive Disclosure](principles/progressive-disclosure.md)

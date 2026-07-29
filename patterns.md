# Patterns

## Purpose

Canonical home for design and resilience patterns. These are referenced from everywhere; without this folder, Circuit Breaker gets re-explained in five files.

## Boundary

Patterns are *implementations* — reusable shapes that solve a class of problems. They are distinct from [principles](principles.md) (decision heuristics) and [fundamentals](engineering-fundamentals.md) (mechanics).

State machines have a canonical owner in [`engineering-fundamentals/state-machines.md`](engineering-fundamentals/state-machines.md) (mechanics); [`patterns/state.md`](patterns/state.md) is the pattern-shaped implementation. Cross-link both ways.

## What This Folder Helps You Do

- Recognize recurring solution shapes in Android, Kotlin, backend-for-mobile, and platform code without cargo-culting them.
- Choose implementation patterns intentionally: Repository for source-of-truth boundaries, Adapter for anti-corruption layers, Strategy for runtime behavior, Command for queued work, and Saga for multi-step recovery.
- Apply resilience patterns such as Retry and Circuit Breaker with mobile constraints like battery, offline mode, idempotency, and user-visible fallback.
- Review whether a pattern reduces complexity or merely adds vocabulary around code that should stay simple.

## Guided Reading Sequence

Prerequisites: [Engineering Fundamentals](engineering-fundamentals.md) and [Principles](principles.md). Patterns are reusable implementation shapes, not substitutes for the mechanics and tradeoffs underneath them.

### Phase 1 — Boundaries and object collaboration

1. [Repository](patterns/repository.md)
2. [Adapter](patterns/adapter.md)
3. [Factory](patterns/factory.md)
4. [Builder](patterns/builder.md)
5. [Strategy](patterns/strategy.md)
6. [Decorator](patterns/decorator.md)
7. [Observer](patterns/observer.md)
8. [State](patterns/state.md) — implementation; read state-machine mechanics first.
9. [Command](patterns/command.md)

### Phase 2 — Resilience and distributed recovery

10. [Retry](patterns/retry.md)
11. [Circuit Breaker](patterns/circuit-breaker.md)
12. [Saga](patterns/saga.md)

**Next:** apply these patterns in [Android](android.md) and [Mobile System Design](mobile-system-design.md).

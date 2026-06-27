# Patterns

## Purpose

Canonical home for design and resilience patterns. These are referenced from everywhere; without this folder, Circuit Breaker gets re-explained in five files.

## Boundary

Patterns are *implementations* — reusable shapes that solve a class of problems. They are distinct from [principles](principles.md) (decision heuristics) and [fundamentals](engineering-fundamentals.md) (mechanics).

State machines have a canonical owner in [`engineering-fundamentals/state-machines.md`](engineering-fundamentals/state-machines.md) (mechanics); [`patterns/state.md`](patterns/state.md) is the pattern-shaped implementation. Cross-link both ways.

## Learning Order

Design patterns first (the classics), then resilience patterns (the production-engineering set).

## Topics

### Design Patterns

- [Repository](patterns/repository.md)
- [Adapter](patterns/adapter.md)
- [Factory](patterns/factory.md)
- [Strategy](patterns/strategy.md)
- [Observer](patterns/observer.md)
- [State](patterns/state.md) — implementation; mechanics in `engineering-fundamentals/state-machines.md`
- [Builder](patterns/builder.md)
- [Decorator](patterns/decorator.md)
- [Command](patterns/command.md)

### Resilience Patterns

- [Circuit Breaker](patterns/circuit-breaker.md)
- [Retry](patterns/retry.md)
- [Saga](patterns/saga.md)


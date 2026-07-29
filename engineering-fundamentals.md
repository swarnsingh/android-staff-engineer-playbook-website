# Engineering Fundamentals

## Purpose

The canonical home for timeless concepts that span Android, backend, and distributed systems. These never become obsolete. Per the canonical-owner rule, everything else in the repo links here rather than re-explaining.

## Why It Matters

A Staff Mobile Platform Engineer is differentiated less by knowing a specific framework and more by understanding the substrate everything sits on: concurrency, state, caching, time. These are the concepts you reach for when designing under pressure.

## What This Folder Helps You Do

- Learn the timeless mechanics that reappear in Android, backend systems, distributed systems, SDKs, and platform engineering.
- Explain tradeoffs using first principles instead of framework names: latency vs throughput, sync vs async, coupling, cohesion, queues, state machines, caching, and backpressure.
- Spot design failure modes early: unbounded queues, hidden shared mutable state, cache incoherence, retry storms, clock assumptions, and serialization brittleness.
- Use one shared vocabulary across the repo so application files can stay focused on concrete systems instead of redefining fundamentals.

## Guided Reading Sequence

This is the first tree in the [Complete Curriculum](learning-paths.md#path-0-complete-curriculum-for-new-learners). Read in order: vocabulary first, state and coordination next, then production failure behavior.

1. [Complexity Analysis](engineering-fundamentals/complexity-analysis.md) — canonical owner; `computer-science/big-o.md` cross-references.
2. [Latency vs Throughput](engineering-fundamentals/latency-vs-throughput.md)
3. [Sync vs Async](engineering-fundamentals/sync-vs-async.md)
4. [Coupling vs Cohesion](engineering-fundamentals/coupling-vs-cohesion.md)
5. [Immutability](engineering-fundamentals/immutability.md)
6. [State Machines](engineering-fundamentals/state-machines.md) — canonical owner; all application FSMs link here.
7. [Queues](engineering-fundamentals/queues.md)
8. [Event-Driven Architecture](engineering-fundamentals/event-driven-architecture.md)
9. [Serialization](engineering-fundamentals/serialization.md)
10. [Caching](engineering-fundamentals/caching.md)
11. [Backpressure](engineering-fundamentals/backpressure.md)
12. [Time & Clocks](engineering-fundamentals/time-and-clocks.md)
13. [Fault Tolerance](engineering-fundamentals/fault-tolerance.md)

**Next:** continue to [Computer Science](computer-science.md).

## Wiring Examples

- Coroutines → Sync vs Async
- Flow → Backpressure
- Offline Sync → Fault Tolerance
- Feature Flags → Event-Driven Architecture

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

## Learning Order

Start with the building blocks (complexity, sync vs async, latency vs throughput), then move to state and coordination (state machines, queues, time & clocks), then to operational concerns (caching, backpressure, fault tolerance).

## Topics

- [Complexity Analysis](engineering-fundamentals/complexity-analysis.md) — canonical owner; `computer-science/big-o.md` cross-references
- [Latency vs Throughput](engineering-fundamentals/latency-vs-throughput.md)
- [Sync vs Async](engineering-fundamentals/sync-vs-async.md)
- [Coupling vs Cohesion](engineering-fundamentals/coupling-vs-cohesion.md)
- [Immutability](engineering-fundamentals/immutability.md)
- [State Machines](engineering-fundamentals/state-machines.md) — canonical owner; all application FSMs link here
- [Queues](engineering-fundamentals/queues.md)
- [Event-Driven Architecture](engineering-fundamentals/event-driven-architecture.md)
- [Caching](engineering-fundamentals/caching.md)
- [Serialization](engineering-fundamentals/serialization.md)
- [Backpressure](engineering-fundamentals/backpressure.md)
- [Time & Clocks](engineering-fundamentals/time-and-clocks.md)
- [Fault Tolerance](engineering-fundamentals/fault-tolerance.md)

## Wiring Examples

- Coroutines → Sync vs Async
- Flow → Backpressure
- Offline Sync → Fault Tolerance
- Feature Flags → Event-Driven Architecture

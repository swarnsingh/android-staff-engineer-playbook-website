# Distributed Systems

## Purpose

The theory underneath every multi-device, multi-server system the mobile client talks to. AirBridge's deterministic resume is an idempotency-and-consistency story — this tree is what makes that story coherent.

## Why It Matters

A mobile engineer who treats the backend as a black box will eventually ship a bug that only manifests under partition or partial failure. Knowing CAP, consistency models, and idempotency at the theory level is what makes you able to reason about those bugs before they ship.

## Learning Order

CAP and consistency models first (the framing), then idempotency and delivery semantics (the most-applied concepts), then advanced topics (vector clocks, CRDTs, consensus).

## Topics

- [CAP Theorem](distributed-systems/cap-theorem.md)
- [Consistency Models](distributed-systems/consistency-models.md)
- [Idempotency](distributed-systems/idempotency.md) — canonical; cross-referenced from AirBridge and Offline Sync
- [Delivery Semantics (at-least-once vs exactly-once)](distributed-systems/delivery-semantics.md)
- [Vector Clocks](distributed-systems/vector-clocks.md)
- [CRDTs](distributed-systems/crdts.md)
- [Consensus Basics](distributed-systems/consensus-basics.md)
- [Distributed Tracing](distributed-systems/distributed-tracing.md) — short stub; canonical is [`observability/distributed-tracing.md`](observability/distributed-tracing.md)

## Anchor

[AirBridge](airbridge.md)'s deterministic resume cross-links heavily into this tree.

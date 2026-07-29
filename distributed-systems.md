# Distributed Systems

## Purpose

The theory underneath every multi-device, multi-server system the mobile client talks to.

## Why It Matters

A mobile engineer who treats the backend as a black box will eventually ship a bug that only manifests under partition or partial failure. Knowing CAP, consistency models, and idempotency at the theory level is what makes you able to reason about those bugs before they ship.

## What This Folder Helps You Do

- Reason about the backend guarantees your mobile app depends on: consistency, ordering, retries, deduplication, replication, and conflict resolution.
- Design mobile flows that behave correctly under partitions, reconnects, duplicate submissions, stale reads, long-offline clients, and multi-device edits.
- Translate distributed-systems theory into client contracts: idempotency keys, monotonic reads, sync tokens, vector clocks, CRDTs, and server-owned convergence.
- Push backend/API discussions beyond "call this endpoint" toward explicit correctness, availability, and recovery guarantees.

## Guided Reading Sequence

Prerequisites: [Engineering Fundamentals](engineering-fundamentals.md), especially state machines, queues, time, and fault tolerance. Read framing before conflict-resolution mechanisms.

1. [CAP Theorem](distributed-systems/cap-theorem.md)
2. [Consistency Models](distributed-systems/consistency-models.md)
3. [Idempotency](distributed-systems/idempotency.md) — canonical; cross-referenced from Offline Sync.
4. [Delivery Semantics](distributed-systems/delivery-semantics.md)
5. [Mobile Client Consistency Contracts](distributed-systems/mobile-client-consistency-contracts.md)
6. [Vector Clocks](distributed-systems/vector-clocks.md)
7. [CRDTs](distributed-systems/crdts.md)
8. [LWW vs CRDT](distributed-systems/lww-vs-crdt.md)
9. [Consensus Basics](distributed-systems/consensus-basics.md)
10. [Replication & Leader Election](distributed-systems/replication-and-leader-election.md)
11. [Streaming Logs & Partitioning](distributed-systems/streaming-logs-partitioning.md)
12. [Distributed Tracing](distributed-systems/distributed-tracing.md) — bridge file; canonical treatment lives under Observability.

**Next:** continue to [Backend for Mobile](backend-for-mobile.md).

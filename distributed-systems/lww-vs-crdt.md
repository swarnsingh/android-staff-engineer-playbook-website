# ADR 008 — Last-Write-Wins vs CRDTs for Offline Sync Conflict Resolution

**Status:** Accepted
**Date:** *replace with actual decision date*
**Deciders:** *replace with actual deciders*

---

## Context

We are building an offline-first feature where users can mutate shared state from any device while disconnected, and those mutations must reconcile when devices reconnect. The mutations are not strictly user-private (a user-only note app would be trivially LWW per device); multiple devices, possibly multiple users, can edit the same logical entity concurrently.

The relevant constraints:

- **Concurrency model.** Two writes to the same field from different devices, neither aware of the other, may happen during the offline window.
- **Convergence requirement.** After all devices come online and replicate their changes, every replica must arrive at the same final state. No "split brain" allowed.
- **Causality.** Most mutations are independent of each other (different fields, different entities), but a small fraction are causally related (e.g., "create item X" then "rename X to Y").
- **Mobile constraints.** Sync metadata is sent over slow, costly cellular networks. Per-mutation metadata size matters. Local computation cost matters (older devices have limited CPU).
- **User expectation.** Users expect their last action to "win" when they consciously edit, but they expect *both* edits to be preserved when two concurrent edits genuinely disagree.

The choice is between two broad strategies for resolving concurrent conflicting writes:

1. **Last-Write-Wins (LWW)** — the write with the latest timestamp (or vector clock, or hybrid logical clock) is the surviving value. Earlier concurrent writes are dropped.
2. **Conflict-Free Replicated Data Types (CRDTs)** — data structures designed so that concurrent operations produce the same merged result regardless of order, by construction. No information is dropped.

There is also a hybrid path — LWW for most fields with CRDTs for specific collaborative fields — that we evaluate.

---

## Problem

What conflict-resolution strategy should the offline sync layer use for shared mutable state?

---

## Alternatives

### Last-Write-Wins with wall-clock timestamps

Each write carries a wall-clock timestamp. On merge, the value with the highest timestamp wins.

- **Pros:** dead simple to implement; tiny metadata (one timestamp per write); trivial to reason about; matches user mental model in most cases ("my last action wins").
- **Cons:** depends on synchronized clocks — wall clocks across devices drift, can be set wrong by the user, and have no causal ordering; ties (same timestamp from two devices) need a tie-breaker; some legitimate concurrent edits are silently dropped; offers no protection when one device's clock is wildly wrong.

### Last-Write-Wins with Hybrid Logical Clocks (HLC)

Each write carries an HLC timestamp (physical time + logical counter, see [`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md)). HLC respects causal ordering — if A causally precedes B, A's HLC < B's HLC, even if their physical clocks disagree.

- **Pros:** still simple to implement; metadata is small (a few extra bytes per write for the logical counter); preserves causality so "A then B" is never reordered; tolerant to bounded clock skew.
- **Cons:** still drops information on concurrent edits — the "losing" write is gone forever; still requires a tie-breaker for genuinely concurrent edits (typically the device ID); HLC doesn't *detect* concurrency, just respects causality.

### State-based CRDTs (e.g., LWW-Register, OR-Set, RGA for text)

Each data type is replaced with a CRDT that mathematically guarantees deterministic merges. Examples: an LWW-Register stores both timestamp and value; a 2P-Set tracks adds and removes separately; an OR-Set assigns unique tags to additions so adds and concurrent removes can be reconciled.

- **Pros:** mathematically guaranteed convergence with no information loss; handles arbitrary concurrent edits correctly; well-studied; libraries exist (Yjs, Automerge, Y-CRDT).
- **Cons:** metadata grows per operation — large state when many writes accumulate; some CRDTs (especially text/RGA) carry per-character metadata; merge complexity is type-specific (each data type needs its own CRDT); some CRDT semantics (e.g., 2P-Set's "you can't re-add after removing") surprise users.

### Operation-based CRDTs (CmRDTs)

Instead of merging full states, operations are propagated and replayed in any causally-consistent order to produce the same result.

- **Pros:** smaller per-message payload than state-based; precise semantics; popular for collaborative text editing (OT/Yjs).
- **Cons:** require reliable causal broadcast of every operation — losing an operation breaks convergence; not naturally offline-tolerant unless paired with persistent buffers; harder to retrofit onto an existing REST-style backend.

### Hybrid: LWW with HLC for most fields, CRDTs for genuinely collaborative ones

Use HLC-LWW as the default for fields where last-write-wins matches the user mental model (e.g., "name", "status", "priority"). Use specific CRDTs only for fields that are genuinely collaborative (e.g., shared lists, text editing).

- **Pros:** keeps the common case simple; uses CRDT complexity only where it's worth it; metadata size is bounded for non-CRDT fields.
- **Cons:** two strategies in one codebase; team must decide per-field which strategy applies; harder to explain to new engineers; field-by-field merges complicate the schema model.

---

## Decision

**Hybrid: HLC-LWW as the default conflict-resolution strategy, with specific CRDTs for genuinely-collaborative data types.**

For 90%+ of the fields (status, priority, assignee, name, due date, single-user-owned fields), the user mental model is "my last change wins." HLC-LWW gives us:

- Causally-correct ordering (no "A then B" reordering bug).
- Small per-write metadata (HLC is ~12-16 bytes).
- A deterministic tie-break for the rare case of identical HLCs from concurrent devices (device ID lexicographic order).

For specific collaborative data types — shared task lists, comment threads, shared text fields — we use the appropriate CRDT (OR-Set for the list, log-based CRDT for the comment thread, RGA or Yjs for collaborative text). These types pay the CRDT cost where the collaborative semantics demand it.

---

## Consequences

**Positive**

- The default path is simple: every mutation carries an HLC, every merge picks the higher HLC, ties broken by device ID. Easy to implement, easy to debug.
- HLC keeps clock-skew problems bounded — devices with wildly wrong wall clocks are quarantined (see HLC's drift-detection mechanism), not silently corrupting data.
- Per-field CRDT use is localized. Engineers building new features default to HLC-LWW and only adopt a CRDT when they specifically need collaborative semantics for that field.
- We do not pay the CRDT complexity tax across the entire schema. Metadata stays small for the bulk of the data.

**Negative**

- We will lose data on genuinely-concurrent conflicting edits to non-CRDT fields. The "losing" write is dropped silently. The mitigation is a per-field activity log so users can audit recent changes and recover via undo if a critical edit was lost.
- Adding a CRDT to a previously-LWW field is a schema migration with backward-compatibility implications.
- Engineers need to be trained to recognize "is this field truly LWW-acceptable, or is it secretly collaborative?" PR review and a small architecture-doc checklist help.
- Two conflict strategies in one codebase is more cognitive load than one. We accept the tradeoff for the implementation simplicity savings.

---

## Tradeoffs

We accept:

- **Some lost concurrent edits.** For non-CRDT fields, two concurrent writes will deterministically resolve to one — the other is gone. This matches user expectation for most fields (name, status) but is wrong for genuinely-collaborative semantics, which is why we use CRDTs there.
- **Implementation cost of HLC.** Every device must track its HLC, persist it across restarts, and merge it on every received write. The cost is small but pervasive.
- **Field-by-field strategy decisions.** Adding a field requires asking "LWW or CRDT?" The answer is usually obvious, but the question is not optional.

We give up:

- **Universal mathematical guarantees of CRDT-style convergence.** If we were building Google Docs (every byte is collaborative), we would adopt CRDTs universally. For our use case, where most fields are single-owner-at-a-time, the simpler LWW path wins.
- **Full-state CRDT semantics on most fields.** A non-CRDT field can't, for example, support "concurrent additions to a list" — adopt OR-Set if you need that.

---

## Future Revisit Conditions

Re-open this decision if any of the following becomes true:

- The fraction of CRDT fields exceeds *replace with threshold* of the schema, indicating that LWW was the wrong default and most data is actually collaborative.
- We observe a measurable rate of user complaints about lost concurrent edits beyond what an activity-log/undo flow can mitigate.
- HLC's quarantine mechanism is triggered frequently in production, indicating clock-drift problems beyond what we expected.
- A future product direction (e.g., realtime collaborative editing across the entire schema) requires us to converge on CRDTs universally, at which point LWW's information-loss tradeoff becomes unacceptable.
- Sync metadata size approaches a problem on cellular networks because of CRDT-field accumulation (in which case we evaluate operation-based CRDTs or state-pruning strategies).

---

## Related

- [`../distributed-systems/consistency-models.md`](../distributed-systems/consistency-models.md) — eventual consistency, causal consistency, strong consistency.
- [`../distributed-systems/crdts.md`](../distributed-systems/crdts.md) — canonical treatment of CRDT families.
- [`../distributed-systems/vector-clocks.md`](../distributed-systems/vector-clocks.md) — vector clocks as an alternative to HLC.
- [`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md) — physical, monotonic, and logical clocks; HLC mechanics.
- [`../mobile-system-design/offline-sync.md`](../mobile-system-design/offline-sync.md) — broader offline-sync architecture context.
- [`../mobile-system-design/collaborative-editing.md`](../mobile-system-design/collaborative-editing.md) — when CRDTs become the dominant choice.
- [`../patterns/saga.md`](../patterns/saga.md) — sagas as an alternative for multi-step distributed operations.

---

## References

- Marc Shapiro et al., *"Conflict-Free Replicated Data Types"* (2011) — the founding CRDT paper.
- Sandeep Kulkarni et al., *"Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases"* (2014) — the HLC paper.
- Martin Kleppmann, *Designing Data-Intensive Applications* (2017) — Chapter 5 on replication, Chapter 9 on consistency and consensus.
- Yjs documentation (https://docs.yjs.dev/) — practical CRDT library widely used for collaborative editing.
- Automerge documentation (https://automerge.org/) — alternative CRDT library with broader data structure support.

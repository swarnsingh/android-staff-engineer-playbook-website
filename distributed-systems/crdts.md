# CRDTs

## Overview

A **Conflict-free Replicated Data Type (CRDT)** defines updates and merge rules so replicas with the same updates reach the same state under the synchronization contract. This can avoid coordination for supported operations. Convergence does not preserve every user intent: an LWW register discards losing writes, and an add-wins set can restore an item another user removed. Applications choose the semantics, authorize updates and enforce any additional business invariants.

---

## Why It Exists

In eventually consistent systems, concurrent writes to the same data create conflicts. Traditional approaches resolve conflicts after the fact: last-writer-wins (which loses data), application-specific merge functions (which are error-prone), or user intervention (which is slow). Each approach has failure modes that compound at scale.

What was broken before CRDTs: every eventually consistent system needed a bespoke conflict-resolution strategy for every data type. Shopping carts used set union. Counters used "just pick the bigger number" (which is wrong under concurrent increments). Text editors used operational transformation (OT), which is notoriously complex. Each strategy was hand-designed, hand-tested, and hand-debugged.

CRDTs define deterministic concurrency semantics so replicas with the same updates agree. Agreement does not guarantee that every user intent survives or that business invariants hold. The trade-off: you can only represent data that has a commutative, associative, idempotent merge function — but a surprising number of useful data types fit this constraint.

---

## Historical Context

1. **Bayou (1995).** One of the first systems to explore conflict resolution in replicated data, using application-specific merge functions. Ahead of its time but manual.
2. **Operational Transformation (1989-2000s).** Used by Google Docs for collaborative text editing. Correct but complex — the number of edge cases grows combinatorially with the number of operation types.
3. **CRDTs formalized (2011).** Marc Shapiro, Nuno Preguiça, Carlos Baquero, and Marek Zawirski published *Conflict-free Replicated Data Types*, defining the two CRDT families (state-based and operation-based) and proving convergence.
4. **Riak (2012+).** One of the first production databases to offer CRDTs (counters, sets, maps, flags) as first-class data types.
5. **Redis CRDT module (2018).** Redis Enterprise added CRDT-based active-active geo-replication.
6. **Automerge, Yjs (2017 onward).** CRDT-based libraries for collaborative editing, making CRDTs practical for text, JSON, and rich documents.
7. **Figma.** A published example of a custom collaboration design inspired by CRDTs.

The arc: manual conflict resolution → algorithmic conflict resolution (OT) → conflict-free by construction (CRDTs).

---

## First Principles

### Two families

**State-based CRDTs (CvRDTs — Convergent)**

Each replica holds the full state. To sync, replicas exchange their complete states and *merge* them. The merge function must be:

- **Commutative:** `merge(A, B) = merge(B, A)`
- **Associative:** `merge(merge(A, B), C) = merge(A, merge(B, C))`
- **Idempotent:** `merge(A, A) = A`

For a state-based CRDT, merge is a least upper bound, local updates are inflationary in that order, and states must eventually propagate. Associativity, commutativity and idempotence alone do not repair lost updates or an invalid update function. There need not be a greatest element.

**Operation-based CRDTs (CmRDTs — Commutative)**

Instead of exchanging full states, replicas broadcast *operations*. The operations must commute: applying them in any order produces the same result. Classic operation-based designs require reliable causal delivery without duplicate application, or an explicit deduplication/idempotent-operation mechanism. At-least-once delivery alone duplicates increments. Yjs document updates have their own idempotent, order-independent contract.

In practice, state-based CRDTs are more common because they work with unreliable networks (you can re-send the state without harm — idempotent merge). Operation-based CRDTs are more efficient (smaller messages) but need stronger delivery guarantees.

### The lattice intuition

A CRDT's state lives on a *semilattice*: a partially ordered set where every pair of elements has a unique *least upper bound* (join). The merge function computes the join.

```text
         {a, b, c}        ← top (all elements present)
        /    |    \
   {a,b}  {a,c}  {b,c}    ← two elements
    / \    / \    / \
  {a}  {b}  {c}            ← one element
    \   |   /
       {}                  ← bottom (empty set)
```

Values can only move up the lattice (toward more information). With eventual dissemination and valid updates, this supports convergence. The visible data can still discard concurrent values (LWW), remove items, or violate an application invariant.

---

## Mental Model

A whiteboard in a meeting room, and everyone has a dry-erase marker.

**Traditional approach:** Everyone writes on the whiteboard simultaneously. When two people write in the same spot, someone has to decide whose text to keep (conflict resolution). This is error-prone and requires coordination.

**CRDT approach:** The whiteboard is append-only. Everyone adds sticky notes. A sticky note, once placed, is never removed (in the basic model). To "see the current state," you collect all the sticky notes. No matter what order you read them, the set of sticky notes is the same. Convergence is guaranteed because the operation (adding a sticky note) is commutative and idempotent.

For deletion: instead of removing a sticky note, you add a *new* sticky note that says "ignore note #7." This is a *tombstone*, and it's why CRDTs often use more space than traditional data structures.

---

## Internal Mechanics

### G-Counter (Grow-only Counter)

The simplest useful CRDT. Each node maintains its own increment count; the total is the sum.

```kotlin
data class GCounter(val counts: Map<String, Long> = emptyMap()) {
    fun increment(nodeId: String): GCounter {
        val current = counts[nodeId] ?: 0
        return GCounter(counts + (nodeId to current + 1))
    }

    fun value(): Long = counts.values.sum()

    fun merge(other: GCounter): GCounter {
        val allKeys = counts.keys + other.counts.keys
        val merged = allKeys.associateWith { key ->
            maxOf(counts[key] ?: 0, other.counts[key] ?: 0)
        }
        return GCounter(merged)
    }
}
```

Merge takes the element-wise max. This works because each node only increments its own entry, so the max of any entry is the correct count for that node.

### PN-Counter (Positive-Negative Counter)

Supports both increment and decrement by using two G-Counters: one for increments (P), one for decrements (N). The value is P - N.

```kotlin
data class PNCounter(
    val positive: GCounter = GCounter(),
    val negative: GCounter = GCounter()
) {
    fun increment(nodeId: String): PNCounter =
        copy(positive = positive.increment(nodeId))

    fun decrement(nodeId: String): PNCounter =
        copy(negative = negative.increment(nodeId))

    fun value(): Long = positive.value() - negative.value()

    fun merge(other: PNCounter): PNCounter =
        PNCounter(
            positive = positive.merge(other.positive),
            negative = negative.merge(other.negative)
        )
}
```

### G-Set (Grow-only Set)

Elements can be added, never removed. Merge is set union.

```kotlin
data class GSet<T>(val elements: Set<T> = emptySet()) {
    fun add(element: T): GSet<T> = GSet(elements + element)

    fun contains(element: T): Boolean = element in elements

    fun merge(other: GSet<T>): GSet<T> = GSet(elements + other.elements)
}
```

### OR-Set (Observed-Remove Set)

Supports both add and remove. Each addition generates a unique tag; a remove marks specific tags as removed. Concurrent add and remove of the same element: add wins (the new add has a fresh tag that wasn't in the remove's set).

```kotlin
data class ORSet<T>(
    private val adds: Map<T, Set<String>> = emptyMap(),    // element → {unique tags}
    private val removes: Map<T, Set<String>> = emptyMap()  // element → {removed tags}
) {
    fun add(element: T, nodeId: String): ORSet<T> {
        val tag = "$nodeId-${UUID.randomUUID()}"
        val existing = adds[element] ?: emptySet()
        return copy(adds = adds + (element to existing + tag))
    }

    fun remove(element: T): ORSet<T> {
        val currentTags = adds[element] ?: return this
        val removedTags = removes[element] ?: emptySet()
        return copy(removes = removes + (element to removedTags + currentTags))
    }

    fun elements(): Set<T> = adds.filter { (element, tags) ->
        val removedTags = removes[element] ?: emptySet()
        (tags - removedTags).isNotEmpty()
    }.keys

    fun merge(other: ORSet<T>): ORSet<T> {
        val mergedAdds = (adds.keys + other.adds.keys).associateWith { key ->
            (adds[key] ?: emptySet()) + (other.adds[key] ?: emptySet())
        }
        val mergedRemoves = (removes.keys + other.removes.keys).associateWith { key ->
            (removes[key] ?: emptySet()) + (other.removes[key] ?: emptySet())
        }
        return ORSet(mergedAdds, mergedRemoves)
    }
}
```

### LWW-Register (Last-Writer-Wins Register)

The simplest register CRDT. Each write carries a timestamp; the value with the highest timestamp wins. It requires a deterministic total order of unique write stamps. Physical-clock accuracy affects which user intent wins, not convergence itself.

```kotlin
data class WriteStamp(val counter: Long, val writerId: String) : Comparable<WriteStamp> {
    override fun compareTo(other: WriteStamp): Int =
        compareValuesBy(this, other, WriteStamp::counter, WriteStamp::writerId)
}

data class LWWRegister<T>(val value: T, val stamp: WriteStamp) {
    fun merge(other: LWWRegister<T>): LWWRegister<T> = when {
        stamp < other.stamp -> other
        stamp > other.stamp -> this
        else -> {
            require(value == other.value) { "A write stamp must identify one payload" }
            this
        }
    }
}
```

Each writer needs a stable unique ID and a durable, increasing logical counter; advance past observed counters before a causally later write. Never reuse a stamp for another payload. Hash codes are not a valid tie-breaker: distinct strings such as `Aa` and `BB` collide and would make merge depend on argument order.



LWW-Register has the weakest semantics — it can lose concurrent writes. But it's the simplest and most widely used in practice (Cassandra columns are effectively LWW registers).

---

## Architecture

```mermaid
flowchart LR
    subgraph Node1["Node 1"]
        S1[Local CRDT state]
    end
    subgraph Node2["Node 2"]
        S2[Local CRDT state]
    end
    subgraph Node3["Node 3"]
        S3[Local CRDT state]
    end

    S1 -->|"merge"| S2
    S2 -->|"merge"| S3
    S3 -->|"merge"| S1

    Note1["Each node updates locally<br/>Merge on sync<br/>All converge to same state"]
```

```mermaid
flowchart TB
    Op["Local Operation<br/>increment / add / remove"] --> Local[Update Local State]
    Local --> Broadcast[Broadcast State or Op]
    Broadcast --> Peer1[Peer merges]
    Broadcast --> Peer2[Peer merges]
    Peer1 --> Converge[All replicas converge]
    Peer2 --> Converge
```

CRDTs require no coordination layer — no leader, no consensus, no lock server. Each node operates independently; merging happens opportunistically. This makes CRDTs ideal for AP systems where availability is paramount.

---

## Production Example

- **Riak.** Offers built-in CRDTs: counters (PN-Counter), sets (OR-Set), maps (nested CRDTs), flags (LWW boolean), registers (LWW). Used for shopping carts, view counts, feature flags.
- **Redis Enterprise.** CRDT-based active-active geo-replication. Counters and sets replicate across regions without conflicts.
- **Figma.** Uses CRDT-inspired data structures for real-time collaborative design. Each user edits independently; changes merge automatically.
- **Automerge.** A CRDT library for JSON documents. Used by Ink & Switch (the research group) for local-first applications.
- **Yjs.** A high-performance CRDT library for collaborative text editing. Used by many collaborative editors (including some under the hood of Notion-like tools).
- **SoundCloud.** Used CRDTs for counting plays across a globally distributed system.

---

## Android Example

CRDTs are natural for mobile offline-first sync — the phone and server are two replicas that sync when the network is available.

```kotlin
// Membership-only example; quantity/checkout invariants are separate.
data class CartMembership(val items: ORSet<String> = ORSet()) {
    fun add(itemId: String, actor: String) = copy(items = items.add(itemId, actor))
    fun remove(itemId: String) = copy(items = items.remove(itemId))
    fun merge(other: CartMembership) = CartMembership(items.merge(other.items))
}
```

A sync adapter must atomically merge the remote state with the **current** local state, not a copy loaded before the network request. The server endpoint must merge states too; an ordinary replacement `PUT` can erase another device's update. These are application contracts, not properties of HTTP. Persist merge metadata and tombstones with the state.

Quantity needs its own lifecycle and concurrency semantics. Simply attaching a permanent PN-counter to an item resurrects old quantity on remove/re-add and does not prevent negative totals. Checkout still validates price and inventory authoritatively.



However, consider the **CRDT UX implications**: deterministic resolution does not always mean *intuitive* resolution from the user's perspective. For instance, concurrent edits to a text string might interleave characters unexpectedly, or an "add-wins" set might resurrect a deleted item. The UI must carefully present these merged states (e.g., via visual hints or undo stacks) so users understand what happened.

For collaborative features (shared notes, real-time co-editing), libraries like Automerge or Yjs can be used through their JavaScript bindings in a WebView or through native ports.

---

## Tradeoffs

**Advantages**

- **Defined convergence.** Valid updates converge under the synchronization contract; the application still chooses and validates the concurrency semantics.
- **High availability.** No coordination required. Every node can accept writes independently.
- **Partition tolerance.** Nodes can be offline for arbitrary periods and still merge correctly when reconnected.
- **Simplicity of reasoning.** The merge algebra is bounded, but sync still needs durable delivery, atomic persistence, authorization and safe metadata retirement.

**Disadvantages**

- **Limited expressiveness.** Not every data model fits a CRDT. Operations that require global coordination (e.g., "set the value to X only if the current value is Y") are fundamentally non-CRDT.
- **Space overhead.** CRDTs carry metadata (tombstones, unique tags, per-node counters). An OR-Set uses more memory than a plain set.
- **Tombstone accumulation.** Deleted elements are marked, not removed. Without garbage collection, tombstones grow forever.
- **Semantic limitations.** A PN-Counter can go negative. An OR-Set has add-wins semantics (which may not match business requirements). LWW-Register can lose concurrent writes.

**Hidden costs**

- **Garbage collection is hard.** Removing tombstones requires global knowledge (has every replica seen this tombstone?). This is itself a coordination problem — the thing CRDTs were designed to avoid.
- **CRDT choice is a schema decision.** Choosing the wrong CRDT for your data (LWW when you need OR-Set, G-Counter when you need PN-Counter) creates subtle bugs that only appear under concurrency.
- **Testing concurrent scenarios is hard.** Convergence is guaranteed by the math, but the *semantics* of the converged state may not match user expectations.

**When not to use**

- Data that requires strong consistency (bank balances, inventory with strict limits).
- Operations that need compare-and-swap semantics.
- Simple key-value data where LWW is acceptable and CRDT overhead is unwarranted.

---

## Failure Modes

**Tombstone bloat.** Deleted elements accumulate as tombstones. Over months of use, tombstones dominate the data structure's size. Mitigation: periodic garbage collection with a protocol that ensures all replicas have seen the tombstone before removing it.

**Semantic surprise.** A PN-Counter allows negative values (more decrements than increments on one node, before merge). Users don't expect "quantity: -3." Concurrent decrements can leave a permanently negative total. A display clamp does not enforce non-negativity; use coordination or a proven bounded/escrow design when the invariant matters.

**Clock-dependent CRDTs.** LWW-Register depends on timestamps. If clocks are skewed, the "wrong" writer wins. Mitigation: use Hybrid Logical Clocks ([`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md)), or avoid LWW for critical data.

**Merge explosion.** Merging large CRDT states (thousands of tombstones, many concurrent versions) can be slow. Mitigation: compact the state periodically; limit the number of concurrent writers.

**Incorrect merge implementation.** A merge function that violates commutativity, associativity, or idempotence breaks convergence. Mitigation: property-based testing (generate random operation sequences, verify convergence).

---

## Performance Considerations

- **CPU:** Merge is typically O(N) where N is the size of the CRDT state. For large states (big OR-Sets, many tombstones), merge can be the bottleneck.
- **Memory:** CRDTs use more memory than plain data structures due to metadata (tags, tombstones, per-node counters). A G-Counter for 100 nodes uses 100 entries; a plain counter uses 1.
- **Network:** State-based CRDTs exchange the full state on sync. For large states, delta-based CRDTs (sending only changes since the last sync) reduce bandwidth.
- **Storage:** Tombstones accumulate on disk. Without GC, storage grows monotonically.
- **Battery (mobile):** Syncing large CRDT states is expensive. Use delta CRDTs and sync only changed parts.

---

## Reliability Considerations

- CRDTs provide **strong eventual consistency:** if all replicas receive all updates, they converge to the same state. This is a *stronger* guarantee than eventual consistency — it guarantees convergence, not just eventual delivery.
- **No coordination point = no single point of failure.** CRDTs don't depend on a leader, a coordinator, or a consensus protocol. Every node is independently available.
- **Offline resilience.** CRDTs are inherently offline-tolerant. A mobile device offline for days can merge correctly when it reconnects.

---

## Security Considerations

- **Byzantine nodes.** CRDTs assume honest participants. A malicious node that sends invalid states (e.g., a G-Counter with decremented values) can corrupt the merged result. Mitigation: validate CRDT state on receive; reject invalid states.
- **PII in tombstones.** Deleted data persists as tombstones. If the data contains PII, tombstones must be encrypted or purged with the same rigor as live data.
- **Metadata leakage.** CRDT metadata (node IDs in counters, unique tags in OR-Sets) reveals information about which nodes performed which operations. Anonymize if needed.

---

## Observability

- **Convergence time.** How long after a write does every replica reflect it? Histogram per data type.
- **State size.** Total size of each CRDT instance (including metadata and tombstones). Alert on growth beyond expected bounds.
- **Tombstone count.** Number of tombstones per CRDT instance. Monitor for accumulation.
- **Merge latency.** Time spent in merge operations. Alert if merge becomes a bottleneck.
- **Delta size.** For delta CRDTs, the size of each delta sent. Should be small relative to total state.

Canonical: [`../observability/metrics.md`](../observability/metrics.md).

---

## Staff Engineer Thinking

**CRDTs are a design choice, not a library choice.** The decision to use a CRDT constrains your data model. Make this decision early, understand the semantic implications, and document them. "We use an OR-Set for the shopping cart, which means concurrent add-and-remove resolves in favor of add" is a design decision that product and engineering must agree on.

**Start with the simplest CRDT that fits.** G-Counter, PN-Counter, LWW-Register, and G-Set cover a surprising number of use cases. Reach for OR-Set or CRDT maps only when you genuinely need add/remove semantics.

**Plan for garbage collection from day one.** Tombstone GC is the hardest operational problem in CRDT systems. Design the protocol before you ship, not after tombstones fill your database.

**Use CRDTs for the data that benefits most.** Not every piece of data needs conflict-free replication. Use CRDTs for data that's written concurrently and must converge (counters, collaborative documents, offline sync). Use traditional approaches for data that's rarely concurrent or where LWW is fine.

**Property-based testing is non-negotiable.** CRDT correctness depends on mathematical properties (commutativity, associativity, idempotence). Property-based tests (generate random operation sequences, verify convergence) are the only reliable way to validate these.

---

## Common Misconceptions

**"CRDTs solve all consistency problems."** They solve *convergence*. They don't solve ordering, global constraints, or application-level invariants (e.g., "stock cannot go below zero").

**"CRDTs are too complex for mobile."** The simplest CRDTs (G-Counter, LWW-Register) are trivial to implement. Libraries like Automerge handle complex cases.

**"Last-writer-wins is a CRDT."** An LWW register is a CRDT with overwrite semantics. CRDTs promise agreement under their assumptions, not preservation of every concurrent value.

**"CRDTs don't need a network."** They work *without* a reliable network (no consensus needed), but they still need *some* communication to sync. Without sync, replicas diverge forever.

**"CRDTs are only for distributed databases."** They're equally useful for local-first mobile apps, collaborative editors, multiplayer games, and any system where multiple writers update shared state independently.

---

## Probing Questions

1. Explain the difference between a state-based CRDT and an operation-based CRDT. When would you choose each?
2. Why must a state-based CRDT's merge function be commutative, associative, and idempotent? What breaks if any property is violated?
3. Implement a G-Counter. Why can't a plain counter be a CRDT?
4. An OR-Set uses "add wins" semantics for concurrent add-and-remove. Why? What would happen with "remove wins"?
5. How do you garbage-collect tombstones in a CRDT? Why is this hard?
6. A PN-Counter shows a value of -2. Is this a bug? How would you prevent it from being user-visible?
7. Compare CRDTs and vector clocks as approaches to handling concurrent writes. How do they complement each other?
8. You're building an offline-first collaborative note-taking app. Which CRDTs would you use for the note content, the tag list, and the view count?
9. Explain delta CRDTs. Why are they more efficient than state-based CRDTs for network sync?
10. When would you choose a CRDT over a server-arbitrated conflict resolution strategy?

## Answer Key

1. **Explain the difference between a state-based CRDT and an operation-based CRDT. When would you choose each?**
   State-based CRDTs exchange their full state and merge it; best for unreliable networks. Operation-based CRDTs broadcast only operations; they require a reliable, causally-ordered transport but use less bandwidth.
2. **Why must a state-based CRDT's merge function be commutative, associative, and idempotent? What breaks if any property is violated?**
   Commutativity (order doesn't matter), associativity (grouping doesn't matter), and idempotency (duplicates don't matter). If any are violated, different replicas merging in different orders or with duplicate messages will diverge.
3. **Implement a G-Counter. Why can't a plain counter be a CRDT?**
   A G-Counter is a map of node IDs to their local increment counts. A plain counter isn't a CRDT because concurrent increments (`+1` on two nodes starting at 0) would both set the value to 1, losing an increment when merged.
4. **An OR-Set uses "add wins" semantics for concurrent add-and-remove. Why? What would happen with "remove wins"?**
   "Add wins" ensures that if one node adds an item while another concurrently removes it, the item remains. If it were "remove wins", an item might instantly disappear immediately after a user adds it, creating poor UX.
5. **How do you garbage-collect tombstones in a CRDT? Why is this hard?**
   Garbage collection requires ensuring every replica has seen the tombstone before you can safely remove it. This is hard because it requires global coordination in a system designed to be coordination-free.
6. **A PN-Counter shows a value of -2. Is this a bug? How would you prevent it from being user-visible?**
   A PN-counter permits more decrements than increments, even after full convergence. Clamping the display hides the negative value; it does not prevent overspending. Use an appropriate bounded-counter/escrow protocol or coordinated authorization.
7. **Compare CRDTs and vector clocks as approaches to handling concurrent writes. How do they complement each other?**
   Vector clocks detect concurrent updates and identify conflicts for the application to resolve. CRDTs define deterministic concurrency semantics and converge when their update/delivery assumptions hold. That resolves replica disagreement, not necessarily a conflict between user intentions.
8. **You're building an offline-first collaborative note-taking app. Which CRDTs would you use for the note content, the tag list, and the view count?**
   Note content: text CRDT (like Automerge or Yjs). Tag list: OR-Set (to add/remove tags). View count: G-Counter or PN-Counter (if views can be removed).
9. **Explain delta CRDTs. Why are they more efficient than state-based CRDTs for network sync?**
   Delta CRDTs only send the state that has changed since the last sync (the delta) rather than the entire state structure, vastly reducing network payload sizes.
10. **When would you choose a CRDT over a server-arbitrated conflict resolution strategy?**
    When high availability, offline capability, and guaranteed convergence without manual conflict resolution are strictly required, such as in real-time collaborative editing or mobile offline-first sync.

---

## Further Reading

- [Preguiça, Baquero and Shapiro: CRDT definitions and synchronization models](https://arxiv.org/abs/1805.06358).
- [Yjs document-update contract](https://docs.yjs.dev/api/document-updates).


In this repository:

- [`vector-clocks.md`](vector-clocks.md) — causal/concurrency detection (vector clocks) versus defined merge semantics (CRDTs).
- [`consistency-models.md`](consistency-models.md) — CRDTs provide strong eventual consistency, a precise point on the consistency spectrum.
- [`cap-theorem.md`](cap-theorem.md) — CRDTs are AP-native: available during partitions, consistent after.
- [`delivery-semantics.md`](delivery-semantics.md) — state-based synchronization must eventually disseminate updates; operation-based designs must meet their ordering and duplicate-delivery requirements.
- [`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md) — LWW-Register depends on clock quality.
- [`../reference-architectures/offline-first-app.md`](../reference-architectures/offline-first-app.md) — CRDTs as the foundation for offline-first sync.
- [`../mobile-system-design/collaborative-editing.md`](../mobile-system-design/collaborative-editing.md) — CRDTs vs OT for collaborative editing.

External:

- Marc Shapiro et al., *Conflict-free Replicated Data Types* (2011). The foundational paper.
- Martin Kleppmann and Alastair Beresford, *A Conflict-Free Replicated JSON Datatype* (2017). The Automerge paper.
- Nuno Preguiça et al., *CRDTs: Making δ-CRDTs Delta-Based* (2018). Delta CRDTs for efficient sync.
- Ink & Switch, *Local-First Software* (2019). The manifesto for CRDT-based local-first applications.
- The Automerge documentation (automerge.org). The most accessible practical introduction to CRDTs.

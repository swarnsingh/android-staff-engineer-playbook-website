# LWW Registers vs Richer CRDT Semantics

## Decision Context

An LWW register is itself a CRDT when it has a deterministic total order of unique write stamps. The useful choice is which concurrency semantics preserve the product's intent: overwrite a field, merge membership, accumulate operations, retain alternatives, or ask a user. This is a reusable comparison, not an accepted decision for an unspecified project.

See [CRDT mechanics](crdts.md) and [vector clocks](vector-clocks.md) for the algorithms. A vector clock is a partial causal order, not an LWW timestamp: concurrent vectors need another resolution policy.

## Decision Criteria

Decide which concurrent intent may be discarded, whether a business invariant needs coordination, the supported offline lifetime, available metadata/storage, library maturity and the team's recovery burden. Keep the existing representation if its measured conflict behavior already meets the product contract.

## Comparison Matrix

| Option | Concurrent result | Main cost | Fits when |
|---|---|---|---|
| LWW register | One ordered winner | Lost-edit recovery and clock/identity discipline | Overwrite semantics are accepted |
| OR-set / counter | Type-defined membership or totals | Metadata and safe retirement; business invariants remain | Those operation semantics match the feature |
| Collaborative text / alternatives | Merged text or retained conflicts | More history, migration and UX work | Concurrent authors must retain/recover intent |
| Keep current model | Existing behavior | Existing conflict and support cost | Evidence shows the contract is already met |

## Options

### LWW register

Pick the maximum unique write stamp. The stamp can combine logical or hybrid time with a stable writer ID. Every retry of one write must retain its identity; never assign the same stamp to different values. A hash of the value is not a collision-free tie-breaker.

LWW is compact and straightforward when overwriting concurrent edits is acceptable. It can discard a legitimate edit from another device. A wall clock does not establish which action a user intended to take last; skew can make an old action win. The same user on two offline devices still creates concurrency.

Hybrid logical clocks preserve causal order when send/receive updates are implemented correctly. They do not detect concurrency, recover overwritten values, or quarantine bad clocks automatically. Drift limits, rejection and recovery are separate policies. Persist clock state and advance it past observed values before issuing a causally later write.

### Membership and counter CRDTs

An OR-Set gives a defined add-versus-remove result. A PN-counter preserves increments and decrements under its synchronization contract. Neither makes every business rule automatic: add-wins may resurrect a removed item, and independent decrements can produce a negative total. A display clamp does not enforce inventory or balance constraints.

State-based merge needs a valid semilattice, inflationary local updates and eventual dissemination. Classical operation-based designs need reliable causal delivery and duplicate suppression unless operations are intrinsically idempotent. Use the chosen library's documented contract; Yjs updates, for example, are idempotent and order-independent. OT is a different collaboration technique, not a CRDT subtype.

### Collaborative text or retained alternatives

Use a text CRDT when preserving concurrent edits is part of the feature, or retain conflicting versions for explicit resolution. Convergence is not a promise that the merged sentence matches either author's intent. Undo, attribution and conflict presentation remain product work.

## Default Recommendation

For a field whose concurrent value may be discarded, consider an LWW register with an audit/recovery path appropriate to its value. For shared membership, counters or text, evaluate a data type whose documented concurrency semantics match the feature. For money, permissions or workflow invariants, use authoritative validation or coordination where required; changing the merge function does not remove that requirement.

A hybrid schema is reasonable, but document each field's semantics. There is no evidence for a universal percentage of fields that should use LWW. Names, assignees and status can be high-value edits in one product and replaceable preferences in another.

## Failure Modes and Hidden Costs

- **Metadata:** registers are usually compact; sets and text can retain tags, history or tombstones. Exact size depends on encoding and garbage collection.
- **Recovery:** LWW converges by choosing one value. Keeping history improves recovery but adds storage, privacy and retention work.
- **Migration:** moving from replacement to operation/state merge needs old-client compatibility, snapshot conversion and a protocol version boundary.
- **Transport:** replacement PUT is not a CRDT merge endpoint. Both client and server must preserve metadata and merge against current state atomically.
- **Retirement:** do not discard tombstones or actor history merely because they are old. A supported offline device must not resurrect deleted data; define replica retirement or a reset contract.

## Migration and Reversibility

Introduce versioned envelopes before changing representation. Convert a known snapshot, preserve supported older-client behavior at the server boundary, and stage by capability. Do not allow a legacy replacement writer to erase CRDT metadata. Reversing to a scalar can discard history needed to merge offline replicas; define retirement/reset and user recovery before that transition.

## Staff Engineer Review

Test duplicate delivery, out-of-order updates, concurrent add/remove, remove/re-add, actor restart and clock skew. Check algebraic properties as well as user-visible outcomes. Revisit the choice when lost-edit reports exceed the agreed recovery contract, metadata exceeds measured budgets, or collaboration changes the semantics. A good merge proof and property tests complement each other; neither replaces product review.

## Probing Questions

1. Why is LWW versus CRDT a misleading binary choice?
2. When is retaining an existing LWW field reasonable?
3. Can an HLC prove that two edits were concurrent?
4. Why does migrating an OR-set back to a plain set require an offline-replica plan?

## Answer Key

1. An LWW register is a CRDT with overwrite semantics; compare the supported concurrency semantics rather than the label.
2. When discarded concurrent intent is acceptable and measured support/recovery costs meet the product's contract. New collaboration or lost-edit evidence can change the choice.
3. No. Correct HLC updates preserve causal order, but ordered stamps do not prove causation; use causal metadata when detection matters.
4. Removing tags/tombstones can let an old replica resurrect deleted membership or erase newer updates. Retire incompatible writers or require a supported reset/migration boundary.

## Related

- [`../distributed-systems/consistency-models.md`](../distributed-systems/consistency-models.md) — eventual consistency, causal consistency, strong consistency.
- [`../distributed-systems/crdts.md`](../distributed-systems/crdts.md) — canonical treatment of CRDT families.
- [`../distributed-systems/vector-clocks.md`](../distributed-systems/vector-clocks.md) — vector clocks as an alternative to HLC.
- [`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md) — physical, monotonic, and logical clocks; HLC mechanics.
- [`../mobile-system-design/offline-sync.md`](../mobile-system-design/offline-sync.md) — broader offline-sync architecture context.
- [`../mobile-system-design/collaborative-editing.md`](../mobile-system-design/collaborative-editing.md) — when CRDTs become the dominant choice.
- [`../patterns/saga.md`](../patterns/saga.md) — sagas as an alternative for multi-step distributed operations.

---

## Further Reading

- [Preguiça, Baquero and Shapiro: CRDT concurrency and synchronization models](https://arxiv.org/abs/1805.06358).
- [Original HLC paper](https://cse.buffalo.edu/tech-reports/2014-04.pdf).
- [Yjs document update guarantees](https://docs.yjs.dev/api/document-updates).

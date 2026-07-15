# Mobile Client Consistency Contracts

## Overview

Consistency is a product contract. Users do not care whether the backend is leaderless, quorum-based, or eventually consistent; they care whether their action appears to work and whether the app explains uncertainty honestly.

This chapter translates distributed consistency models into mobile API contracts.

## Why It Matters

Backend teams reason in consistency models; product teams reason in user promises; the mobile client is where the two meet — and where the gap between them ships as a bug.

- When the contract is **implicit**, the client discovers the backend's real guarantees one production incident at a time: the stale read after profile edit, the push that beats the fetch, the retry that double-posts.
- When the contract is **explicit**, each feature's client strategy becomes a table lookup: this flow needs read-your-writes, so it persists a commit token; that flow is eventual, so it renders optimistically and reconciles.

The Staff-level move is refusing to let "what happens when the user does X twice, offline, during a failover" be discovered in production. Every one of those answers is designable — but only if the guarantee is written down *per feature*, because "the API is eventually consistent" is not one fact; it's a different fact per endpoint.

## Mental Model

A consistency contract is a **service-level agreement between the backend and the user's thumb**, with the client as the enforcing middleman.

Think of the client as a **bank teller working from a branch ledger**:

- Head office (the backend) owns the master ledger; the branch ledger (local DB) syncs on a schedule.
- For a balance inquiry, the teller may quote the branch ledger — mostly right, occasionally stale, instantly available (eventual consistency).
- For a withdrawal, the teller must confirm with head office before handing over cash (strong confirmation) — no matter how long the phone call takes.
- For a deposit, the teller takes the money, writes a *pending* entry, and gives a receipt (optimistic write + pending state). The receipt number (idempotency key) guarantees the deposit is counted exactly once even if the paperwork is submitted twice.

A teller who treats every operation like a balance inquiry loses money. One who treats every operation like a withdrawal makes customers queue for hours. Choosing per-operation is the job.

## Common Mobile Guarantees

| Guarantee | Meaning | Mobile example |
|---|---|---|
| Read-your-writes | User sees their own write after it succeeds | Updated profile appears immediately |
| Monotonic reads | User does not go backward in time | Order status does not revert |
| Causal reads | Dependent data appears in cause order | Reply appears after original message |
| Eventual consistency | State converges later | Like count catches up |
| Strong/linearizable read | Read reflects latest committed write | Bank balance after transfer |

Not every feature needs strong consistency. Every feature needs an explicit answer.

## Contract Per Feature

| Feature | Required guarantee | Client strategy |
|---|---|---|
| Payment submit | Idempotent write + strong confirmation | Disable duplicate submit, store idempotency key |
| Profile edit | Read-your-writes | Optimistic local state, server version |
| Feed likes | Eventual | Optimistic count, reconcile later |
| Chat messages | Per-thread order + dedup | client IDs, server sequence |
| Inventory checkout | Strong validation at purchase | Revalidate server-side before commit |
| Collaborative doc | Causal/CRDT/OT semantics | operation IDs and conflict handling |

Two observations Staff engineers act on:

1. **The guarantee column is owned by product as much as backend.** "Can the like count be wrong for a minute?" is a product question; the table forces it to be asked before launch instead of after the incident review.
2. **Each row costs differently.** Strong confirmation costs latency on every use; eventual costs reconciliation logic once. Feature teams tend to ask for stronger guarantees than they need — the table is where that negotiation happens with the costs visible.

## API Fields That Enable Consistency

Strong mobile contracts usually need:

- `idempotencyKey`
- `clientOperationId`
- `serverVersion`
- `etag`
- `updatedAt` from server clock
- `commitToken`
- `syncCursor`
- `conflictReason`
- `retryAfter`
- `isAuthoritative`

If an API response lacks all versioning and identity fields, the client cannot safely reconcile.

This is worth stating as a review rule: **the client can only be as consistent as the fields the API carries.** No client code distinguishes "deleted" from "not yet visible," or "newer" from "concurrent," unless the response encodes it. Missing consistency fields are contract bugs even when every current happy path works — they remove the client's ability to handle the unhappy ones.

## Optimistic UI

Optimistic UI is a consistency bet.

```kotlin
database.withTransaction {
    noteDao.updateTitle(noteId, newTitle, syncState = SyncState.Pending)
    outboxDao.insert(operation)
}
```

Rules:

- Persist optimistic state with pending marker.
- Make retry idempotent.
- Show failure recovery.
- Reconcile with server version.
- Avoid optimistic UI for irreversible/high-value actions unless product accepts risk.

The transaction above is the load-bearing detail: the optimistic write and the outbox entry commit **atomically**. Write them separately and a crash between the two produces either a phantom edit (local change that will never sync) or a ghost operation (sync of a change the user never saw). See [`idempotency.md`](idempotency.md) on atomic capture.

## Monotonic Reads

The app should avoid showing older versions after newer versions.

```kotlin
fun shouldApply(incoming: EntityDto, current: EntityRow?): Boolean =
    current == null || incoming.version > current.version
```

This protects against:

- Replica lag.
- Out-of-order sync batches.
- Push arriving before fetch.
- Cache race between old and new responses.

The subtle prerequisite: `version` must come from a **single authority** (the server), not from device clocks. Client timestamps regress across devices, timezone changes, and clock corrections — the moment two writers timestamp independently you are in [`vector-clocks.md`](vector-clocks.md) territory, and a single integer comparison silently drops writes.

## Conflict UX

Conflict handling is not only a merge algorithm.

Options:

- Server wins.
- Client wins.
- Field-level merge.
- User chooses.
- Keep both copies.
- Reject local write with recovery.

Staff rule: conflict policy must be product-approved for each user-value data type. Silent LWW is rarely acceptable for drafts, money, identity, or collaboration.

The forcing question for product: *"Two devices edited this offline. Which edit survives, and does the user find out?"* Every answer is legitimate for some data type; **not choosing** is the only wrong answer, because the system then chooses for you — usually "whichever request arrived last," which is LWW with extra steps.

## Offline and Reset Contracts

Delta sync needs reset paths.

```json
{
  "error": {
    "code": "SYNC_CURSOR_EXPIRED",
    "resetRequired": true
  }
}
```

Client behavior:

- Stop applying deltas.
- Preserve local outbox.
- Fetch snapshot.
- Rebase or replay pending operations.
- Mark conflicts explicitly.

The ordering is deliberate: **preserve the outbox before touching the snapshot.** The single worst implementation of cursor reset is "wipe local and re-download" — it silently destroys every unsynced user edit. A reset path that loses pending work converts a backend retention decision into user data loss.

## Production Example

**The revert that shook user trust.**

A task app ships optimistic edits with a plain `updatedAt` LWW policy, client-timestamped. A user edits a task on their phone (clock skewed 3 minutes fast), then edits it again on their tablet. Sync runs: the tablet's *newer* edit loses to the phone's *older* one because of the skewed clock. The user watches their latest edit revert in front of them.

No error fired; every service was healthy. The bug is the contract: client clocks were allowed to decide ordering. The fix touched every layer — server assigns `version` on write; clients compare versions, not timestamps; concurrent versions (tablet edited before seeing phone's write) surface a `conflictReason` and a merge UI for task *notes*, while LWW remains for the `done` checkbox, a product-approved distinction. The incident writeup's title became the team's contract rule: *"clocks don't order writes; servers do"* ([`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md)).

## Tradeoffs

- **Optimistic vs confirmed UI:** optimism buys perceived speed and costs reconciliation complexity plus occasional visible rollback. Confirmation buys truth and costs a spinner. The choice is per-action, keyed to reversibility and value — not a global app policy.
- **Strong guarantees vs offline capability:** a flow that demands linearizable reads simply cannot run offline. Requiring strong consistency is *deciding* the feature doesn't work on the subway; someone should make that decision on purpose.
- **Contract richness vs API surface:** every consistency field is backend work, documentation, and client handling. The discipline is adding fields where the feature table demands them — not everywhere (bloat), not nowhere (unfixable clients).

## Testing Consistency

Test scenarios:

- Write succeeds but follow-up read hits stale replica.
- Same mutation retried after timeout.
- Push arrives before entity is visible.
- Delta events arrive out of order.
- Cursor expired while local outbox has pending work.
- Conflict between server delete and local edit.

Use fake backend scripts that deliberately violate happy-path timing.

## Staff Engineer Review Checklist

- Is the consistency guarantee documented per feature?
- Do APIs expose version/idempotency/cursor fields?
- Does optimistic state survive process death?
- Are stale responses rejected by version checks?
- Are conflict policies explicit?
- Does cursor expiration preserve local user work?
- Are push and sync races tested?
- Are irreversible actions confirmed by authoritative server state?
- Are eventual states explained in UI?
- Does telemetry show consistency failures and conflict rates?

## Probing Questions

1.  For a feature you know well, name its consistency guarantee, the API fields that enable it, and the client code that enforces it. Which of the three is missing today?
2.  Why must the optimistic local write and its outbox entry commit in one transaction? Describe the failure mode of each ordering if they're split.
3.  A monotonic-read version check uses `updatedAt` from device clocks. Construct the exact multi-device sequence that loses a user's newest edit.
4.  The sync cursor expires while the outbox holds unsynced edits. Walk through the reset flow that preserves user work, step by step.
5.  Product asks for "instant" UI on an irreversible action (sending money, deleting an account). What do you push back with, and what compromise designs exist?
6.  Which consistency failures should page on-call, which should be dashboards, and what client telemetry distinguishes them?

## Further Reading

- [`consistency-models.md`](consistency-models.md) - formal consistency models.
- [`replication-and-leader-election.md`](replication-and-leader-election.md) - replication lag and failover.
- [`streaming-logs-partitioning.md`](streaming-logs-partitioning.md) - event ordering and cursors.
- [`idempotency.md`](idempotency.md) - retry-safe writes.
- [`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md) - why client clocks cannot order writes.
- [`../android/data-and-di/repository-source-of-truth.md`](../android/data-and-di/repository-source-of-truth.md) - local source-of-truth design.

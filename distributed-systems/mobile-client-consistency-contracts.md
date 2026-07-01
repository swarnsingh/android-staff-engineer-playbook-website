# Mobile Client Consistency Contracts

## Overview

Consistency is a product contract. Users do not care whether the backend is leaderless, quorum-based, or eventually consistent; they care whether their action appears to work and whether the app explains uncertainty honestly.

This chapter translates distributed consistency models into mobile API contracts.

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

## Further Reading

- [`consistency-models.md`](consistency-models.md) - formal consistency models.
- [`replication-and-leader-election.md`](replication-and-leader-election.md) - replication lag and failover.
- [`streaming-logs-partitioning.md`](streaming-logs-partitioning.md) - event ordering and cursors.
- [`idempotency.md`](idempotency.md) - retry-safe writes.
- [`../android/data-and-di/repository-source-of-truth.md`](../android/data-and-di/repository-source-of-truth.md) - local source-of-truth design.

# Replication and Leader Election

## Overview

Replication keeps copies of data on multiple nodes. Leader election decides which node is allowed to coordinate writes, assign log positions, or serve as the primary. Together, they explain many mobile-visible behaviors: stale reads, failover gaps, duplicate writes, read-your-writes failures, and "try again later" errors during backend incidents.

Mobile engineers do not usually implement Raft, but Staff mobile engineers must understand the contracts their clients depend on.

## Replication Models

| Model | Write path | Read behavior | Mobile-visible risk |
|---|---|---|---|
| Single leader | Leader accepts writes, followers replicate | Followers may lag | Stale reads after write |
| Multi-leader | Multiple regions accept writes | Conflicts must be resolved | Last-write-wins data loss |
| Leaderless/quorum | Client/database writes to N replicas | Reads use quorum/repair | Higher latency, partial failures |
| Async replica | Primary commits before replicas catch up | Fast writes, stale reads | User refresh sees old data |
| Sync replica | Commit waits for replica ack | Stronger durability | Slower writes/unavailability |

## Leader Election

Leader election chooses one coordinator among replicas.

Leader responsibilities often include:

- Accepting writes.
- Assigning log offsets.
- Coordinating replication.
- Serving linearizable reads.
- Managing schema/config changes.

Failure mode: split brain. Two nodes both think they are leader and accept writes. Consensus protocols prevent this by requiring a quorum.

## Quorum Rule

For crash-fault tolerant consensus:

```text
N >= 2F + 1
```

A 3-node cluster tolerates 1 failure. A 5-node cluster tolerates 2.

The key property is quorum intersection: any two majorities overlap in at least one node, preventing two conflicting leaders from both committing values.

## Replication Lag

Replication lag is the time between a write committing on the primary and becoming visible on a replica.

Mobile symptoms:

- User edits profile, navigates back, sees old name.
- Checkout succeeds, order history does not show order yet.
- Push says "message received," thread fetch misses it.
- Feed refresh returns old pagination cursor.

Client mitigation:

- Read from leader after critical writes.
- Use read-your-writes tokens.
- Optimistically update local source of truth.
- Show pending/syncing state.
- Use monotonic version or commit timestamp returned by server.

## Read-Your-Writes Token

The server can return a consistency token after a write.

```json
{
  "orderId": "ord_123",
  "commitToken": "region-a:log:882913"
}
```

The client sends it on follow-up reads:

```http
GET /orders/ord_123
X-Min-Commit-Token: region-a:log:882913
```

The backend can route to a replica that has caught up or wait until one does.

## Failover Windows

During leader failover:

- Writes may fail with retryable errors.
- Reads may be stale.
- Idempotency stores may be temporarily unavailable.
- Duplicate requests may arrive after timeout.
- Push notifications may race with replicated data visibility.

Mobile should not treat all 500s as final. It should classify retryable vs terminal failures, preserve user work, and use idempotency keys.

## Mobile Contract Questions

Ask backend teams:

- Are reads after writes linearizable, read-your-writes, or eventually consistent?
- Which endpoints read from replicas?
- Does the response include version, ETag, or commit token?
- What happens during leader failover?
- Are retries safe for mutations?
- Is idempotency scoped globally, per user, or per endpoint?
- Does push fire before or after data is visible to reads?

## Staff Engineer Review Checklist

- Does the client know which flows require read-your-writes?
- Are critical writes idempotent across failover?
- Does UI state model pending vs committed?
- Are stale reads tolerated or retried with a token?
- Are backend retryable errors classified explicitly?
- Does push handling account for replication lag?
- Are conflict/version fields preserved through local storage?
- Are failover scenarios tested with delayed/stale reads?

## Further Reading

- [`consensus-basics.md`](consensus-basics.md) - consensus and leader election mechanics.
- [`consistency-models.md`](consistency-models.md) - read guarantees.
- [`idempotency.md`](idempotency.md) - retry-safe mutations.
- [`mobile-client-consistency-contracts.md`](mobile-client-consistency-contracts.md) - client-facing consistency contracts.

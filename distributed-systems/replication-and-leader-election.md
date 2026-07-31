# Replication and Leader Election

## Overview

Replication keeps copies of data on multiple nodes. Leader election decides which node is allowed to coordinate writes, assign log positions, or serve as the primary. Together, they explain many mobile-visible behaviors: stale reads, failover gaps, duplicate writes, read-your-writes failures, and "try again later" errors during backend incidents.

Mobile engineers do not usually implement Raft, but Staff mobile engineers must understand the contracts their clients depend on.

## Why It Matters

Every "weird" production bug of the form *"the write succeeded but the next screen shows old data"* is a replication story the client didn't account for. When you don't know the backend's replication model:

- You retry non-idempotent writes during failovers and double-charge users.
- You treat replica lag as a client cache bug and "fix" it by breaking your cache.
- You design offline sync against an ordering guarantee the backend never promised.
- You cannot ask the backend team the one question that would have prevented the incident.

The client is the *last replica* in the system — your local database is a follower that receives changes late, out of order, and sometimes twice. Every technique in this file applies to your own sync engine as much as to the backend.

## Mental Model

Think of replication as a **newspaper with regional printing presses**.

- The editor-in-chief (the leader) decides what goes in today's edition and in what order.
- Regional presses (replicas) print copies — some finish minutes after the master copy is set (replication lag).
- A reader in a lagging region sees yesterday's headline after their friend has read today's (stale read).
- If the editor-in-chief disappears, the presses must agree on a replacement before anything new is printed (leader election). Print nothing during the vote (unavailability), or risk two editors publishing conflicting editions (split brain).

The mobile app is a subscriber with an unreliable delivery route: copies arrive late, occasionally duplicated, and the reader must never be shown yesterday's paper after today's.

## Replication Models

| Model | Write path | Read behavior | Mobile-visible risk |
|---|---|---|---|
| Single leader | Leader accepts writes, followers replicate | Followers may lag | Stale reads after write |
| Multi-leader | Multiple regions accept writes | Conflicts must be resolved | Last-write-wins data loss |
| Leaderless/quorum | Client/database writes to N replicas | Reads use quorum/repair | Higher latency, partial failures |
| Async replica | Primary commits before replicas catch up | Fast writes, stale reads | User refresh sees old data |
| Sync replica | Commit waits for replica ack | Stronger durability | Slower writes/unavailability |

The choice is invisible in the API schema but visible in the API *behavior*. Two endpoints returning the same JSON can have completely different staleness characteristics because one reads from the leader and one from a replica pool.

## Leader Election

Leader election chooses one coordinator among replicas.

Leader responsibilities often include:

- Accepting writes.
- Assigning log offsets.
- Coordinating replication.
- Serving linearizable reads.
- Managing schema/config changes.

### Split Brain and Fencing

The defining failure mode is **split brain**: two nodes both believe they are leader and both accept writes. Consensus protocols prevent it by requiring a quorum to elect, and by attaching a monotonically increasing **epoch/term number** to each leadership generation.

**Fencing tokens** carry that protection to the edges of the system: every write a leader issues includes its epoch, and downstream stores reject writes from stale epochs. Without fencing, a paused-then-resumed old leader (GC pause, network partition healing) can overwrite data committed by its successor.

Mobile relevance: the same pattern protects your own sync engine. If two app processes (or a stale WorkManager job) can both flush the outbox, a monotonic generation number on sync sessions prevents a resurrected old worker from clobbering newer state.

### Leases

Most systems combine election with **leases**: the leader holds leadership for a bounded time and must renew before expiry. This bounds how long a dead leader blocks the system, at the price of a mandatory unavailability window — a client-visible period where writes fail retryably. This is why "the API was down for 20 seconds and then everything worked" is often not an incident but a lease expiry doing its job.

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

The client-side obligation is subtle: the token must **survive process death** with the pending state it protects. A token held only in memory disappears exactly when the user backgrounds the app between write and read — which is the window where the stale read happens.

## Failover Windows

During leader failover:

- Writes may fail with retryable errors.
- Reads may be stale.
- Idempotency stores may be temporarily unavailable.
- Duplicate requests may arrive after timeout.
- Push notifications may race with replicated data visibility.

Mobile should not treat all 500s as final. It should classify retryable vs terminal failures, preserve user work, and use idempotency keys.

## Production Example

**The double-charge that wasn't the client's fault (until it was).**

A payment API runs single-leader with async replicas. During a failover:

1. The app POSTs a charge; the dying leader commits it but the ack is lost in the partition.
2. The app times out and retries — against the *new* leader.
3. The new leader hasn't replicated the original charge yet (it was mid-flight), so the idempotency lookup misses, and it charges again.

Whose bug is it? The backend's idempotency store should have been replicated synchronously with the data it protects — but the client also retried a payment without an idempotency key, betting the backend would dedupe. The Staff-level lesson: **the client's retry policy is part of the replication design.** For money, retries carry an idempotency key generated *before* the first attempt and persisted with the pending operation ([`idempotency.md`](idempotency.md)); the backend's contract states explicitly whether dedupe survives failover.

## Tradeoffs

- **Sync vs async replication** is durability vs latency: waiting for replica acks makes writes slower and the system less available during replica failures, but shrinks the window where committed data can be lost or invisible. Backends usually choose per-table or per-endpoint — which is why consistency behavior differs *within* one API.
- **Leader reads vs replica reads** is freshness vs scale: routing all reads to the leader gives linearizability and melts under load; replica reads scale and lag. The practical compromise — read-your-writes tokens on the flows that need them — pushes work onto the client, which is why the client team must be in the room when the contract is designed.
- **Fast failover vs split-brain risk:** aggressive election timeouts shrink unavailability windows but misfire during network blips, causing leadership churn (and client-visible retry storms). Conservative timeouts mean longer "try again later" windows. Neither end is free; the client should tolerate both symptoms.

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

## Probing Questions

1.  A user updates their profile and immediately sees the old value on the next screen. Walk through every layer (client cache, replica lag, CDN) that could cause this and how you'd distinguish them.
2.  Why does `N >= 2F + 1` prevent two leaders from both committing, and what property of majorities does the proof rest on?
3.  What is a fencing token, and where in a *mobile sync engine* would you apply the same idea?
4.  Push notifications for new messages arrive before the message is visible via the fetch API. What replication design causes this, and what are three client strategies to handle it?
5.  The backend offers you a `commitToken` for read-your-writes. What client-side persistence obligations come with using it correctly?
6.  During a leader failover, which client behaviors make the incident worse, and which make it invisible to users?

## Answer Key

1. **A user updates their profile and immediately sees the old value on the next screen. Walk through every layer (client cache, replica lag, CDN) that could cause this and how you'd distinguish them.**
   It could be client cache (app fails to update local DB after write), CDN cache (returning stale edge data), or replica lag (reading from a follower that hasn't caught up). Distinguish by checking DB logs for lag, disabling CDN caching via headers, and verifying the local cache gets invalidated correctly upon a successful write.
2. **Why does `N >= 2F + 1` prevent two leaders from both committing, and what property of majorities does the proof rest on?**
   It prevents two leaders from committing because it ensures quorum intersection: any two majorities must overlap by at least one node. That overlapping node cannot vote for two conflicting leaders in the same epoch.
3. **What is a fencing token, and where in a *mobile sync engine* would you apply the same idea?**
   A fencing token is a monotonically increasing epoch number attached to writes to reject stale leader commands. In mobile sync, attach a generation number to a sync session to prevent an older, resurrected worker from overwriting the state of a newer worker.
4. **Push notifications for new messages arrive before the message is visible via the fetch API. What replication design causes this, and what are three client strategies to handle it?**
   This happens with async replication where the push system reads from the leader but the fetch API routes to a lagging replica. Strategies: read from the leader on push, pass the message payload directly in the push, or poll with a `commitToken` until the replica catches up.
5. **The backend offers you a `commitToken` for read-your-writes. What client-side persistence obligations come with using it correctly?**
   The client must persist the token securely across process death alongside the pending state it protects, rather than just in memory, otherwise restarting the app risks reading stale data.
6. **During a leader failover, which client behaviors make the incident worse, and which make it invisible to users?**
   Worse: aggressive, non-idempotent retries (retry storms) that overwhelm the new leader. Invisible: using idempotency keys, classifying 500s as retryable vs terminal, caching previously fetched data, and showing pending UI states until the failover completes.

---

## Further Reading

- [`consensus-basics.md`](consensus-basics.md) - consensus and leader election mechanics.
- [`consistency-models.md`](consistency-models.md) - read guarantees.
- [`idempotency.md`](idempotency.md) - retry-safe mutations.
- [`mobile-client-consistency-contracts.md`](mobile-client-consistency-contracts.md) - client-facing consistency contracts.
- [`../engineering-fundamentals/time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md) - why "latest write" is harder than it sounds.

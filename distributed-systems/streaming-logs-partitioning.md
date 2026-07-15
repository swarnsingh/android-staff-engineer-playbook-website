# Streaming Logs and Partitioning

## Overview

Modern distributed systems often move data through append-only logs: Kafka topics, Pulsar topics, Kinesis streams, database change logs, outbox tables, and event buses. Partitioning lets these logs scale, but it also changes ordering guarantees.

Mobile engineers see the consequences through feeds, notifications, chat, trading ticks, sync streams, and analytics pipelines.

## Why It Matters

The log is invisible from the client — the API shows you endpoints, not topics. But the log's partitioning choices leak directly into user-visible behavior:

- A read receipt renders before the message it acknowledges.
- An order shows "delivered" then flips back to "shipped" after a refresh.
- A notification deep-links to an entity the read model hasn't materialized yet.

When the client team doesn't know the ordering contract, they either over-trust it (and ship the bugs above) or over-defend against it (and build a full CRDT layer for a feed that only needed per-user ordering). Knowing precisely *what is ordered relative to what* is the difference between a 50-line version check and a quarter of unnecessary conflict-resolution work.

The same model also runs *inside* the app: the offline outbox is an append-only log, Room's changelog-driven Flows are a materialized view, and your sync cursor is a consumer offset. Learn the semantics once, apply them on both sides of the API.

## Mental Model

Think of a partitioned log as a **stadium with many turnstile lines**.

- Each line (partition) is strictly ordered: the people in line 3 enter in line-3 order, guaranteed.
- There is no global order *across* lines: someone who arrived at the stadium last can enter first if their line is short.
- The line you're assigned to is determined by your ticket type (the partition key).
- If everyone with the same ticket type stands in the same line, their relative order is preserved — that's the entire guarantee, and nothing more.

Every mobile-visible ordering bug is someone assuming the stadium has one line when it has many.

## Append-Only Log

An append-only log is an ordered sequence of records.

```text
offset 100: MessageSent(thread=1, id=m1)
offset 101: MessageRead(thread=1, id=m1)
offset 102: MessageSent(thread=2, id=m2)
```

Consumers track offsets and resume from the last processed position. This is the backbone of many "catch up after offline" designs.

## Partitioning

A topic is split into partitions. Each partition has order. The whole topic does not have a single global order.

```text
partition 0: user-1 events -> ordered
partition 1: user-2 events -> ordered
partition 2: user-3 events -> ordered
```

Ordering is guaranteed only within the partition key.

## Choosing Partition Keys

| Use case | Good key | Why |
|---|---|---|
| Chat messages | `threadId` | Preserve order within a thread |
| User sync | `userId` | Per-user stream remains ordered |
| Order updates | `orderId` | State transitions stay ordered |
| Stock ticks | `symbol` | Per-symbol order matters |
| Global feed | shard key | Throughput matters more than total order |

Bad partition keys cause hot partitions or broken ordering.

**Hot partitions** are the throughput side of the tradeoff: partition by `symbol` and the day the market crashes, one symbol carries the entire load on a single partition while others idle. Keys must balance *ordering need* against *load skew* — and load skew is a production incident, not a design-review footnote.

The key decision is also a **product** decision: partitioning chat by `threadId` means two threads can render out of order relative to each other. If product expects the conversation *list* to be globally time-ordered, that ordering must be reconstructed client-side from timestamps — a different guarantee with different failure modes.

## Mobile-Visible Ordering Bugs

- Chat read receipt arrives before message.
- Order "delivered" arrives before "shipped."
- Notification opens detail before entity exists in read model.
- Feed item appears, disappears, then reappears after catch-up.
- Offline sync applies delete before create.

Root causes often include cross-partition ordering assumptions: the receipt and the message traveled different partitions (or different pipelines entirely — push vs sync), and nothing ever promised their relative order.

## Offset vs Cursor vs Version

| Token | Meaning | Mobile use |
|---|---|---|
| Offset | Position in one partition/log | Internal consumers, rarely exposed directly |
| Cursor | Opaque continuation token | Pagination/sync APIs |
| Version | Entity-specific monotonic number | Conflict detection and stale update prevention |
| Watermark | "Processed through time/offset" signal | Catch-up and completeness indicators |

Mobile APIs should expose opaque cursors or entity versions, not Kafka offsets. Exposing raw offsets welds the client to the backend's partition count — the moment the topic is re-partitioned, every persisted client cursor breaks simultaneously. An opaque cursor lets the backend re-shard behind the token.

## At-Least-Once Streams

Streaming systems usually deliver at least once. Consumers must handle duplicates.

Client contract:

- Every event has stable ID.
- Every entity update has version.
- Deletes are tombstones, not silent absence.
- Replays are possible.
- Out-of-order events are either impossible by key or handled by version checks.

```kotlin
fun apply(event: SyncEvent) {
    val currentVersion = dao.versionFor(event.entityId)
    if (event.version <= currentVersion) return
    dao.apply(event)
}
```

That one `if` is the client's entire defense against duplicates *and* reordering within an entity — which is why events carrying versions is a contract requirement, not a nicety. See [`delivery-semantics.md`](delivery-semantics.md) for why exactly-once delivery is not on the menu.

## Compaction and Tombstones

Compacted logs keep the latest value per key. Deletes are represented by tombstones.

Mobile sync implication:

- A missing entity may mean "not sent yet," not "deleted."
- A tombstone explicitly means deleted.
- Tombstones need retention long enough for offline clients to catch up.

If tombstones expire before a client syncs, the server needs a reset/full-resync path.

This retention window is a real product decision: it defines **how long a device can stay offline and still sync incrementally**. A 7-day tombstone retention means the user who returns from a two-week trip gets a full resync — which on a large dataset may mean minutes of spinner and a re-download over metered data. Staff engineers ask for this number explicitly; it rarely appears in API docs.

## Backpressure

Consumers can fall behind. Mobile clients fall behind every time the app is offline.

Design:

- Delta sync with cursor.
- Maximum cursor age.
- Full resync when cursor is too old.
- Batch size limits.
- Compression.
- Idempotent application.
- Progress metadata.

## Production Example

**The disappearing feed item.**

A feed is built from two pipelines: a fast push pipeline (new post → fanout → client) and a slower materialization pipeline (post → read-model builder → feed API). Both consume the same log, but the push consumer runs ahead of the read-model consumer.

1. A post is published; push delivers it and the client inserts it optimistically at the top of the feed.
2. The user pulls to refresh. The feed API's read model hasn't materialized the post yet — the response omits it.
3. The client reconciles "server response = truth" and deletes the post from the local cache. The item vanishes before the user's eyes.
4. Thirty seconds later the read model catches up; the next refresh resurrects the item.

The fix is contract-level, not code-level: the feed API response carries a **watermark** ("materialized through offset/time T"), and the client only deletes locally-known items that are *older than the watermark*. Items newer than the watermark are in the uncertainty window and must be kept. Without the watermark field in the API, the client cannot distinguish "deleted" from "not yet materialized" — no amount of client cleverness recovers information the contract doesn't carry.

## Tradeoffs

- **More partitions vs stronger ordering:** parallelism scales with partition count; ordering shrinks to the key. Choosing the key is choosing which product behaviors are guaranteed and which are best-effort.
- **Longer tombstone retention vs storage cost:** every extra day of retention is storage and compaction work on the backend, but widens the offline window clients can survive without a full resync.
- **Exposing versions/watermarks vs API simplicity:** every consistency field added to the contract is client work to honor — but each omitted one is a class of bugs the client *cannot* fix (see the production example).

## Staff Engineer Review Checklist

- Is ordering guaranteed per entity/user/thread, or only best-effort?
- Is the partition key aligned with the ordering requirement?
- Are event IDs stable for deduplication?
- Do events carry entity versions?
- Are deletes explicit tombstones?
- What happens when a mobile cursor is too old?
- Can the client full-resync safely?
- Are duplicate and out-of-order events tested?
- Are push notifications ordered relative to sync visibility?
- Are stream lag and mobile sync lag observable?

## Probing Questions

1.  Chat is partitioned by `threadId`. What ordering is guaranteed, what isn't, and what does the client have to reconstruct itself?
2.  Why should a mobile sync API never expose raw partition offsets, and what breaks the day it does?
3.  A feed item appears, disappears on refresh, and reappears later. Walk through the two-pipeline race that causes this and the contract field that fixes it.
4.  Tombstone retention is 7 days and your users go offline for weeks. What does the sync protocol need, and what does the UX for it look like?
5.  What makes an event stream safe to replay against a client database — list the minimum contract fields and the client-side check for each.
6.  Your analytics pipeline and your sync pipeline consume the same log but lag differently. What user-visible inconsistencies can this cause, and which ones matter?

## Further Reading

- [`delivery-semantics.md`](delivery-semantics.md) - at-least-once and idempotent consumers.
- [`vector-clocks.md`](vector-clocks.md) - causality and concurrency.
- [`mobile-client-consistency-contracts.md`](mobile-client-consistency-contracts.md) - mobile sync contracts.
- [`../mobile-system-design/offline-sync.md`](../mobile-system-design/offline-sync.md) - offline sync architecture.
- [`../engineering-fundamentals/queues.md`](../engineering-fundamentals/queues.md) - the substrate underneath logs and streams.

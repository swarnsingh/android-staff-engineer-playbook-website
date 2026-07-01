# Streaming Logs and Partitioning

## Overview

Modern distributed systems often move data through append-only logs: Kafka topics, Pulsar topics, Kinesis streams, database change logs, outbox tables, and event buses. Partitioning lets these logs scale, but it also changes ordering guarantees.

Mobile engineers see the consequences through feeds, notifications, chat, trading ticks, sync streams, and analytics pipelines.

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

## Mobile-Visible Ordering Bugs

- Chat read receipt arrives before message.
- Order "delivered" arrives before "shipped."
- Notification opens detail before entity exists in read model.
- Feed item appears, disappears, then reappears after catch-up.
- Offline sync applies delete before create.

Root causes often include cross-partition ordering assumptions.

## Offset vs Cursor vs Version

| Token | Meaning | Mobile use |
|---|---|---|
| Offset | Position in one partition/log | Internal consumers, rarely exposed directly |
| Cursor | Opaque continuation token | Pagination/sync APIs |
| Version | Entity-specific monotonic number | Conflict detection and stale update prevention |
| Watermark | "Processed through time/offset" signal | Catch-up and completeness indicators |

Mobile APIs should expose opaque cursors or entity versions, not Kafka offsets.

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

## Compaction and Tombstones

Compacted logs keep the latest value per key. Deletes are represented by tombstones.

Mobile sync implication:

- A missing entity may mean "not sent yet," not "deleted."
- A tombstone explicitly means deleted.
- Tombstones need retention long enough for offline clients to catch up.

If tombstones expire before a client syncs, the server needs a reset/full-resync path.

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

## Further Reading

- [`delivery-semantics.md`](delivery-semantics.md) - at-least-once and idempotent consumers.
- [`vector-clocks.md`](vector-clocks.md) - causality and concurrency.
- [`mobile-client-consistency-contracts.md`](mobile-client-consistency-contracts.md) - mobile sync contracts.
- [`../mobile-system-design/offline-sync.md`](../mobile-system-design/offline-sync.md) - offline sync architecture.

# Mobile System Design, Offline Sync: possible errors in the original chapter

**Status, 29 October 2026: both findings are resolved at source** by playbook PR #61 (merged as `fe82316`). The website copy of `offline-sync.md` and its `source-snapshot.json` hash were refreshed from that commit; the teaching layer now follows the corrected chapter. The original text below is kept as the record.

These were findings for the owner's review, not approved corrections. Website work never edited the original Markdown, and nothing was added to `content/corrections-*.json`. Under the owner decision of 28 October 2026, published pages carry no review notices, so findings are tracked only here. The teaching layer does not restate either claim.

| ID | Section | Original says | Problem | Evidence |
|---|---|---|---|---|
| OS1 | 7. Deep Dive, write path and push path | The write path calls `workManager.enqueueUniqueWork("push", REPLACE, pushWorkRequest())`. The push path says "`PushWorker` is unique-named so concurrent edits coalesce." | With `ExistingWorkPolicy.REPLACE`, a new request cancels the existing unique work rather than coalescing with it. An edit made while a push runs therefore stops that push; the replacement run retries the outbox. `KEEP` keeps the existing work and ignores the new request, and `APPEND_OR_REPLACE` chains new work after it. | Android Developers, [Manage work](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work): "`REPLACE` existing work with the new work. This option cancels the existing work." |
| OS2 | 4. API Contract, push example and Idempotency | The push example's `delete` op has no `clientId`. Idempotency says "Every `upsert` carries `clientId`." The answer to the follow-up question on duplicates says "Each op has `clientId`." `OutboxEntry` stores a `clientId` per operation, including `DELETE`, and the versioned envelope gives every op an `opId`. | The chapter does not say whether deletes carry an idempotency key on the wire. A retried delete may still be harmless (a tombstone is the same final state), but the contract should say so explicitly. | Internal consistency of `offline-sync.md`, sections 4, 6 and 10 |

## Proposed wording, for owner approval only

- **OS1.** Either change the example to `ExistingWorkPolicy.KEEP` and keep "concurrent edits coalesce", or keep `REPLACE` and write: "`PushWorker` is unique-named with `REPLACE`, so a new edit cancels an in-flight push and the replacement run retries the outbox."
- **OS2.** Add `"clientId"` to the delete op in the push example, and change "Every `upsert` carries `clientId`" to "Every op carries `clientId`". Alternatively, state that deletes are idempotent by tombstone and need no key.

## What the teaching layer says now

- **Step-through.** It does not claim that triggers coalesce. Its two queued ops are illustrative upserts. The kill-mid-push step states its scenario: the push was already persisted WorkManager work. It also names the foreground check and periodic sweep for the case where the enqueue was never persisted.
- **Recap.** It says every op, deletes included, carries a stable `clientId`, and that a foreground check and periodic sweep back up WorkManager. Both follow the corrected chapter.

## Claims the teaching layer makes, and what they were checked against

| Claim | Checked against |
|---|---|
| WorkManager work persists across app restarts and device reboots | Android Developers, [WorkManager guide](https://developer.android.com/topic/libraries/architecture/workmanager) |
| The local data source is the source of truth the UI reads; queued writes are drained by WorkManager | Android Developers, [Build an offline-first app](https://developer.android.com/topic/architecture/data-layer/offline-first) |
| Replay, conflict copy, `Result.retry()` / `Result.success()`, 100-row batches, `TOKEN_EXPIRED` handling, tombstones kept for about 30 days | `offline-sync.md`, sections 4, 6 and 7 |

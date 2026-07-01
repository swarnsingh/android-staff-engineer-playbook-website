# Repository Source of Truth

## Overview

A repository is not a bag of Retrofit and Room calls. In a production Android app, the repository defines the source-of-truth contract for a domain slice:

- What data is canonical locally?
- What data is only a cache?
- What writes are durable?
- How do network responses merge with local state?
- What does the UI observe during offline, stale, conflict, and retry states?

Staff engineers care because most mobile data bugs are ownership bugs. Two layers each believe they own truth, and the user pays with stale screens, duplicated writes, lost drafts, and impossible migrations.

## Source-of-Truth Decision Matrix

| Data | Source of truth | Why |
|---|---|---|
| User-created drafts | Local database until uploaded | Losing local work is unacceptable |
| Server-owned profile | Server, locally cached | Server resolves identity and permissions |
| Read-only catalog | Server, Room cache | Offline/read performance; easy refetch |
| Feature flags | Remote config, memory cache | Needs current server policy |
| Pending mutations | Local outbox | Must survive process death |
| UI filters/sort | SavedStateHandle/DataStore | User preference and restoration |
| Auth token | Secure storage/session manager | Security boundary, not generic repository cache |

The repository should document which category it owns.

## Offline-First Read Pattern

The UI observes local state. Network updates local state.

```kotlin
class ProductRepository(
    private val dao: ProductDao,
    private val api: ProductApi
) {
    fun observeProducts(): Flow<List<Product>> =
        dao.observeProducts()
            .map { rows -> rows.map(ProductRow::toDomain) }

    suspend fun refreshProducts() {
        val response = api.getProducts()
        dao.withTransaction {
            dao.upsertProducts(response.items.map(ProductDto::toRow))
            dao.updateSyncMetadata(SyncMetadata.now())
        }
    }
}
```

This gives the UI a stable contract:

- It can render cached data immediately.
- Refresh failure does not erase existing data.
- Database invalidation drives UI updates.
- Process death does not lose the latest committed cache.

## Network-Bound Resource, Staff Version

The common "NetworkBoundResource" pattern is useful but incomplete. A production repository must also model freshness, partial failure, retries, and sync provenance.

```kotlin
data class ResourceState<T>(
    val data: T,
    val freshness: Freshness,
    val syncStatus: SyncStatus,
    val lastSuccessfulSyncAt: Instant?
)

enum class Freshness {
    Fresh,
    Stale,
    Unknown
}

sealed interface SyncStatus {
    data object Idle : SyncStatus
    data object Refreshing : SyncStatus
    data class Failed(val reason: SyncFailure) : SyncStatus
}
```

Do not collapse everything into `Loading/Error/Success`. Offline-first apps often have data and an error at the same time.

## Write Path: Outbox First

Important writes should be persisted before the network starts.

```kotlin
suspend fun renameNote(noteId: NoteId, newTitle: String) {
    val operationId = newOperationId()

    database.withTransaction {
        noteDao.updateTitle(noteId, newTitle)
        outboxDao.insert(
            OutboxOperation(
                id = operationId,
                aggregateId = noteId.value,
                type = "RenameNote",
                payload = RenameNotePayload(newTitle).toJson(),
                state = OutboxState.Pending
            )
        )
    }

    workManager.enqueueUniqueWork(
        "outbox-drain",
        ExistingWorkPolicy.KEEP,
        OutboxWorker.request()
    )
}
```

The transaction ties user-visible state to the durable sync operation. If the process dies after the transaction, WorkManager can still drain the outbox later.

## Merge Semantics

Every repository that syncs must define merge rules.

| Conflict | Common strategy |
|---|---|
| Server field changed, local field unchanged | Accept server |
| Local pending write exists | Keep local optimistic state, retry |
| Same field changed locally and remotely | Product-specific conflict policy |
| Server deleted entity with local pending edit | Tombstone/conflict state |
| Client duplicated write after retry | Idempotency key collapses duplicates |

Do not hide conflict resolution inside DTO mapping. It is domain behavior.

## Freshness and Staleness

Stale data is not the same as invalid data.

```kotlin
fun SyncMetadata.freshness(clock: Clock): Freshness =
    when {
        lastSuccessAt == null -> Freshness.Unknown
        clock.now() - lastSuccessAt < 15.minutes -> Freshness.Fresh
        else -> Freshness.Stale
    }
```

The UI can render stale content with a banner, refresh affordance, or disabled critical actions. This is better than blanking the screen because refresh failed.

## Repository Boundaries

Repositories should not:

- Know about Compose.
- Return mutable entities.
- Expose DAO rows as domain models.
- Start unscoped global coroutines.
- Hide non-idempotent network retries.
- Own auth token refresh without a clear auth boundary.
- Use `stateIn(applicationScope)` accidentally.

Repositories can:

- Expose cold Flows from local storage.
- Execute suspend reads/writes.
- Own sync transactions.
- Map data rows and DTOs to domain models.
- Enqueue durable work.
- Expose hot state only when intentionally acting as a scoped cache.

## Testing Source of Truth

Test the contract, not just mocks.

```kotlin
@Test
fun refreshFailureKeepsCachedDataAndMarksSyncFailed() = runTest {
    dao.insert(ProductRow(id = "1", name = "Cached"))
    api.failNextRequest(IOException())

    repository.refreshProducts()

    val state = repository.observeProductState().first()
    assertEquals("Cached", state.data.single().name)
    assertIs<SyncStatus.Failed>(state.syncStatus)
}
```

Add tests for:

- Process death between local write and upload.
- Idempotent retry after timeout.
- Server conflict while local outbox pending.
- Multi-hop database migration preserving outbox rows.
- Stale cache after failed refresh.

## Staff Engineer Review Checklist

- Is source of truth documented per repository?
- Does the UI observe local state instead of raw network state?
- Are important writes durable before network starts?
- Are local state and outbox insertions in one transaction?
- Are freshness and sync failure modeled independently from data?
- Are conflict policies explicit and product-approved?
- Is idempotency part of write retry design?
- Are destructive migrations forbidden for user-value tables?
- Are repository Flows cold unless hot caching is intentional?
- Do tests cover process death, retries, conflicts, and stale data?

## Further Reading

- [`room.md`](room.md) - Room and offline-first storage.
- [`paging.md`](paging.md) - paging source ownership.
- [`../../mobile-system-design/offline-sync.md`](../../mobile-system-design/offline-sync.md) - durable outbox and sync design.
- [`../concurrency/workmanager.md`](../concurrency/workmanager.md) - durable background work.
- [Android Developers: Guide to app architecture](https://developer.android.com/topic/architecture)

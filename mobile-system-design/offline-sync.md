# Offline Sync (Notes / Tasks / CRM-style)

> A 45-60 minute mobile system-design walkthrough for an offline-first app where users mutate state without a network (Apple Notes, Todoist, Salesforce Mobile). The bulk of this file is the *client* sync engine — outbox, delta pull, conflict resolution — with the server reduced to an API contract.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design offline sync for a notes app."
> **Candidate:** "The interesting client problem is making writes durable, the read flow eventually consistent, and conflicts comprehensible to the user. I'll deep-dive the outbox + merge path."

### Functional Requirements
- **Create, edit, delete notes** while offline. Changes are durable.
- **Sync up** on reconnect — no user button required.
- **Sync down** changes made on other devices.
- **Conflict resolution** that doesn't silently destroy user work.
- **Last-modified timestamps** visible to the user.

### Non-Functional Requirements
- **Local writes are instant** — UI never blocks on the server.
- **Eventually consistent** across devices within minutes of reconnect.
- **No duplicates** after retries.
- **Survives reinstall** — server is the ultimate source of record.
- **Low data usage** — only deltas, not full state.

### Out of Scope
- Real-time collaborative editing (separate file — see `collaborative-editing.md`)
- Rich text / media attachments inside notes
- End-to-end encryption (assume TLS only)
- Multi-account on one device
- Background sync on a hostile OEM (best-effort)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Single-user across devices, or shared notebooks? | LWW is fine for single-user; shared notebooks need merge UX |
| Note size? | Whole-record vs field-level diffs |
| Average notes per user? | Initial sync time, page size |
| How often do conflicts actually happen? | LWW vs CRDT vs manual-merge tradeoff |
| Hard delete or trash? | Tombstones, retention policy |
| Background sync expectations? | WorkManager periodic vs on-demand |
| Compliance (right to delete)? | Tombstone propagation |

> **Candidate:** "Assume 1 user across 2-3 devices, < 5KB notes, ~500 notes/user typical, conflicts rare (< 1%), trash with 30-day retention, periodic background sync."

---

## 3. High-Level Diagram (~10 min)

```
   ┌─────────────────────────────────┐
   │  Android Client (this talk)     │
   │  ┌──────┐  ┌───────┐  ┌───────┐ │
   │  │ Room │  │Outbox │  │ Sync  │ │
   │  └──────┘  └───────┘  └───────┘ │
   └──────────────┬──────────────────┘
                  │ HTTPS (deltas)
                  ▼
        ┌─────────────────────┐
        │   Sync API (BFF)    │
        │ /push, /pull        │
        └──────────┬──────────┘
                   │
       ┌───────────▼────────────┐
       │   Notes Service +      │
       │   Versioned Store      │  ← black box
       └────────────────────────┘
```

**Server-side (named, not designed):**
- **Sync API (BFF)** — accepts a batch of client ops in `/push`; returns deltas since a change token in `/pull`.
- **Notes Service** — applies ops, assigns server version, emits change events.
- **Versioned Store** — durable persistence with monotonic per-record versions.

---

## 4. API Contract

### Push (client → server)

```json
POST /v1/sync/push
{
  "ops": [
    { "op": "upsert", "clientId": "8f7…uuid", "id": "n_42",
      "title": "Groceries", "body": "milk\neggs", "baseVersion": 7, "updatedAt": 1750000000 },
    { "op": "delete", "id": "n_99", "baseVersion": 3 }
  ]
}

200 OK
{
  "applied": [
    { "clientId": "8f7…", "id": "n_42", "newVersion": 8 }
  ],
  "conflicts": [
    { "id": "n_99", "reason": "VERSION_MISMATCH", "serverVersion": 5,
      "serverState": { "title": "...", "body": "...", "updatedAt": ... } }
  ]
}
```

### Pull (server → client)

```json
GET /v1/sync/pull?since=ct_8f3a&limit=100
200 OK
{
  "changes": [
    { "id": "n_77", "version": 12, "title": "...", "body": "...",
      "updatedAt": ..., "deleted": false },
    { "id": "n_03", "version": 9, "deleted": true, "deletedAt": ... }
  ],
  "nextToken": "ct_910c",
  "hasMore": false
}
```

### Idempotency
- Every `upsert` carries `clientId` (UUID). Server dedupes on retry.
- Every record has a monotonic `version`. Client sends `baseVersion`; server rejects with `VERSION_MISMATCH` if it advanced.
- Server returns a `nextToken` (opaque change cursor) for the next pull.

> **Wire-level rule:** the client never sends "full state" — only ops since the last successful push. Pulls are always deltas after the first sync.

---

## 5. Mobile App Architecture (~10 min)

### Module structure

```
:app
:feature:notes-list
:feature:note-editor
:core:network        ← Ktor 3 / Retrofit
:core:database       ← Room 2.7+
:core:work           ← SyncWorker (periodic) + PushWorker (on-write)
:core:sync           ← Outbox, ChangeTokenStore, ConflictResolver
:domain:notes
:data:notes
```

### Layered diagram

```
   Compose UI ──► NoteViewModel ──► NoteRepository
                                       │
                                       ├─► NoteDao (Room, SSOT for UI)
                                       ├─► OutboxDao (durable pending ops)
                                       └─► SyncEngine
                                            │
                                            ├─► PushWorker (on dirty)
                                            └─► PullWorker (periodic + on FCM hint)
```

### Key class signatures

```kotlin
interface NoteRepository {
    fun notes(): Flow<List<Note>>
    suspend fun create(title: String, body: String): String   // returns id
    suspend fun update(id: String, title: String, body: String)
    suspend fun delete(id: String)
}

class SyncEngine @Inject constructor(
    private val outboxDao: OutboxDao,
    private val noteDao: NoteDao,
    private val tokenStore: ChangeTokenStore,
    private val api: SyncApi,
    private val resolver: ConflictResolver,
) {
    suspend fun push(): SyncResult
    suspend fun pull(): SyncResult
}
```

---

## 6. Local Storage (Room as the only thing the UI reads)

```kotlin
@Entity(tableName = "notes")
data class NoteEntity(
    @PrimaryKey val id: String,             // client UUID or server id (stabilized after first push)
    val title: String, val body: String,
    val version: Int,                        // last known server version
    val updatedAt: Long,
    val deleted: Boolean,                    // tombstone for sync
    val dirty: Boolean                       // local changes not yet pushed
)

@Entity(tableName = "outbox")
data class OutboxEntry(
    @PrimaryKey val clientId: String,        // UUID per operation
    val noteId: String, val opType: OpType,  // UPSERT, DELETE
    val baseVersion: Int,
    val payloadJson: String,                 // snapshot at enqueue time
    val attempts: Int, val firstAttemptedAt: Long?
)

@Entity(tableName = "sync_state")
data class SyncStateEntity(
    @PrimaryKey val key: String,             // "lastChangeToken", "lastPushAt"
    val value: String
)
```

> **Probing Q:** "Why a separate outbox and not just `dirty=true` rows?" Because an outbox op is a snapshot — if the user edits the same note 3 times offline, you get 3 ops with 3 client IDs and the server resolves in order. The `dirty` flag is a UI-side hint; the outbox is the durable transmission queue.

---

## 7. Deep Dive: Outbox + Conflict Resolution (~15 min)

> *I'd pick this as the deep dive because it covers durability, idempotency, retry semantics, and the user-visible conflict UX — the parts that actually break in production.*

### Write path (online or offline, same code)

```kotlin
suspend fun update(id: String, title: String, body: String) = db.withTransaction {
    val current = noteDao.get(id)
    val updated = current.copy(title = title, body = body,
                               updatedAt = clock.now(), dirty = true)
    noteDao.upsert(updated)                       // UI sees it immediately
    outboxDao.insert(OutboxEntry(
        clientId = UUID.randomUUID().toString(),
        noteId = id, opType = OpType.UPSERT,
        baseVersion = current.version,             // server-known version at enqueue
        payloadJson = json.encodeToString(updated),
        attempts = 0, firstAttemptedAt = null,
    ))
    workManager.enqueueUniqueWork("push", REPLACE, pushWorkRequest())
}
```
> [!WARNING]
> **The Outbox Flaw:** It is extremely tempting to replace `workManager.enqueue...` with a simple `CoroutineScope.launch { upload() }` for lower latency. Do not do this. If the network call succeeds but the OS kills your app *before* you can delete the Outbox row, the record remains in the database. Without WorkManager, that row is permanently stuck. With WorkManager, it will be retried on the next launch. Furthermore, because it will be retried, the `clientId` acts as an **idempotency key** so the server safely drops the duplicate upload.

### Push path (`PushWorker`, `@HiltWorker`)

```kotlin
override suspend fun doWork(): Result {
    val batch = outboxDao.take(100)
    if (batch.isEmpty()) return Result.success()
    val resp = api.push(PushReq(batch.toOps()))
    db.withTransaction {
        resp.applied.forEach { applied ->
            outboxDao.delete(applied.clientId)
            noteDao.updateVersion(applied.id, applied.newVersion, dirty = false)
        }
        resp.conflicts.forEach { conflict ->
            outboxDao.delete(conflictedClientIdsFor(conflict.id))
            resolver.handle(conflict)            // see below
        }
    }
    return if (outboxDao.size() > 0) Result.retry() else Result.success()
}
```

`PushWorker` is unique-named so concurrent edits coalesce. Backoff is exponential with jitter; max 5 attempts per row before flipping to a `FAILED_PERMANENT` state.

### Pull path (`PullWorker`, periodic + on FCM hint)

```kotlin
override suspend fun doWork(): Result {
    var token = tokenStore.lastToken
    do {
        val resp = api.pull(since = token, limit = 200)
        db.withTransaction {
            resp.changes.forEach { change ->
                val local = noteDao.get(change.id)
                if (local?.dirty == true) {
                    resolver.handleDownstream(local, change)    // local has unpushed edits
                } else {
                    noteDao.upsert(change.toEntity())
                }
            }
            tokenStore.lastToken = resp.nextToken
        }
        token = resp.nextToken
    } while (resp.hasMore)
    return Result.success()
}
```

### Conflict resolution

Three strategies, picked per record type at design time:

| Strategy | When | UX |
|---|---|---|
| **Last-write-wins (LWW)** | Notes, prefs — when last edit usually reflects intent | Silent; show "synced just now" |
| **HLC-LWW** (hybrid logical clock) | Devices with skewed clocks | Same UX, robust ordering |
| **Manual merge** | Anything irreplaceable (long-form, structured data) | Banner: "This note was edited on another device. Keep mine / Keep theirs / Merge" |
| **CRDT (last-writer-set / RGA)** | Truly concurrent edits to one note | Auto-merge; out of scope for this round |

**Default for this design:** LWW for trivial fields, **manual merge** for body when `serverVersion > baseVersion` AND `local.dirty`. The losing version is preserved as `n_42_conflict_v5` so nothing is destroyed.

```kotlin
class ConflictResolver {
    fun handle(conflict: PushConflict) {
        val local = noteDao.get(conflict.id) ?: return
        // Save local as a conflict copy
        noteDao.upsert(local.copy(id = "${conflict.id}_conflict_${local.version}", dirty = false))
        // Accept server state as the canonical record
        noteDao.upsert(conflict.serverState.toEntity())
        // Surface in a "Conflicts" inbox
        conflictInboxDao.insert(ConflictRecord(conflict.id, local.version, conflict.serverVersion))
    }
}
```

### Tombstones + delete propagation

Deletes are **soft** server-side: the record gets `deleted=true` and stays around for ~30 days so other devices can pull the tombstone. Client mirrors: setting `deleted=true` instead of removing the row, then purging after the next successful pull confirms the tombstone.

### Sync triggers

| Trigger | Worker |
|---|---|
| User edit | `PushWorker` (debounced 2s) |
| App foreground | `PullWorker` (one-shot) |
| FCM "sync hint" data message | `PullWorker` (one-shot, expedited) |
| Periodic | `PullWorker` every 30 min (`PeriodicWorkRequest`) |
| Reconnect | `PushWorker` + `PullWorker` (chain) |

### Failure modes

| What breaks | Behavior |
|---|---|
| App killed mid-push | Outbox rows persist; next launch retries |
| Server returns 409 conflict | Resolver writes conflict copy + surfaces in inbox |
| Token store wiped | Pull falls back to full sync (paginated) |
| Clock skew (laptop in past) | HLC or server-side timestamp wins |
| Outbox grows huge (weeks offline) | Push in pages of 100; show "syncing X of Y" |

---

## 8. Trade-offs

### Sync strategy

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Op log + delta pull** (this design) | Bandwidth efficient, supports conflicts | Schema discipline, more code | Pick this |
| Full-state diff | Trivial | Crushes battery + data | Skip |
| Realtime CRDT replication | Best UX | Complex; needs CRDT library + server | For collab editing only |
| Full-state push every change | Trivial | Wastes bandwidth | Skip |

### Conflict resolution

| Option | Pros | Cons | Use when |
|---|---|---|---|
| **LWW** | No code | Silent data loss possible | Single-user, low-stakes |
| **HLC-LWW** | Robust ordering | Slightly more logic | Single-user, multi-device |
| **Manual merge** | No data loss | Bothers user | Stakes are high |
| **CRDT** | Auto-merge, no UX | Heavy library, schema lock-in | Real concurrent editing |

### Local storage

| Option | Verdict |
|---|---|
| **Room** | Pick — query + Flow + migrations |
| Realm Sync | Powerful but paid, vendor lock-in |
| SQLDelight | Good if KMP from day 1 |
| Plain files | No queries, no atomicity |

### Background scheduler

| Option | Verdict |
|---|---|
| **WorkManager** | Pick — survives reboot, constraints, expedited, periodic |
| AlarmManager | Lower-level; no constraints |
| Foreground Service | Only for user-initiated long syncs |
| GcmTaskService | Deprecated |

---

## 9. Major Concerns

- **Durability.** Outbox is in Room (WAL mode). Every op is a transaction. No in-memory queue.
- **Clock skew.** Don't trust device clocks. Use HLC or server-assigned `updatedAt`. Show "synced X ago" relative to last successful pull.
- **Battery.** Periodic pull at 30 min; on-write push debounced by 2s; FCM hint for high-priority pulls. No keep-alive sockets unless the product needs them.
- **OEM kill.** `WorkManager` with `setRequiresBatteryNotLow(false)` and `NetworkType.CONNECTED`. Foreground service only for user-initiated big restores.
- **Token loss.** If `tokenStore.lastToken` is corrupted, fall back to full pull (paginated). Document the cost; it's rare but it happens.
- **Schema migrations.** Every Room version ships an explicit migration. Outbox payloads use a versioned JSON envelope so old rows survive code changes.
- **Conflict UX.** Don't surprise the user. A conflict inbox with "Mine | Theirs | Merge" is better than silent overwrites. Track the rate; if it's > 1% something is wrong.
- **Privacy / delete-my-data.** Hard-delete locally on request; server propagates tombstones; honor GDPR window.

---

## 10. Follow-up Questions

> **Q: Why version per record instead of a global change number?**
> Per-record versioning lets the server detect conflicts on the row that changed without locking everything. Global versions force serialization and don't scale.

> **Q: What's the difference between dirty and outbox?**
> `dirty=true` is a UI hint ("this note has unsynced edits — show a dot"). The outbox is the durable queue of ops to send. They can diverge: the worker may be mid-push, in which case the row is still dirty until the ack lands.

> **Q: A user edits the same note 5 times offline — what does the server see?**
> 5 outbox ops in order, each with `baseVersion = previous_known_version`. Server applies them serially; only the last one wins the final state. We could collapse the queue on the client (debounce), and we do — 2 s coalesce window.

> **Q: How do you guarantee no duplicates if push retries after a timeout?**
> Each op has `clientId`. Server returns the same `newVersion` for the same `clientId`. Client deletes the outbox row on success — retries are idempotent.

> **Q: How do you handle a really long offline period (weeks)?**
> Outbox grows. Push in pages of 100 with a visible "syncing X of Y" indicator. Pull paginates over `nextToken` until `hasMore=false`. Don't block UI; sync is background.

> **Q: How is this tested?**
> Fake API server returning scripted responses (success, 409, network error). Run the sync engine against the fake in a JVM test. Property-based test for the resolver: any sequence of (push, pull, conflict) ends in a deterministic state.

---

## 11. Out of Scope (defended)

- **Real-time collaboration** — operational transforms or CRDTs are a different beast (see `collaborative-editing.md`).
- **End-to-end encryption** — encrypt at the op layer with libsodium; here we assume TLS only.
- **Cross-account sync** — assume one account per install.
- **Binary attachments inside notes** — separate flow (pre-signed upload, content-addressed blobs).
- **Server scaling internals** — the change-token store is a black box.

---

## 12. Further Reading

- [weeeBox/mobile-system-design](https://github.com/weeeBox/mobile-system-design) — reference format.
- [Android Developers — WorkManager guide](https://developer.android.com/topic/libraries/architecture/workmanager) — official guide; expedited + constraints.
- [Local-first software (Ink & Switch)](https://www.inkandswitch.com/local-first/) — manifesto behind offline-first design.
- [Hybrid Logical Clocks paper](https://cse.buffalo.edu/tech-reports/2014-04.pdf) — the HLC algorithm.
- [Yjs CRDT docs](https://docs.yjs.dev/) — when you need real concurrent merge.

---

> **Closing in the interview:** "I anchored on the outbox + resolver because that's where bugs live in production. Happy to next discuss FCM-driven pull hints, schema-evolution discipline, or how the conflict inbox UI is designed."

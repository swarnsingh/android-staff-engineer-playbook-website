# Collaborative Editing (Google Docs / Figma-style)

> A 45-60 minute mobile system-design walkthrough for a real-time collaborative editor on Android. CRDT / OT internals live on a shared library — bulk is on-device: client model, presence, optimistic local apply, sync, offline.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design Google Docs / Figma-style collaboration for a mobile app."
> **Candidate:** "Two hard parts on the client: model that supports concurrent ops (CRDT or OT via SDK), and presence + cursor sync at low latency. Backend is a sequencer/relay. I'll deep-dive the local apply + sync path."

### Functional Requirements
- **Multiple users edit the same document concurrently**.
- **Real-time updates** of others' edits.
- **Presence + remote cursors** visible.
- **Offline edits** that sync on reconnect.
- **Conflict-free merge** of concurrent edits.

### Non-Functional Requirements
- **< 100 ms perceived latency** for local edits.
- **Eventual consistency** across all clients.
- **No data loss** during disconnect.
- **Battery** — efficient delta stream, not full state replication.
- **Privacy** — document content stays inside the app's session.

### Out of Scope
- Operational Transform / CRDT algorithm internals (use Yjs, Automerge, or in-house SDK as a black box)
- Server-side relay sharding / scaling
- Document permission management UI
- Comments / suggestions / version history
- Inline media / embedded content

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| CRDT or OT? | Library choice |
| Document type (rich text, tabular, graph)? | Model shape |
| Max concurrent users per doc? | Buffering, presence bandwidth |
| Offline duration to support? | Outbox sizing, conflict resolution stress |
| Cursor presence ephemeral or persisted? | Stream channel |
| Server-side authority on order? | Sequencer model |
| Authentication per document? | Permission check on join |

> **Candidate:** "CRDT via Yjs-style SDK, rich text document, up to 10 concurrent editors, support week-long offline, ephemeral cursors, server is sequencer, doc-scoped permissions."

---

## 3. High-Level Diagram (~10 min)

```
        Mobile Client A
   ┌──────────────────────────┐
   │ Compose Editor           │
   │   ▲                      │
   │   │ render               │
   │ DocumentModel (CRDT)     │
   │   ▲                      │
   │   │ apply local ops      │
   │ OpQueue (Room outbox)    │
   │   │                      │
   │ DocSocket (WSS)          │
   └──────────┬───────────────┘
              │
              ▼
   ┌──────────────────────────┐
   │  Collab Relay / Sequencer│  ← black box
   └──────────┬───────────────┘
              │
              ▼
        Other clients (B, C, ...)
```

**Components:**
- **`DocumentModel`** — CRDT instance for this document.
- **`OpQueue`** — durable buffer of unacked local ops.
- **`DocSocket`** — WebSocket lifeline; sends/receives op + presence frames.
- **`PresenceTracker`** — cursors + selections of other users.
- **`DocSyncService`** — long-running while doc is open.

---

## 4. API Contract

### Join document (WSS handshake)

```json
{ "type": "join", "docId": "d_42", "token": "ey..." }
```

Server replies with current state vector + initial CRDT snapshot if needed.

### Op frame (bidirectional)

```json
{
  "type": "op",
  "docId": "d_42",
  "ops": [
    { "type": "insert", "pos": 142, "text": "hello", "clientId": "c_8f7a", "clock": 999 }
  ]
}
```

### Presence frame

```json
{
  "type": "presence",
  "docId": "d_42",
  "userId": "u_7", "name": "Sam", "color": "#FF6B6B",
  "selection": { "anchor": 142, "focus": 150 }
}
```

### Ack

```json
{ "type": "ack", "ops": [{ "clientId": "c_8f7a", "clock": 999 }] }
```

---

## 5. Mobile App Architecture

### Module structure

```
:app
:feature:editor          ← Compose editor screen, presence UI
:core:network
:core:database           ← outbox + snapshot
:core:crdt               ← Yjs-style SDK wrapper
:data:document
```

### Layered diagram

```
   Compose Editor ──► EditorViewModel ──► DocumentRepository
                                                │
                                                ├─► DocumentModel (CRDT)
                                                ├─► OpQueue (Room outbox)
                                                ├─► DocSocket (WSS)
                                                └─► PresenceTracker
```

### Key class signatures

```kotlin
interface DocumentRepository {
    suspend fun open(docId: String): Document
    fun observeContent(docId: String): Flow<DocumentContent>
    fun observePresence(docId: String): Flow<List<RemoteCursor>>
    suspend fun applyLocalEdit(edit: LocalEdit)
    suspend fun close(docId: String)
}

class DocumentModel internal constructor(private val crdt: CrdtInstance) {
    fun snapshot(): DocumentContent
    fun applyLocal(op: Op): Op             // returns the op as serialized
    fun applyRemote(op: Op)
    fun stateVector(): ByteArray
}
```

---

## 6. Local Storage

```kotlin
@Entity(tableName = "documents")
data class DocumentEntity(
    @PrimaryKey val docId: String,
    val crdtSnapshotBytes: ByteArray,   // serialized CRDT state
    val lastSyncedClock: Long,
    val openedAt: Long
)

@Entity(tableName = "op_outbox")
data class OpOutbox(
    @PrimaryKey val clientOpId: String,
    val docId: String, val opBytes: ByteArray,
    val clock: Long, val createdAt: Long, val sent: Boolean
)
```

CRDT snapshot is the durable state. Outbox is the queue of locally-applied ops awaiting server ack.

---

## 7. Deep Dive: Local Apply + Sync (~15 min)

> *I'd pick this as the deep dive because the local-first apply + outbox + reconcile is the heart of the collaborative client. Get this wrong and edits get lost or duplicated; get it right and the UI feels instant.*

### Local edit path

```kotlin
suspend fun applyLocalEdit(edit: LocalEdit) = db.withTransaction {
    val op = documentModel.applyLocal(edit.toCrdtOp())
    // 1. Apply locally — UI updates via Flow
    contentBus.tryEmit(documentModel.snapshot())
    // 2. Persist outbox entry — durable
    outboxDao.insert(OpOutbox(
        clientOpId = UUID.randomUUID().toString(),
        docId = currentDocId,
        opBytes = op.serialize(),
        clock = op.clock,
        createdAt = clock.now(),
        sent = false,
    ))
    // 3. Send via socket — if connected
    if (socket.isConnected) {
        socket.send(op.toWire(currentDocId))
    }
    // 4. Update persistent snapshot (debounced)
    snapshotScheduler.touch()
}
```

The order matters: apply → persist → send. If we crash between (1) and (2), the user sees the edit but loses it after restart. So (2) must happen before any UI commit; we use a Room transaction.

### Snapshot debouncing

```kotlin
class SnapshotScheduler @Inject constructor(
    private val dao: DocumentDao,
    private val model: DocumentModel,
    private val scope: CoroutineScope,
) {
    private val pending = MutableStateFlow(false)

    init {
        scope.launch {
            pending.debounce(2.seconds).collect {
                if (it) writeSnapshot()
            }
        }
    }

    fun touch() { pending.value = true }

    private suspend fun writeSnapshot() {
        val bytes = model.serialize()
        dao.update(currentDocId, bytes, clock.now())
        pending.value = false
    }
}
```

Writing the whole CRDT snapshot on every keystroke is wasteful. Debounce 2s. The outbox provides durability between snapshot saves.

### Remote op handling

```kotlin
socket.incomingFrames.collect { frame ->
    when (frame) {
        is Frame.Op -> {
            documentModel.applyRemote(frame.op)
            contentBus.tryEmit(documentModel.snapshot())
        }
        is Frame.Presence -> presenceTracker.update(frame)
        is Frame.Ack -> outboxDao.deleteByClientOpId(frame.ackedOpId)
    }
}
```

The CRDT library handles concurrent ops correctly — local and remote ops can be applied in any order and converge to the same state.

### Reconnect + state vector sync

```kotlin
suspend fun onReconnect() {
    val sv = documentModel.stateVector()
    socket.send(Frame.SyncRequest(docId = currentDocId, stateVector = sv))
    // Server responds with deltas the client doesn't have yet
}
```

The state vector compactly represents "what ops I've seen." Server computes the diff and sends only missing ops.

### Outbox flush on reconnect

```kotlin
suspend fun onSocketConnected() {
    val pending = outboxDao.unsent(docId = currentDocId)
    pending.forEach { socket.send(it.toWire()) }
    // Optionally: persist in `sent=true` after send; relies on server ack to delete
}
```

CRDT ops are idempotent — re-sending an op that was already received is a no-op. So we can flush optimistically without worrying about duplicates.

### Presence

```kotlin
class PresenceTracker {
    private val _cursors = MutableStateFlow<Map<String, RemoteCursor>>(emptyMap())
    val cursors = _cursors.asStateFlow()

    fun update(presence: Frame.Presence) {
        _cursors.update { it + (presence.userId to presence.toRemoteCursor()) }
    }

    fun localCursorChanged(selection: TextRange) {
        socket.send(Frame.Presence(localUserId, ..., selection.toRange()))
    }
}
```

Presence is ephemeral; not persisted. Cursors fade after 5s of no update from a user.

### Foreground service while doc is open

```kotlin
class DocCollabService : LifecycleService() {

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        ServiceCompat.startForeground(
            this, NOTIF_ID, buildDocOpenNotification(currentDoc),
            FOREGROUND_SERVICE_TYPE_DATA_SYNC
        )
        return START_REDELIVER_INTENT
    }
}
```

Foreground service while a document is actively open (with the user). Keeps the socket alive during brief backgrounding. Closed when user exits the doc.

### Failure modes

| What breaks | Behavior |
|---|---|
| Network drops mid-edit | Outbox persists; flush on reconnect; UI keeps working |
| App killed by OEM | On relaunch, outbox replays; CRDT idempotency saves us |
| Document grew very large | Pagination on initial load via CRDT chunking; lazy materialization |
| Two clients edit same range concurrently | CRDT merges per its algebra; both edits preserved |
| Server out of sync | Client requests full sync; server sends complete state |
| Stale snapshot on disk | State vector reconciliation pulls deltas to catch up |

---

## 8. Trade-offs

### Algorithm

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **CRDT (Yjs, Automerge)** | Decentralized; offline-friendly; commutative ops | Larger state vectors | Pick for modern apps |
| **OT (Operational Transform)** | Tighter document state | Requires central server; complex to implement | Used by Google Docs historically |
| Last-write-wins | Trivial | Loses concurrent edits | Skip for collab |
| Locking | Avoids conflicts | Blocks users; bad UX | Skip |

### Server topology

| Option | Verdict |
|---|---|
| **Sequencer / relay (server orders ops)** | Pick — easier for client; supports offline |
| **Peer-to-peer (no server)** | Niche; firewall pain |
| **Authoritative server (client sends intentions, server commits)** | Used by Figma-like; more complex client |

### Storage

| Option | Verdict |
|---|---|
| **CRDT snapshot in Room (BLOB) + op outbox** | Pick — durable + idempotent |
| Per-op file | Many small files |
| In-memory only | Loses on crash |

### Sync protocol

| Option | Verdict |
|---|---|
| **WebSocket (binary frames)** | Pick — bidirectional, low overhead |
| HTTP long-poll | Higher latency |
| WebRTC data channel | Peer-to-peer; not our model |

### Presence channel

| Option | Verdict |
|---|---|
| **Same WebSocket, separate frame type** | Pick — one connection |
| Separate channel | More connections, more overhead |

---

## 9. Major Concerns

- **Durability.** Outbox in Room before UI commits. Snapshot debounced.
- **Latency.** Local apply is synchronous; remote ops apply async; UI updates from Flow.
- **Battery.** Foreground service only while doc is open. Socket disconnects on close.
- **Backpressure.** Don't flood the server with op frames; batch within 10ms windows.
- **Privacy.** End-to-end encryption is possible with some CRDT libraries; out of scope here, but the SDK boundary supports it.
- **Document size.** CRDT state grows over time (tombstones, vector clocks). Periodic GC server-side; client re-syncs.
- **Permission revocation.** Server can boot a client; client must gracefully exit (`socket.disconnect()`).
- **Conflict UX.** Concurrent edits to the same range — CRDT merges deterministically; user may see unexpected text. Highlight remote edits briefly to reduce surprise.

---

## 10. Follow-up Questions

> **Q: User edits offline for a week, then reconnects — what happens?**
> Outbox has ~thousands of ops. On reconnect: `applyOutbox` sends them. Server orders and broadcasts. Other clients receive and CRDT-merge. The user's view doesn't change until other clients' ops arrive.

> **Q: How is initial document load fast for large docs?**
> Server sends a CRDT snapshot (compact) + state vector. Client renders the visible portion lazily; full document materializes in background. Subsequent edits stream.

> **Q: Two users select the same text and edit at the same time — what does user A see?**
> User A sees their edit instantly. Then User B's op arrives a few hundred ms later; CRDT merges (e.g., both inserts coexist at the same logical position). UI highlights B's contribution briefly for awareness.

> **Q: How is presence kept fresh without flooding the server?**
> Presence frames sent at most every 100 ms while cursor is moving. Idle cursors send a keepalive every 5s. Server fans out.

> **Q: How would you support comments / suggestions?**
> Separate CRDT layer (or a separate op type). Comments are anchored to op identifiers, which CRDTs make stable across edits. Sketched here, fully covered in a different design.

> **Q: How do you test this?**
> Fake socket + scripted ops. Property test: any interleaving of (local edit, remote op, network drop, reconnect) converges to the same final state. Compare against the reference CRDT lib's own conformance tests.

---

## 11. Out of Scope (defended)

- **CRDT / OT algorithm internals** — use SDK.
- **Server relay / scaling** — backend.
- **Version history UI** — separate feature.
- **Comments / suggestions** — additive layer.
- **Inline media** — separate sub-system.

---

## 12. Further Reading

- [Yjs documentation](https://docs.yjs.dev/) — production CRDT for collaborative editing.
- [Automerge](https://automerge.org/) — alternative CRDT library.
- [Figma — How our multiplayer works](https://www.figma.com/blog/how-figmas-multiplayer-technology-works/) — practitioner perspective.
- [Ink & Switch — Local-first software](https://www.inkandswitch.com/local-first/) — design philosophy.
- [Google Wave OT history](https://en.wikipedia.org/wiki/Operational_transformation) — origins of OT.

---

> **Closing in the interview:** "I anchored on local apply + sync because that's the heart of the user experience. Happy to dig into the state vector reconciliation, presence backpressure, or offline week-long edit scenarios next."

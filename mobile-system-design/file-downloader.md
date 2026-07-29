# File Downloader Library

> A 45-60 minute mobile system-design walkthrough for a robust file-downloader library. Think podcasts, offline video, attachments: chunked, resumable, parallel, lifecycle-aware.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a file-downloader library."
> **Candidate:** "The classic problems are resumability across flaky networks, parallel chunks for speed, and surviving process death. I'll deep-dive the chunked download + resume path."

### Functional Requirements
- **Queue arbitrary downloads** identified by URL + destination.
- **Resumable** after pause / network loss / process death.
- **Progress updates** to the UI.
- **Concurrency control** — N parallel downloads, M parallel chunks per download.
- **Priority levels** (foreground user-initiated vs background prefetch).

### Non-Functional Requirements
- **Survives process death** (durable queue, partial files preserved).
- **Battery-conscious** (no Wi-Fi-blocking unless requested).
- **Resilient to network drops** (auto-retry with backoff).
- **Composable observation** (Flow-based progress).
- **Storage-aware** (low-storage handling).

### Out of Scope
- DRM / encrypted streams (delegate to ExoPlayer's DRM session)
- Peer-to-peer downloads
- Cross-process queue sharing
- Background upload (separate concern — see media upload patterns)
- HTTPS pinning details (caller wires OkHttp)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Largest file size? | Chunking strategy, disk pre-allocation |
| Server supports HTTP `Range` requests? | Resumable + parallel chunks |
| Wi-Fi-only requirement? | WorkManager constraint vs Foreground service |
| Foreground-only downloads or also background? | Notification + service decision |
| Android API floor? | `setExpedited`, FGS rules |
| Need cellular data warnings? | `ConnectivityManager.isActiveNetworkMetered` |
| Acceptable resume granularity? | Block size for the partial file ledger |

> **Candidate:** "Files 1 MB-500 MB, server supports `Range`, mostly Wi-Fi but cellular allowed with consent, foreground + background, Android 9+, resume at chunk boundaries."

---

## 3. High-Level Diagram (~10 min)

```mermaid
flowchart TD
    App["App caller"] --> Manager["DownloadManager API"]
    Manager --> Queue["Durable Room queue"]
    Queue --> Work["WorkManager DownloadWorker"]
    Work --> Fetch["Bounded parallel range fetchers"]
    Fetch --> Partial["Partial files + verified chunk ledger"]
    Partial --> Assemble["Atomic assembly / rename"]
    Assemble --> Final["Final file"]
```

Queue and chunk progress are durable, so process death resumes verified work instead of restarting blindly or exposing a partial file as complete.

**Components:**
- **`DownloadManager`** — public API; enqueue, observe, pause, cancel.
- **`Queue (Room)`** — durable queue + chunk ledger.
- **`DownloadWorker`** — `@HiltWorker` per download; orchestrates chunks.
- **`ChunkFetcher`** — single chunk request via OkHttp `Range`.
- **`Assembler`** — concatenates chunks into the final file on completion.

---

## 4. API Contract

```kotlin
interface DownloadManager {
    suspend fun enqueue(req: DownloadRequest): DownloadId
    suspend fun pause(id: DownloadId)
    suspend fun resume(id: DownloadId)
    suspend fun cancel(id: DownloadId)
    fun observe(id: DownloadId): Flow<DownloadState>
    fun observeAll(): Flow<List<DownloadState>>
}

data class DownloadRequest(
    val url: String,
    val destFile: File,
    val constraints: Constraints = Constraints(),
    val priority: Priority = Priority.NORMAL,
    val headers: Map<String, String> = emptyMap(),
    val expectedSize: Long? = null,
    val checksum: Checksum? = null,
)

sealed class DownloadState {
    object Queued : DownloadState()
    data class Running(val downloadedBytes: Long, val totalBytes: Long?, val bytesPerSecond: Long) : DownloadState()
    object Paused : DownloadState()
    data class Failed(val reason: Throwable, val canResume: Boolean) : DownloadState()
    data class Completed(val file: File) : DownloadState()
}
```

---

## 5. Mobile App Architecture

### Module structure

```
:lib:download
    download-api          ← public interface, models
    download-core         ← queue, worker, scheduler
    download-okhttp       ← OkHttp adapter
    download-ktor         ← optional Ktor adapter
```

### Layered diagram

```mermaid
flowchart LR
    Caller --> Manager["DownloadManager"] --> Queue["Room queue"]
    Queue --> Scheduler["WorkManager"] --> Worker["DownloadWorker"]
    Worker --> C0["Chunk 0"]
    Worker --> C1["Chunk 1"]
    Worker --> C2["Chunk 2"]
    C0 --> Assemble["Assembler"]
    C1 --> Assemble
    C2 --> Assemble
    Assemble --> Final["Final file"]
```

One worker owns download state while fetch concurrency remains bounded; assembly begins only after every required chunk passes validation.

---

## 6. Local Storage (Room as ledger)

```kotlin
@Entity(tableName = "downloads")
data class DownloadEntity(
    @PrimaryKey val id: String,
    val url: String, val destPath: String,
    val state: DownloadStateCode,
    val totalBytes: Long?, val downloadedBytes: Long,
    val priority: Int, val constraintsJson: String,
    val createdAt: Long, val updatedAt: Long,
    val checksumExpected: String?, val checksumAlgo: String?
)

@Entity(tableName = "chunks",
    primaryKeys = ["downloadId", "index"],
    foreignKeys = [ForeignKey(DownloadEntity::class, ["id"], ["downloadId"], onDelete = CASCADE)])
data class ChunkEntity(
    val downloadId: String, val index: Int,
    val startByte: Long, val endByte: Long,    // inclusive
    val state: ChunkState                       // PENDING, IN_PROGRESS, DONE
)
```

> **Probing Q:** "Why a chunk ledger separate from the file?" Because the partial file might be truncated by the OS or contain incomplete chunks. The ledger is the truth — on resume we re-issue any chunk not marked `DONE`.

---

## 7. Deep Dive: Chunked Resumable Download (~15 min)

> *I'd pick this as the deep dive because it covers HTTP `Range`, parallelism, partial-file management, and resume-after-crash — the whole reason this library exists.*

### Enqueue

```kotlin
suspend fun enqueue(req: DownloadRequest): DownloadId {
    val id = UUID.randomUUID().toString()
    db.withTransaction {
        downloadDao.insert(DownloadEntity(id, req.url, req.destFile.path, ...))
        // chunk planning happens after HEAD request inside the worker
    }
    workManager.enqueueUniqueWork(
        "download-$id",
        ExistingWorkPolicy.KEEP,
        OneTimeWorkRequestBuilder<DownloadWorker>()
            .setConstraints(req.constraints.toAndroidx())
            .setInputData(workDataOf("id" to id))
            .build()
    )
    return DownloadId(id)
}
```

### Worker

```kotlin
@HiltWorker
class DownloadWorker @AssistedInject constructor(
    @Assisted ctx: Context, @Assisted params: WorkerParameters,
    private val client: OkHttpClient,
    private val dao: DownloadDao,
    private val chunkDao: ChunkDao,
) : CoroutineWorker(ctx, params) {

    override suspend fun doWork(): Result {
        val id = inputData.getString("id") ?: return Result.failure()
        val entity = dao.get(id) ?: return Result.failure()

        // 1) HEAD to learn content-length + accept-ranges
        val head = client.headOrNull(entity.url) ?: return Result.retry()
        val totalBytes = head.contentLength()
        val supportsRange = head.acceptsRanges()
        dao.updateMeta(id, totalBytes, supportsRange)

        // 2) Plan chunks (one-time, idempotent)
        if (chunkDao.countFor(id) == 0) {
            planChunks(id, totalBytes, supportsRange)
        }

        // 3) Run parallel chunks
        return runChunks(id, entity)
    }
}
```

### Chunk planning

```kotlin
private suspend fun planChunks(id: String, total: Long?, supportsRange: Boolean) {
    if (total == null || !supportsRange) {
        chunkDao.insert(ChunkEntity(id, 0, 0, Long.MAX_VALUE, ChunkState.PENDING))   // one-shot
        return
    }
    val chunkSize = pickChunkSize(total)        // 1-8 MB based on file size
    val chunks = (0 until ceil(total / chunkSize.toDouble()).toInt()).map { i ->
        val start = i * chunkSize.toLong()
        val end = minOf(start + chunkSize - 1, total - 1)
        ChunkEntity(id, i, start, end, ChunkState.PENDING)
    }
    chunkDao.insertAll(chunks)
}
```

### Chunk runner (parallel)

```kotlin
private suspend fun runChunks(id: String, entity: DownloadEntity): Result = coroutineScope {
    val maxParallel = 3
    val sem = Semaphore(maxParallel)
    val pending = chunkDao.notDoneFor(id)
    val jobs = pending.map { chunk ->
        async {
            sem.withPermit { fetchChunk(id, chunk, entity) }
        }
    }
    val results = jobs.awaitAll()
    when {
        results.all { it is FetchResult.Ok } -> {
            assemble(id, entity.destPath)
            verifyChecksum(entity)?.let { return@coroutineScope Result.failure() }
            dao.markCompleted(id)
            Result.success()
        }
        results.any { it is FetchResult.NetworkError } -> Result.retry()
        else -> Result.failure()
    }
}
```

### Single chunk fetch

```kotlin
private suspend fun fetchChunk(id: String, chunk: ChunkEntity, entity: DownloadEntity): FetchResult {
    val partFile = File("${entity.destPath}.part.${chunk.index}")
    val alreadyWritten = if (partFile.exists()) partFile.length() else 0L
    val effectiveStart = chunk.startByte + alreadyWritten
    if (effectiveStart > chunk.endByte) {
        chunkDao.update(chunk.copy(state = ChunkState.DONE))
        return FetchResult.Ok
    }
    val request = Request.Builder()
        .url(entity.url)
        .header("Range", "bytes=$effectiveStart-${chunk.endByte}")
        .build()
    return runCatching {
        client.newCall(request).execute().use { resp ->
            if (resp.code !in setOf(200, 206)) return FetchResult.HttpError(resp.code)
            partFile.appendingSink().buffer().use { sink ->
                resp.body!!.source().use { src ->
                    while (true) {
                        val read = src.read(sink.buffer, BUFFER)
                        if (read == -1L) break
                        sink.emitCompleteSegments()
                        progressBus.publish(id, read)
                    }
                }
            }
            chunkDao.update(chunk.copy(state = ChunkState.DONE))
            FetchResult.Ok
        }
    }.getOrElse { FetchResult.NetworkError(it) }
}
```

### Assemble

```kotlin
private fun assemble(id: String, destPath: String) {
    val dest = File("$destPath.tmp")
    dest.outputStream().use { out ->
        chunkDao.allFor(id).sortedBy { it.index }.forEach { ck ->
            File("$destPath.part.${ck.index}").inputStream().use { it.copyTo(out) }
        }
    }
    if (!dest.renameTo(File(destPath))) error("rename failed")
    chunkDao.deleteAllFor(id)        // tidy up partial files
}
```

### Progress aggregation

```kotlin
object progressBus {
    private val flow = MutableSharedFlow<Pair<String, Long>>(extraBufferCapacity = 256)
    fun publish(id: String, bytes: Long) { flow.tryEmit(id to bytes) }
    fun observe(id: String): Flow<Long> = flow
        .filter { it.first == id }
        .map { it.second }
        .scan(0L) { acc, v -> acc + v }
        .sample(250.milliseconds)        // UI updates 4x/sec, not 60x
}
```

### Failure modes

| What breaks | Behavior |
|---|---|
| Network drop mid-chunk | Worker returns `Result.retry()`; partial file kept; resume from byte offset |
| Server returns 200 not 206 | Server ignored Range; restart chunk from start |
| Server returns 416 | Range invalid; re-plan (file size may have changed) |
| Process killed | Ledger persists; new worker invocation re-runs `notDoneFor(id)` |
| Disk full | Worker fails permanently; surface to user |
| Checksum mismatch | Delete file; mark failed; do not retry automatically |

---

## 8. Trade-offs

### Background scheduler

| Option | Use |
|---|---|
| **WorkManager** | Pick — survives reboot, constraints, retry, backoff |
| Foreground service | Add when user expects continuous progress with notification |
| AlarmManager | Lower-level; no constraints |
| `JobScheduler` (raw) | `WorkManager` wraps this; no benefit to use directly |

### Concurrency

| Choice | Pick |
|---|---|
| Parallel chunks per download | **3 (network dispatcher capped)** |
| Parallel downloads | **2 default, tunable** |
| Total HTTP connections | OkHttp `connectionPool` defaults are fine |

### Resume granularity

| Option | Verdict |
|---|---|
| **Chunk-level (file-per-chunk)** | Pick — easy ledger, easy resume |
| Byte-level append to one file | Possible but fragile if assembly truncates |
| Restart from zero | Awful UX for big files |

### HTTP client

| Option | Verdict |
|---|---|
| **OkHttp** | Pick — `Range`, connection pool, interceptors |
| Ktor 3 | Acceptable, KMP-friendly |
| Cronet | Faster on bad networks (Google's QUIC); heavier integration |
| `HttpURLConnection` | Don't |

### Storage

| Option | Use |
|---|---|
| App-private (`context.filesDir`) | Cache / non-user-visible |
| Scoped storage (Downloads collection) | User-visible files (`MediaStore`) |
| Pre-allocate with `setLength()` | Avoid file-system fragmentation on large files |

---

## 9. Major Concerns

- **Process death.** Ledger in Room is the truth. Worker invocation replays remaining chunks. No state in memory.
- **Disk space.** Check `StatFs.getAvailableBytes()` before starting; fail fast if not enough. Pre-allocate large files with `setLength()` for predictability.
- **Battery.** Use WorkManager constraints (`NetworkType.UNMETERED` for Wi-Fi-only). Foreground service only when user expects active progress.
- **Throttling.** Cellular: throttle to N MB/s if needed; surface a "downloading on cellular" banner.
- **OEM kill.** WorkManager survives. For user-initiated downloads use `setExpedited`; for prefetch use defaults.
- **Network changes.** `OkHttp` `connectionSpec` handles renegotiation; restart in-flight chunks if the local IP changes mid-stream.
- **Checksum.** SHA-256 verify on completion (optional). Mismatch = delete + fail.
- **Privacy.** Don't log URLs with auth tokens; redact in error reports.
- **Observability.** Total bytes, throughput, retry count surfaced via the same `EventListener` pattern.

---

## 10. Follow-up Questions

> **Q: How do you know the server supports Range?**
> HEAD request; check `Accept-Ranges: bytes`. If absent, fall back to single-chunk download.

> **Q: What if the user starts a 1 GB download and switches to cellular mid-stream?**
> Honour constraints: if `NetworkType.UNMETERED` was set, worker pauses (`Result.retry()` until constraint satisfied). Without constraint, continue but emit a warning event.

> **Q: How would you support a "pause" button?**
> `pause(id)` writes a flag in `DownloadEntity` + cancels the work. The worker checks the flag on each chunk boundary. Resume = new `WorkManager` enqueue with the same id; chunks not marked `DONE` re-fetch with their byte offsets.

> **Q: What about HTTPS without pinning?**
> Caller configures the OkHttp client. The library accepts a `Client` adapter; pinning, interceptors, timeouts are caller's concern.

> **Q: Memory footprint during download?**
> Streaming via Okio's `BufferedSource` / `BufferedSink`. No full-file in memory. Each chunk is a sequential write to its part file.

> **Q: How do you test this without a server?**
> `MockWebServer` from OkHttp; scripted responses (200, 206, 416, 5xx). Property-based test: any sequence of (network drop, resume) eventually produces a file matching the source bytes.

---

## 11. Out of Scope (defended)

- **DRM** — Widevine integration is its own world; ExoPlayer handles for streaming.
- **P2P** — different protocol stack entirely.
- **Cross-process queue** — single-app assumption.
- **Background upload** — symmetric but different concerns (chunked PUT, multipart).
- **Real-time mirroring** (a-la `rsync`) — out of mobile scope.

---

## 12. Further Reading

- [weeeBox/mobile-system-design — file-downloader-library](https://github.com/weeeBox/mobile-system-design/blob/master/exercises/file-downloader-library.md) — reference format.
- [Android Developers — WorkManager](https://developer.android.com/topic/libraries/architecture/workmanager) — official guide, expedited + constraints.
- [OkHttp recipes](https://github.com/square/okhttp/tree/master/samples/guide/src/main/java/okhttp3/recipes) — request examples, including headers and streaming.
- [Cronet / QUIC for Android](https://developer.android.com/develop/connectivity/cronet) — for next-gen transport.
- [Android Developers — Foreground services](https://developer.android.com/develop/background-work/services/foreground-services) — when to escalate from worker.

---

> **Closing in the interview:** "I anchored on the chunked resumable path because it's where every bug lives. Happy to dig into the pause/resume race, the checksum verification flow, or how priority preemption would work next."

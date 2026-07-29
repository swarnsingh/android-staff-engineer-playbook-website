# Caching Library

> A 45-60 minute mobile system-design walkthrough for designing a generic in-process caching library on Android. Think `LruCache` + disk fallback + invalidation: the kind of building block image loaders, network layers, and feature flag systems use underneath.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a caching library for a mobile app."
> **Candidate:** "Lots of products use a tiered memory + disk cache. The interesting tradeoffs are eviction policy, atomic disk writes, and how clients invalidate. I'll deep-dive the read/write path with both tiers."

### Functional Requirements
- **Two-tier**: in-memory + on-disk.
- **Generic types** via `Cache<K, V>` with a pluggable serializer.
- **TTL** per entry; expired reads return `null`.
- **Manual invalidate** by key and by predicate.
- **Bounded** by size (memory) and bytes (disk).

### Non-Functional Requirements
- **Thread-safe** (concurrent read/write).
- **Bounded** memory + disk; deterministic eviction.
- **Atomic disk writes** (no torn files on crash).
- **Trivial to test** — in-memory variant + fake clock.
- **No reflection at runtime** for performance.

### Out of Scope
- Distributed / cross-process cache (use `ContentProvider` if needed)
- Encryption at rest (delegate to consumer — they can wrap the serializer)
- Push-driven invalidation (server-driven; caller's problem)
- HTTP cache semantics (handled by OkHttp)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| What's the dominant access pattern (read-heavy, write-heavy)? | Eviction policy tradeoff |
| Median value size? | Disk format choice; memory budget |
| Acceptable cold read latency? | Sync vs async disk reads |
| Need observability (hit rate)? | Built-in metrics counter |
| Will it be used from multiple processes? | Lock model |
| Android API floor? | `LruCache` (4+), `DiskLruCache` (Jake Wharton fork or own) |
| Value types primitive or POJO? | Serializer interface |

> **Candidate:** "Assume single-process, read-heavy (~10:1), avg value 1-50 KB, sync API with coroutine wrappers, single-process, Android 9+."

---

## 3. High-Level Diagram (~10 min)

```
                   Cache<K, V>
                       │
              ┌────────┴────────┐
              ▼                 ▼
      MemoryCache (LRU)   DiskCache (bytes)
           |                 |
         maxSize           maxBytes
           |                 |
      LinkedHashMap     atomic write
                        + index file
```

**Layers (named for context):**
- **`Cache<K, V>`** — public API; orchestrates memory + disk; handles TTL.
- **`MemoryCache`** — `LruCache`-backed, hot tier.
- **`DiskCache`** — atomic writes, an index for O(1) lookup, byte-budget eviction.
- **`Serializer<V>`** — converts to/from `ByteArray` (default: `kotlinx.serialization`).
- **`Clock`** — injectable for tests.

---

## 4. API Contract

```kotlin
interface Cache<K : Any, V : Any> {
    suspend fun get(key: K): V?
    suspend fun put(key: K, value: V, ttl: Duration = Duration.INFINITE)
    suspend fun invalidate(key: K)
    suspend fun invalidateWhere(predicate: (K) -> Boolean)
    suspend fun clear()
    val stats: StateFlow<CacheStats>
}

data class CacheStats(
    val hits: Long, val misses: Long, val evictions: Long,
    val memoryBytes: Long, val diskBytes: Long,
)
```

### Builder

```kotlin
val cache = CacheBuilder<String, User>()
    .memorySize(maxEntries = 200)
    .diskSize(maxBytes = 50 * MB)
    .diskDir(context.cacheDir.resolve("user-cache"))
    .serializer(KotlinSerializer(User.serializer()))
    .ttl(default = 1.hours)
    .clock(SystemClock)
    .build()
```

---

## 5. Mobile App Architecture

### Module structure

```
:lib:cache
    cache-api          ← Cache interface, models
    cache-memory       ← MemoryCache impl
    cache-disk         ← DiskCache impl
    cache-default      ← composed Cache<K, V>
```

> Splitting the impls lets callers swap in a memory-only variant for tests without pulling the disk dependency.

### Layered diagram

```
              get(K)
               │
               ▼
       MemoryCache.get(K)  ── hit ──► return
               │
               miss
               ▼
        DiskCache.get(K)   ── hit ──► hydrate Memory, return
               │
               miss
               ▼
              null
```

---

## 6. Local Storage (Disk format)

Each entry is one file in the cache dir:

```
cacheDir/
├── index.bin                     ← (key → file, expiresAt, sizeBytes)
└── entries/
    ├── 8f7a...uuid
    └── ...
```

`index.bin` is rewritten atomically on flush. Entry files are written `.tmp` → `fsync` → `rename` for atomicity.

```kotlin
internal data class IndexRow(val key: String, val file: String,
                              val expiresAt: Long, val sizeBytes: Long)
```

> **Probing Q:** "Why not use Room?" Because the value is opaque bytes. Room is for queryable structured data. A bytes cache is simpler as files + an index.

---

## 7. Deep Dive: Read/Write Path with Two Tiers (~15 min)

> *I'd pick this as the deep dive because it covers the core orchestration: hit/miss propagation, eviction, atomic disk I/O, and TTL — the bits that decide whether the library is reliable.*

### Get path

```kotlin
override suspend fun get(key: K): V? {
    val stringKey = key.toString()
    memory.get(stringKey)?.let {
        if (it.notExpired(clock)) { stats.recordHit(); return it.value }
        memory.remove(stringKey)                // expired
    }
    val bytes = diskMutex.withLock { disk.get(stringKey) } ?: run {
        stats.recordMiss(); return null
    }
    if (bytes.isExpired(clock)) {
        diskMutex.withLock { disk.remove(stringKey) }
        stats.recordMiss(); return null
    }
    val value = serializer.deserialize(bytes.payload)
    memory.put(stringKey, MemoryEntry(value, bytes.expiresAt))   // promote
    stats.recordHit()
    return value
}
```

### Put path

```kotlin
override suspend fun put(key: K, value: V, ttl: Duration) {
    val stringKey = key.toString()
    val expiresAt = if (ttl == Duration.INFINITE) Long.MAX_VALUE
                    else clock.now() + ttl.inWholeMilliseconds
    memory.put(stringKey, MemoryEntry(value, expiresAt))
    diskScope.launch {                              // off the caller's coroutine
        val bytes = serializer.serialize(value)
        diskMutex.withLock {
            disk.put(stringKey, DiskEntry(bytes, expiresAt))
            disk.evictIfOverBudget()
        }
    }
}
```

> Disk write happens off the caller's coroutine. Reads see the value immediately via memory. If the process dies before the disk flush, we lose the cache entry — that's *acceptable* for a cache.

### Atomic disk write

```kotlin
internal fun writeAtomic(file: File, bytes: ByteArray) {
    val tmp = File(file.parentFile, "${file.name}.tmp")
    tmp.outputStream().use { it.write(bytes); it.fd.sync() }
    if (!tmp.renameTo(file)) error("rename failed")
}
```

### Eviction policies

| Tier | Policy | Why |
|---|---|---|
| Memory | LRU (LinkedHashMap accessOrder) | `LruCache` is built-in; predictable |
| Disk | Byte-budget LRU via index `lastAccessedAt` | Simple, deterministic; FIFO is too crude |

### TTL handling

- Entries carry `expiresAt` absolute timestamp.
- Checked on every read; expired entries removed lazily (cheap).
- No background sweeper — adds wakeups for no benefit.

### Concurrency

- `MemoryCache` is `LruCache` (synchronized).
- `DiskCache` is guarded by a `Mutex` (one writer at a time).
- Reads from disk parallelize via a coroutine dispatcher.

---

## 8. Trade-offs

### Memory tier impl

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **AndroidX `LruCache`** | Built-in, mature | Synchronized (lock contention) | Pick this |
| Caffeine | Best policies (TinyLfu) | JVM-heavy; KMP unfriendly | Skip for mobile |
| Custom LinkedHashMap | Total control | Reinvents `LruCache` | Skip |

### Disk tier impl

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **File per entry + index** | Simple, debuggable | Many small files (FS inode pressure) | Pick this |
| `DiskLruCache` (JW) | Battle-tested in OkHttp | Stale lib, key constraints | Acceptable |
| SQLite blob table | Atomic, transactional | Schema overhead for bytes | Skip |
| MMKV (Tencent) | Fast, mmap-based | Native lib; key-value only | Niche |

### Serializer

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **`kotlinx.serialization`** | Code-gen, KMP, fast | Caller must annotate | Pick (default) |
| Moshi/Gson | Familiar | Reflection or codegen, JVM only | Acceptable |
| Custom | Total control | Caller-burden | Always allowed via interface |

### Async model

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **`suspend` API** | Coroutine-native, structured concurrency | Caller must scope | Pick this |
| `Flow<V>` for reactive | Live updates | Overhead for one-shot reads | Use only for `stats` |
| Callbacks | Old habits | Manual cancellation | Skip |

---

## 9. Major Concerns

- **Crash safety.** Atomic rename for entries. Index rewrite is `tmp + rename`. Lose at most the last in-flight write.
- **OOM risk.** Memory tier uses `LruCache` with a *count* budget; size budget if values are large/heterogeneous. Don't unbound the memory tier.
- **Disk pressure.** Byte budget (e.g., 50 MB). Evict from oldest `lastAccessedAt`. Compact index on threshold.
- **Cold start.** Don't load the index on app launch synchronously. Lazy-load on first cache touch.
- **Serializer drift.** Versioned envelope: `{ "v": 2, "payload": ... }`. Unknown version → cache miss (don't crash).
- **Privacy.** Caller is responsible for not putting sensitive values; if required, offer a reviewed serializer that emits a versioned ciphertext envelope backed by a platform Keystore key.
- **Testing.** Inject `Clock`; use `MemoryCache` only in tests; assert hit rates.
- **Observability.** `CacheStats` `StateFlow` exposes hits/misses/evictions. Caller wires into telemetry SDK.

---

## 10. Follow-up Questions

> **Q: How do you handle a write while a read is in flight for the same key?**
> Memory `put` is atomic on `LruCache`. The disk write happens on a dispatched coroutine; if a read fires before the disk write completes, it gets the memory-tier value (which is newer). After the disk write, future cold reads see the new value.

> **Q: What about multi-process access?**
> Out of scope. If needed: switch the disk index to a `ContentProvider`-fronted SQLite table, or use MMKV with file locks. Don't bolt cross-process onto a single-process design.

> **Q: How do you avoid stampedes (many threads fetching the same missing key)?**
> Out of the library's scope, but recommend caller pattern: `coalesce` via a `Map<K, Deferred<V>>` so only one fetch happens per key. Optional helper utility ships in `cache-default`.

> **Q: TTL precision?**
> Millisecond. We don't try to wake at expiry — entries expire lazily on read. Background sweeper would burn battery; not worth it.

> **Q: How big should defaults be?**
> Memory: 1/8 of `Runtime.maxMemory()` if values are bitmaps; smaller (200 entries) for POJOs. Disk: 50 MB. Always overridable.

> **Q: How would Coil's image cache compare?**
> Coil uses the same shape — in-memory bitmap pool + disk bytes — but with bitmap-aware eviction (`sizeOf` per bitmap) and the Coil `MemoryCache.Builder().maxSizePercent(context, 0.25)` helper. Same architecture, image-specialised.

---

## 11. Out of Scope (defended)

- **Cross-process** — adds lock/IPC complexity; few apps need it.
- **Encryption at rest** — caller can wrap the serializer.
- **Distributed cache** — that's a server problem.
- **Push invalidation** — caller's domain event.
- **HTTP semantics** (`Cache-Control`, `Vary`, conditional requests) — OkHttp's cache exists for this.

---

## 12. Further Reading

- [weeeBox/mobile-system-design — caching-library](https://github.com/weeeBox/mobile-system-design/blob/master/exercises/caching-library.md) — reference format.
- [Android Developers — LruCache](https://developer.android.com/reference/kotlin/androidx/collection/LruCache) — canonical in-memory cache.
- [Jake Wharton — DiskLruCache](https://github.com/JakeWharton/DiskLruCache) — reference for the atomic-rename disk pattern.
- [Coil 3 — MemoryCache and DiskCache](https://coil-kt.github.io/coil/getting_started/) — image-loader take on the same shape.
- [Caffeine paper — Window TinyLfu](https://arxiv.org/abs/1512.00727) — for when LRU isn't enough.

---

> **Closing in the interview:** "I anchored on the get/put orchestration because the rest of the library is just policy. Happy to dig into stampede coalescing, the index rewrite scheme, or an MMKV variant next."

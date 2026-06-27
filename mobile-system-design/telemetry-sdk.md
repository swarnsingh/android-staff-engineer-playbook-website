# Telemetry SDK (Crash + Performance)

> A 45-60 minute mobile system-design walkthrough for a crash + performance telemetry SDK on Android: uncaught exception capture, ANR detection, frame metrics, network timing, durable upload. Product analytics is the previous file (`analytics-sdk.md`).

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a telemetry SDK like Firebase Crashlytics + perf monitoring."
> **Candidate:** "Two beasts in one box: crashes (one-shot, low volume, high value, can't fail) and perf metrics (high volume, statistical, OK to sample). I'll deep-dive crash capture + delivery because that's the highest-stakes path."

### Functional Requirements
- **Capture uncaught JVM exceptions** (Kotlin throws, Java errors).
- **Capture native crashes** (signal handler → minidump).
- **Detect ANR** (main thread blocked > 5s).
- **Frame metrics** (jank frames per session).
- **Startup time** (cold / warm / hot, time to first frame).
- **Network timing** (per request, via OkHttp event listener).

### Non-Functional Requirements
- **Crash report MUST persist** before the process exits.
- **Low overhead** — perf monitoring shouldn't cause jank itself.
- **Battery-conscious** — perf events bundle and flush like analytics.
- **Privacy-aware** — no PII; symbolicate stack traces server-side.
- **Compatible with proguard / R8** mapping files.

### Out of Scope
- Product events (see `analytics-sdk.md`)
- Real-time monitoring dashboard
- Symbol server / dSYM management
- Heap dumps on OOM (separate, heavy)
- Distributed tracing across server boundaries (see OpenTelemetry separately)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| In-house or wrap Crashlytics/Sentry? | Architecture vs SDK adapter |
| Native crashes in scope? | Need NDK signal handler |
| Sampling acceptable for perf? | Network volume, storage |
| Privacy / GDPR for crash payloads? | What to redact |
| Multi-tenant (in-house multiple apps)? | Endpoint routing |
| Android API floor? | FrameMetrics API availability, ANR APIs |
| Symbolication strategy? | Send mapping at upload-time vs server-resolved |

> **Candidate:** "In-house; JVM + native crashes; perf with 10% sampling; PII-scrubbed bodies; single app; Android 9+; server-side symbolication."

---

## 3. High-Level Diagram (~10 min)

```
   JVM Thread.UncaughtExceptionHandler  ─┐
   Signal handler (sigsegv etc.)        ─┤
   ANR watchdog                         ─┤
   FrameMetrics listener                ─┼─► EventBuffer (split: critical vs sampled)
   OkHttp EventListener                 ─┤                         │
   Startup tracer                       ─┘                         ▼
                                                            FlushScheduler
                                                                    │
                                                                    ▼
                                                            FlushWorker (WorkManager)
                                                                    │
                                                                    ▼
                                                            /v1/telemetry POST
```

**Components:**
- **`CrashCapture`** — `Thread.setDefaultUncaughtExceptionHandler` + NDK.
- **`AnrWatchdog`** — separate thread monitoring main responsiveness.
- **`PerformanceMonitor`** — `FrameMetrics`, startup, network.
- **`TelemetryQueue`** — Room-backed; crashes are persisted *synchronously*.
- **`FlushWorker`** — same shape as analytics, dedicated channel.

---

## 4. API Contract

### Crash payload

```json
{
  "type": "crash",
  "exception": "java.lang.NullPointerException",
  "message": "...",
  "thread": "main",
  "stackTrace": ["com.app.Foo.bar(Foo.kt:42)", "..."],
  "threads": { /* other thread states */ },
  "context": {
    "appVer": "4.12.1", "os": "Android 14", "device": "Pixel 7",
    "memoryMb": 4096, "diskFreeMb": 12000, "batteryPct": 47, "locale": "en-IN"
  },
  "breadcrumbs": [
    {"ts": 1750000000, "category": "nav", "msg": "screen=home"},
    {"ts": 1750000010, "category": "network", "msg": "GET /v1/feed 200 132ms"}
  ],
  "userId": "u_42", "anonId": "a_abc", "sessionId": "s_111",
  "buildId": "f3a2c9", "ts": 1750000020, "crashId": "c_uuid"
}
```

### Perf payload

```json
{
  "type": "perf",
  "metric": "frame_jank",
  "value": { "jankFrames": 14, "totalFrames": 1024, "p90Ms": 18.4 },
  "screen": "feed", "sessionId": "s_111", "ts": ...
}
```

### Network event (via OkHttp listener)

```json
{
  "type": "net",
  "url": "/v1/feed",            // scrubbed (no PII)
  "method": "GET", "code": 200,
  "tNetMs": 92, "tTotalMs": 132,
  "ts": ...
}
```

---

## 5. Mobile App Architecture

### Module structure

```
:lib:telemetry
    telemetry-api          ← Telemetry, Breadcrumbs
    telemetry-crash        ← CrashCapture, ANR watchdog
    telemetry-perf         ← FrameMetrics, network listener, startup
    telemetry-core         ← queue, scheduler, worker
```

### Layered diagram

```
   ┌─ JVM uncaught ─┐
   │                 │
   │ Signal handler ─┤
   │                 │
   │ ANR watchdog   ─┼─► CrashSink ─► Room (sync write)
   │                 │
   │ App code .leaveBreadcrumb()
   └─────────────────┘                       │
                                              ▼
                                       BreadcrumbBuffer (in-memory ring, 100)
                                              │ snapshot on crash
                                              ▼
   FrameMetrics ──► PerfSink ──► Room (async, sampled)
   OkHttp listener ──┘
                                              │
                                              ▼
                                       FlushScheduler
                                              │
                                              ▼
                                       FlushWorker → /v1/telemetry
```

### Key class signatures

```kotlin
object Telemetry {
    fun init(context: Context, config: TelemetryConfig)
    fun leaveBreadcrumb(category: String, message: String, data: Map<String, Any> = emptyMap())
    fun captureMessage(message: String, level: Level = Level.WARN)
    fun captureException(t: Throwable, level: Level = Level.ERROR)
    fun startTrace(name: String): Trace
    fun setUser(userId: String?)
}

interface Trace {
    fun stop()
    fun addAttribute(key: String, value: String)
}
```

---

## 6. Local Storage

```kotlin
@Entity(tableName = "telemetry_events", indices = [Index("priority", "ts")])
data class TelemetryEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val type: String,            // crash, anr, perf, net
    val priority: Int,           // 0 = critical (crash), 1 = high (anr), 2 = normal
    val payloadJson: String,
    val ts: Long
)
```

Crashes are written with a **synchronous** Room transaction in the uncaught handler — we have ~milliseconds before process death.

---

## 7. Deep Dive: Crash Capture + Delivery (~15 min)

> *I'd pick this as the deep dive because crash capture is binary: it works or it doesn't. Sampling doesn't apply; lost crashes hide bugs in production.*

### JVM crash capture

```kotlin
class CrashCapture(private val context: Context, private val sink: CrashSink) {
    private val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()

    fun install() {
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            try {
                sink.capture(
                    CrashEvent(
                        throwable = throwable,
                        thread = thread.name,
                        breadcrumbs = BreadcrumbBuffer.snapshot(),
                        context = currentContext()
                    )
                )
            } catch (e: Throwable) {
                // never throw inside the handler
            } finally {
                defaultHandler?.uncaughtException(thread, throwable)
            }
        }
    }
}
```

`CrashSink.capture` writes synchronously to Room *and* a fallback flat file (in case Room is mid-migration or holding a lock).

### CrashSink (sync write)

```kotlin
class CrashSink @Inject constructor(
    private val db: TelemetryDatabase,
    private val fileSink: FileCrashSink,
) {
    fun capture(event: CrashEvent) {
        val json = serializer.encodeToString(event.toWire())
        // Best-effort: Room first, file as fallback. Either is acceptable.
        runCatching {
            // Synchronous write; we may have milliseconds left.
            db.runInTransaction {
                db.telemetryDao().insertCriticalSync(TelemetryEntity(
                    type = "crash", priority = 0, payloadJson = json, ts = clock.now()
                ))
            }
        }.onFailure {
            fileSink.append(json)   // raw file in app's filesDir/crashes/
        }
    }
}
```

> The flat-file path is the safety net. On next app start, the SDK scans `filesDir/crashes/` and migrates entries into Room.

### Breadcrumbs (in-memory ring buffer)

```kotlin
object BreadcrumbBuffer {
    private const val CAPACITY = 100
    private val ring = ArrayDeque<Breadcrumb>(CAPACITY)
    private val lock = ReentrantLock()

    fun add(b: Breadcrumb) = lock.withLock {
        if (ring.size == CAPACITY) ring.removeFirst()
        ring.addLast(b)
    }
    fun snapshot(): List<Breadcrumb> = lock.withLock { ring.toList() }
}
```

Auto-breadcrumbs: nav, network (via OkHttp listener), screen lifecycle. App code adds custom ones with `Telemetry.leaveBreadcrumb`.

### ANR watchdog

```kotlin
class AnrWatchdog(private val threshold: Long = 5_000) : Thread() {
    private val handler = Handler(Looper.getMainLooper())
    override fun run() {
        while (!interrupted()) {
            val ack = AtomicBoolean(false)
            handler.post { ack.set(true) }
            sleep(threshold)
            if (!ack.get()) {
                val mainStack = Looper.getMainLooper().thread.stackTrace
                Telemetry.captureException(AnrException("Main blocked ${threshold}ms", mainStack))
            }
        }
    }
}
```

> Android 11+ exposes `ApplicationExitInfo` with `REASON_ANR`. Read on next launch as confirmation; the watchdog catches in-process; `ApplicationExitInfo` catches the system's view.

### Native crash capture (NDK)

Out of detailed scope here, but pattern: install a SIGSEGV/SIGBUS handler in JNI, write a minidump to `filesDir/native_crashes/`. JVM SDK reads these on launch. Tools: `breakpad`, `crashpad`, or Sentry's NDK.

### Delivery on next launch

```kotlin
class TelemetryDeliveryBootstrapper @Inject constructor(
    private val migrator: FileToRoomMigrator,
    private val workManager: WorkManager,
) {
    fun onAppStart() {
        migrator.migratePending()         // flat files → Room
        workManager.enqueueUniqueWork(
            "telemetry-flush", ExistingWorkPolicy.KEEP,
            OneTimeWorkRequestBuilder<FlushWorker>()
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build()
        )
    }
}
```

### Flush worker (prioritizes crashes)

```kotlin
@HiltWorker
class FlushWorker @AssistedInject constructor(...) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        // 1. Critical first (priority=0)
        flushBatch(dao.takeByPriority(0, limit = 50))?.let { if (!it.isSuccess) return it }
        // 2. High (ANR)
        flushBatch(dao.takeByPriority(1, limit = 50))?.let { if (!it.isSuccess) return it }
        // 3. Normal (perf, net)
        flushBatch(dao.takeByPriority(2, limit = 200))?.let { if (!it.isSuccess) return it }
        return Result.success()
    }
}
```

### Performance traces

```kotlin
class FrameMetricsCapture(activity: Activity) {
    init {
        activity.window.addOnFrameMetricsAvailableListener({ _, fm, _ ->
            val totalNs = fm.getMetric(FrameMetrics.TOTAL_DURATION)
            if (totalNs > 16_700_000) {     // > 16.7ms = jank at 60Hz
                PerfBuffer.addJank(totalNs)
            }
        }, Handler(Looper.getMainLooper()))
    }
}
```

Sample at 10% of sessions; aggregate per-screen at session end; flush.

### Network timing (OkHttp event listener)

```kotlin
class NetTelemetryListener : EventListener() {
    private val timers = ConcurrentHashMap<Call, Long>()
    override fun callStart(call: Call) { timers[call] = clock.now() }
    override fun callEnd(call: Call) {
        val start = timers.remove(call) ?: return
        Telemetry.recordNet(call.request().url, clock.now() - start, code = lastCode)
    }
}
```

### Failure modes

| What breaks | Behavior |
|---|---|
| Process dies before Room write | File-sink fallback catches it |
| Room is corrupted | File-sink only |
| Network unavailable on next launch | Worker retries indefinitely with backoff |
| Server returns 400 | Drop offender (bad schema); continue |
| Disk full | Trim oldest perf; never trim crashes |
| Mapping file mismatch | Server symbolicates with whatever buildId is sent; may show obfuscated names |

---

## 8. Trade-offs

### In-house vs vendor (Crashlytics, Sentry)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **In-house** | Privacy, custom routing, control | Build + maintain | Pick if scale + privacy demand it |
| **Crashlytics** | Free, integrated with Firebase | Vendor lock, limited custom fields | Default for small teams |
| **Sentry** | Best-in-class, OSS option | Cost at scale | Pick for mid-size teams |

### Storage for crashes

| Option | Verdict |
|---|---|
| **Room with sync transaction + file fallback** | Pick — safest |
| Files only | Loses transactional semantics for the rest of the queue |
| Room only | Risky if DB is locked at crash time |

### Symbolication

| Option | Verdict |
|---|---|
| **Server-side with uploaded mapping** | Pick — keeps client small |
| Client-side symbolication | Wastes battery, requires mapping on device (security risk) |
| No symbolication | Useless |

### Perf sampling

| Option | Verdict |
|---|---|
| **10% session sampling** | Pick — bounded volume |
| Per-event sampling | Less statistical signal |
| 100% perf events | Overkill, expensive |

### Frame metrics

| Source | Verdict |
|---|---|
| **`FrameMetrics` API** | Pick — official, accurate |
| `Choreographer` callback | DIY; reinvents wheel |
| `JankStats` (AndroidX) | Pick — wraps the above, easier |

---

## 9. Major Concerns

- **Crash atomicity.** Must persist before exit. File fallback covers the Room-locked edge.
- **Reentrancy.** Uncaught handler must never throw — guard with `runCatching`.
- **Privacy.** Strip query parameters from URLs; redact known PII keys in breadcrumbs.
- **Mapping.** Upload R8 / ProGuard mapping per release. Server stores by `buildId`.
- **NDK crashes.** Need a signal handler installed; not in this code but architecturally a peer to JVM capture.
- **ANR vs slow operation.** 5s is a hard ANR threshold; we want to capture before the system dialog.
- **Battery.** Perf monitoring should be opt-in or sampled. Don't always-on.
- **Stack trace integrity.** Server must store mapping for at least N versions back (last 12 months typical).
- **Compliance.** "Right to be forgotten" — delete by `userId` server-side.

---

## 10. Follow-up Questions

> **Q: How are crashes deduped?**
> Server fingerprint = SHA-256(class + top frame + message). Crashes with the same fingerprint group into an "issue". Counts + affected users update per issue.

> **Q: What about OOM that kill the process suddenly?**
> JVM `OutOfMemoryError` is an exception → caught. Native OOM (Low Memory Killer) is silent; we detect on next launch via `ApplicationExitInfo` (Android 11+).

> **Q: How do you avoid losing a crash if the app crashes again during write?**
> File sink is append-only — partial writes are recoverable by skipping malformed JSON lines.

> **Q: What's the perceived impact on app size?**
> Telemetry SDK ~150 KB stripped (JVM-only). With NDK signal handler, +250 KB. Crashlytics is ~600 KB; in-house can be leaner.

> **Q: How do you test crash capture?**
> `throw RuntimeException("test")` from a debug button. Verify Room row appears post-restart. CI: instrumented test that triggers a crash and checks the persisted artifact.

> **Q: Can the telemetry SDK report on itself?**
> Yes — internal "self-monitoring" events (worker failures, queue overflow) emit as `type=telemetry_internal`. Watch them carefully; they predict outages.

---

## 11. Out of Scope (defended)

- **Product events** — `analytics-sdk.md`.
- **Heap dumps** — heavy, requires symbolication of memory addresses.
- **Distributed tracing** — server domain.
- **Real-time dashboards** — telemetry consumer side.
- **Vendor SDK adapter** — pattern: thin wrapper, route events to chosen vendor.

---

## 12. Further Reading

- [Android Developers — JankStats library](https://developer.android.com/topic/performance/jankstats) — official frame-metrics wrapper.
- [Android Developers — ApplicationExitInfo](https://developer.android.com/reference/android/app/ApplicationExitInfo) — system-level exit reasons (API 30+).
- [Crashlytics Android docs](https://firebase.google.com/docs/crashlytics) — reference implementation.
- [Sentry Android SDK](https://docs.sentry.io/platforms/android/) — open-source alternative.
- [Microsoft AppCenter mobile diagnostics](https://learn.microsoft.com/appcenter/diagnostics/) — for comparison.

---

> **Closing in the interview:** "I anchored on crash capture because zero data loss is the SDK's job-one promise. Happy to dig into NDK signal handlers, perf-sampling strategies, or the symbolication pipeline next."

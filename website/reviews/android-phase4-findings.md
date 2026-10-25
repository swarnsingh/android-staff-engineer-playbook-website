# Android Phase 4: possible errors in the original chapters

Found while writing the teaching layer for Android Phase 4 (concurrency and background execution: the nine chapters listed in Phase 4 of `android.md`). These are **findings for the owner's review**, not approved corrections. The original Markdown is unchanged and nothing has been added to `content/corrections-*.json`.

Each finding is shown on its page as an **Under review** note before the section that contains it. The note identifies the passage and says a correction is pending; it does not print the replacement.

**Verification method:** MX2 was compiled with Kotlin 2.4.21 because it is a language rule. Everything else was checked against official documentation or a well-established library contract, as cited. Android framework code was not compiled. Checked on 2026-10-25.

| ID | Chapter, section | Original says | Problem | Evidence |
|---|---|---|---|---|
| SC1 | Structured Concurrency, Historical Context | Structured concurrency is "implemented in languages like Go" | Go's `go` statement starts unstructured goroutines; the essay that popularised the term is titled "…Go statement considered harmful" | N. J. Smith, [Notes on structured concurrency, or: Go statement considered harmful](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) (2018) |
| SC2 | Structured Concurrency, Tradeoffs (`supervisorScope` example) | A child `launch` inside `supervisorScope` that "Fails!", with no handling | Supervised children must handle their own exceptions; otherwise the scope's `CoroutineExceptionHandler` is used like a root coroutine's, and with none, Android's default uncaught-exception handler crashes the app | [Kotlin: exceptions in supervised coroutines](https://kotlinlang.org/docs/exception-handling.html) |
| TL1 | Threads and Looper, Answer Key 9 | `quitSafely()` lets "all currently pending messages" finish | `quitSafely()` handles messages that are already due; delayed messages due in the future are not delivered | [`Looper.quitSafely()` reference](https://developer.android.com/reference/android/os/Looper#quitSafely()) |
| MX1 | Synchronization and Mutex, The Toolbelt (`@Volatile`) | `@Volatile` makes the JVM "skip the CPU cache and read/write directly to main RAM" | Volatile gives visibility and ordering through happens-before edges in the Java Memory Model; it is not a cache-bypass instruction, and caches stay coherent in hardware | JLS §17.4.5 (happens-before order); the Kotlin tree's Memory Model chapter |
| MX2 | Synchronization and Mutex, Failure Modes ("Using `synchronized` in a Coroutine") and Answer Key 4 | Calling a suspending `networkCall()` inside `synchronized(this) { }` suspends while holding the monitor | Kotlin rejects a suspension point inside `synchronized` at compile time | Compiled with Kotlin 2.4.21: "the 'networkCall' suspension point is inside a critical section" |
| SV1 | Services, Production Example | `flow { withContext(Dispatchers.IO) { … emit(progress) } }` | Emitting from a different context inside `flow { }` violates Flow's context preservation and throws `IllegalStateException`; the documented fix is `flowOn` | [kotlinx.coroutines `flow` builder: context preservation](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow.html) |
| BO1 | Battery Optimizations, Tradeoffs | "starting in Android 14, you must explicitly declare the `SCHEDULE_EXACT_ALARM` permission"; Play rejects apps that are not alarm or calendar apps | The exact-alarm permission arrived in Android 12. Android 14 denies `SCHEDULE_EXACT_ALARM` by default for most newly installed apps targeting 13+. Play's restriction concerns `USE_EXACT_ALARM` | [Android 12: exact alarm permission](https://developer.android.com/about/versions/12/behavior-changes-12#exact-alarm-permission); [Android 14: schedule exact alarms denied by default](https://developer.android.com/about/versions/14/changes/schedule-exact-alarms) |

## Smaller notes (not flagged on the pages)

- **Flow, Mental Model:** describes cancellation travelling up the pipes as "backpressure". The behaviour is cancellation; backpressure is a slow collector suspending the producer.
- **Flow, Tradeoffs:** says `StateFlow` "requires `collectAsStateWithLifecycle` … to avoid memory leaks". The benefit is avoiding off-screen work, not a leak.
- **Flow, History:** says `LiveData` operates "exclusively on the main thread". `postValue` works from any thread; observers run on main.
- **Services, History:** says Android 12 "banned starting a Foreground Service from the background entirely". There are documented exemptions, for example high-priority FCM.
- **WorkManager, Staff Note:** says expedited jobs arrived "Since Android 12". The expedited-work API comes from WorkManager 2.7 and runs as a foreground service on earlier Android versions.
- **WorkManager, Production Example:** `catch (e: Exception) { Result.failure() }` also catches the cancellation that happens when work is stopped.
- **Battery Optimizations:** the bucket restrictions ("No internet access" for Rare) and the "once every 9 minutes" rate limit were not re-verified against the current Doze and App Standby pages.

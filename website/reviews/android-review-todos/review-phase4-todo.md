# Phase 4 review: fixes to apply

From the review subagent, 2026-10-25. Build in a /tmp copy: 65 pages, 8,555 units, 0 problems. All seven findings (SC1–BO1) confirmed; SV1 and SC2 confirmed by run. Nothing applied yet.

## P1

1. **synchronization-and-mutex.blend:27**: the stepper caption states the MX2 correction as fact ("Kotlin also rejects suspension points inside synchronized at compile time"). Remove it or move it to `reviews/pending-android-teaching.blend`.
2. **services.blend:22, new finding SV2**: step 3 correctly names Android 12 background-start exemptions, but the original contradicts it unflagged at `services.md:23` (History, "banned entirely"), `:164-165` (Failure Modes, FCM, then startForegroundService "will immediately crash"), `:206-207` (Answer 4). High-priority FCM is a listed exemption (developer.android.com/develop/background-work/services/fgs/restrictions-bg-start). Add SV2 with notes before History, Failure Modes and Answer Key; remove the exemption wording from step 3 until approved.

## P2

- **threads-and-looper.blend:7, :24**: invented crash. The original example (`textView.text = "Done"`) is a leak; the story should be a leak (old activity held 10 minutes), or use a dialog on a destroyed activity (`BadTokenException`).
- **battery-optimizations.blend:19, :25, :35**: "Everything else waits" is wrong: `setAlarmClock()` and `setAndAllowWhileIdle()` fire; partly exempt apps can use the network. FCM docs now describe v1 high priority as deprecated; v2 uses `RemoteNotification` (AndroidConfigV2). Name `setAlarmClock`, soften, mention v2.
- **Missing notes**: SC2 also before Staff Engineer Thinking (`structured-concurrency.md:176`); MX1 also before First Principles (`synchronization-and-mutex.md:26`); BO1 also before Probing Questions and Answer Key (`battery-optimizations.md:154,170-171`).
- **Promote smaller notes to findings with page notes**: Flow LiveData "exclusively on the main thread" (`flow.md:23,125`); cancellation called "backpressure" (`flow.md:43`); WorkManager Staff Note on expedited work (WorkManager 2.7.0; foreground service before Android 12).
- **synchronization-and-mutex.blend:49-51**: checkpoint 3 echoes per-call confinement as fast; kotlinlang says fine-grained confinement "works very slowly". Say coarse-grained, or drop; add a finding for `synchronization-and-mutex.md:157`.
- **structured-concurrency.blend:44**: swallowed cancellation: "keeps running until its next suspension point, then is cancelled again; cleanup or retry logic in between runs as if nothing happened."

## New original findings (add to findings file, notes on pages)

1. `workmanager.md:147-148,200`: missing factory binding does not crash; WorkerWrapper logs "Could not create Worker" and fails the work.
2. `synchronization-and-mutex.md:111-128`: no `finally`, so `isUploading` sticks and the cleared batch is lost on failure.
3. `services.md:114,143`: a local Binder cannot be exposed to another app via IPC; `lifecycleScope` note does not govern the returned Flow.
4. `services.md:211`: since Android 14 users can dismiss FGS notifications.
5. `services.md:24`: "crash if you declare location but don't request GPS" unsupported; permissions are checked at `startForeground()`.
6. `battery-optimizations.md:83`: "only way to pierce Doze" contradicts its Tradeoffs and the Doze page.
7. `battery-optimizations.md:141`: since Android 13 buckets no longer limit high-priority FCM.
8. `coroutines-under-the-hood.md:57`, Answer 2: parameter is `Continuation<? super T>`, return `Any?` (javap).
9. `shared-flow-and-state-flow.md:463-477`: `incrementsAtomically` passes with read-modify-write code.
10. `synchronization-and-mutex.md:11`: tearing on an int is not possible (JLS §17.7: only non-volatile long/double).
- Unresolved: `battery-optimizations.md:146` vs `workmanager.md:140` contradict on FGS network in Doze; worth a finding. `structured-concurrency.md:13` "crash when handed back to a dead UI" has the same pattern as the Looper defect.

## P3

- structured-concurrency.blend:24 add "and the supervised child must still handle it"; :23 "fetch posts" node is cancelled-styled but says "done".
- coroutines-under-the-hood.blend:42 "cannot respond to cancellation; it and its parent stay suspended until the callback fires"; :37 "None runs in parallel" unless calls switch to IO.
- threads-and-looper.blend:30 "the main thread's queue" not "the main Handler"; :9 "Everything … is a message" simplification.
- flow.blend:47 `repeatOnLifecycle` must run in a launched coroutine.
- shared-flow-and-state-flow.blend:22 "navigates twice" only with an activity-level collector; :35 mention StateFlow for latest-only price ticks.
- workmanager.blend:36-38 KEEP keys on unique name, not an identical request.
- services.blend:40 "guaranteed to run" vs force-stop; :14, :20 targetSdk 26+ / 34+ qualifiers; :25 main-thread work causes ANR.
- Findings file header: record SV1 as confirmed by run.

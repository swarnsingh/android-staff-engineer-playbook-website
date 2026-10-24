# Flow operators and channels audit

Reviewed 2026-10-25 for the website adaptation. Read both `kotlin/coroutines-and-flow/flow-operators-and-backpressure.md` and `kotlin/coroutines-and-flow/channels-and-select.md` in full. Canonical Markdown remains unchanged.

The 17 exact corrections are in `website/content/corrections-flow-channels.json`. Each original excerpt matches exactly once, including when the overlays are applied sequentially. The chapter topics, examples, questions and teaching sequence remain represented.

## Confirmed corrections

The original flowOn explanation said every invocation adds concurrency and moves everything upstream. The documented contract is narrower: preceding operators without their own context are affected, a same-dispatcher context change can stay sequential, and adjacent channel/flowOn/buffer operators fuse. The replacement preserves the dispatcher example while explaining those boundaries.

The terminal table incorrectly treats every hot Flow as noncompleting. StateFlow and SharedFlow do not complete normally, but receiveAsFlow can finish when its channel closes and drains. first() throws on a finite flow that completes without a matching element. Sample's final-window drop and buffer capacity's distinction from total in-flight work are made explicit. WhileSubscribed's stopped-upstream/cached-value behavior is stated beside the UI example.

Channel closure now distinguishes rejecting future sends from already-suspended sends, which close does not abort. Send suspension is qualified by the overflow strategy. The frame-handoff fragment explicitly identifies missing owner/resource-release responsibilities rather than promising that the queue alone preserves every camera frame.

The CartActor example started work in its constructor and could leave checkout() waiting on an incomplete reply after the worker failed or was cancelled. Its replacement exposes a suspending run() started once by the lifecycle owner, returns expected I/O failure through the reply, preserves cancellation/unexpected failures, releases the active reply in finally, and cancels queued reply commands through onUndeliveredElement when the worker ends. The caller releases its own reply if it stops waiting. This does not imply rollback of an already-started backend checkout; the prose retains idempotency/durable-progress requirements.

The runCatching worker example now preserves CancellationException. The QueueWorker test uses runCurrent for immediate backgroundScope work; advanceUntilIdle can stop without running that work when only background tasks remain.

## Executed evidence

Used cached Kotlin/JVM compiler 2.2.21, OpenJDK 17.0.19 and official Maven Central kotlinx-coroutines-core-jvm/test-jvm 1.10.2 artifacts. No Gradle project or canonical file was changed. A plain JVM fixture compiled successfully and all checks passed:

- A bounded Channel worker in backgroundScope had processed `[]` after advanceUntilIdle, then `[1, 2]` after runCurrent.
- The corrected CartActor delivered an expected IOException to its waiting caller and successfully handled a later checkout.
- Cancelling the actor worker released an active checkout reply with cancellation.
- A same-dispatcher flowOn(CoroutineName(...)) retained the collector's Job, demonstrating that flowOn does not universally create another coroutine.
- A closed, drained channel's receiveAsFlow().toList() completed with its queued element.
- emptyFlow<Int>().first() threw NoSuchElementException.

Temporary fixture and results are in `/tmp/kotlin-flow-channel-audit`; library artifacts are in `/tmp/kotlin-audit-libs`. These temporary paths are not dependencies of the website or review pack.

## Primary sources

- [flowOn context, concurrency, cancellation and fusion](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html)
- [Buffer contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/buffer.html)
- [combine](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/combine.html)
- [sample](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/sample.html)
- [first](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/first.html)
- [receiveAsFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/receive-as-flow.html)
- [SharedFlow completion contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)
- [WhileSubscribed](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/-companion/-while-subscribed.html)
- [backgroundScope test scheduling](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-scope/background-scope.html)
- [Channel cancellation and undelivered elements](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/)
- [Channel close](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-send-channel/close.html)

## Limits

This is a bounded audit with targeted executions, not proof that every Android-shaped fragment compiles in a production app. Flow examples with app-defined SearchResult, ProfileUiState and DAO APIs still depend on those stated application contracts. No claim is made that the frame example configures a real camera, that a queue is durable, or that all possible channel cancellation races have been exhaustively tested. No confirmed Flow covariance compile error was found in the typed map examples: Kotlin Flow's covariance makes the declared wider result types valid; inventing such a correction would reduce accuracy.

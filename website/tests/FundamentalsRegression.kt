import kotlinx.coroutines.*
import java.io.IOException

/* EXACT_CORRECTED_FRAGMENTS */

fun main() = runBlocking {
    var checks = 0
    fun expect(condition: Boolean) { check(condition); checks++ }

    val a = LamportClock()
    val b = LamportClock()
    expect(a.tick() == 1L)
    val sent = a.send()
    expect(sent == 2L)
    b.receive(sent)
    expect(b.tick() == 4L)
    expect(a.tick() == 3L) // B's local tick did not mutate A.

    val left = VectorClock(0, 2)
    val right = VectorClock(1, 2)
    val leftEvent = left.send() // [1, 0]
    expect(!left.concurrent(leftEvent))
    expect(!left.happenedBefore(leftEvent)) // equal vectors are not ordered or concurrent.
    val rightEvent = right.send() // [0, 1]
    expect(left.concurrent(rightEvent))
    expect(right.concurrent(leftEvent))
    right.receive(leftEvent) // [1, 2]
    val joined = right.send() // [1, 3]
    expect(left.happenedBefore(joined))
    expect(!right.concurrent(leftEvent))
    leftEvent[0] = 99 // send returned a copy, not mutable access to internal state.
    expect(left.send()[0] == 2L)
    expect(runCatching { left.receive(longArrayOf(1)) }.isFailure)
    expect(runCatching { VectorClock(2, 2) }.isFailure)

    val hlc = HybridLogicalClock()
    val remoteFuture = System.currentTimeMillis() + 60_000
    val merged = hlc.receive(HLC(remoteFuture, 8))
    expect(merged.physicalTime == remoteFuture && merged.logicalCounter == 9)
    val localBehind = hlc.now()
    expect(localBehind.physicalTime == remoteFuture && localBehind.logicalCounter == 10)
    val equalPhysical = hlc.receive(HLC(remoteFuture, 20))
    expect(equalPhysical.physicalTime == remoteFuture && equalPhysical.logicalCounter == 21)
    val olderMessage = hlc.receive(HLC(remoteFuture - 1, 99))
    expect(olderMessage.physicalTime == remoteFuture && olderMessage.logicalCounter == 22)

    val lru = LRUCache<String, Int>(2)
    lru.put("a", 1); lru.put("b", 2)
    expect(lru.get("a") == 1)
    lru.put("c", 3)
    expect(lru.get("b") == null && lru.get("a") == 1 && lru.get("c") == 3)
    val empty = LRUCache<String, Int>(0)
    empty.put("a", 1)
    expect(empty.get("a") == null)

    var attempts = 0
    val value = withRetry(maxAttempts = 3, initialDelayMs = 1, maxDelayMs = 2) {
        attempts++
        if (attempts < 3) throw IOException("retryable test failure")
        42
    }
    expect(value == 42 && attempts == 3)
    attempts = 0
    val finalFailure = runCatching {
        withRetry(maxAttempts = 2, initialDelayMs = 1, maxDelayMs = 1) {
            attempts++
            throw IOException("exhausted")
        }
    }.exceptionOrNull()
    expect(finalFailure is IOException && attempts == 2)
    attempts = 0
    val classified = runCatching {
        withRetry(maxAttempts = 3, initialDelayMs = 1, maxDelayMs = 1, shouldRetry = { false }) {
            attempts++
            throw IOException("nonretryable")
        }
    }.exceptionOrNull()
    expect(classified is IOException && attempts == 1)
    expect(runCatching { withRetry(maxAttempts = 0) { 1 } }.isFailure)
    expect(runCatching { withRetry(initialDelayMs = 0) { 1 } }.isFailure)
    expect(runCatching { withRetry(initialDelayMs = 2, maxDelayMs = 1) { 1 } }.isFailure)

    val entered = CompletableDeferred<Unit>()
    var cancelledAttempts = 0
    val job = launch {
        withRetry(maxAttempts = 100, initialDelayMs = 1, maxDelayMs = 1) {
            cancelledAttempts++
            entered.complete(Unit)
            awaitCancellation()
        }
    }
    entered.await()
    job.cancelAndJoin()
    expect(job.isCancelled && cancelledAttempts == 1)
    println("{\"assertions\":$checks,\"contracts\":[\"Lamport message/local separation\",\"vector equality/concurrency/shape/snapshot\",\"HLC future merge/local clock behind\",\"LRU access eviction\",\"retry attempts/classification/validation/cancellation\"]}")
}

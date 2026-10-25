// Test fixtures for the exact CH4 proposal, inserted by check_kotlin_examples.py.
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*
import kotlinx.coroutines.test.*
import java.io.IOException

typealias ItemId = Int
data class Item(val id: ItemId)
data class CheckoutResult(val value: String)
class CheckoutService(private val operation: suspend () -> CheckoutResult) {
    suspend fun submit(items: List<Item>): CheckoutResult = operation()
}

/* ACTOR_FROM_PROPOSAL */

@JvmInline value class Meters(val value: Double)
fun <T> twice(value: T) = listOf(value, value)

@OptIn(ExperimentalCoroutinesApi::class)
fun main() = runTest {
    var passed = 0
    suspend fun outcome(actor: CartActor): String = try {
        actor.checkout().value
    } catch (error: Exception) {
        error.javaClass.simpleName
    }
    suspend fun stopped(actor: CartActor) {
        val result = withTimeout(1_000) { outcome(actor) }
        check(result.endsWith("CancellationException")) { "Stopped actor returned $result" }
    }
    fun ownerScope(owner: Job) = CoroutineScope(owner + StandardTestDispatcher(testScheduler))

    // Expected I/O failure fails one request and does not poison the worker.
    val normalOwner = SupervisorJob()
    var attempts = 0
    val normal = CartActor(ownerScope(normalOwner), CheckoutService {
        if (attempts++ == 0) throw IOException("expected")
        CheckoutResult("ok")
    })
    val failed = async { outcome(normal) };runCurrent()
    check(failed.await() == "IOException")
    val recovered = async { outcome(normal) };runCurrent()
    check(recovered.await() == "ok")
    normalOwner.cancel();runCurrent();stopped(normal);passed++

    // Cancel before the first dispatch: worker body and its finally never run.
    val earlyOwner = SupervisorJob()
    val early = CartActor(ownerScope(earlyOwner), CheckoutService { error("must not run") })
    earlyOwner.cancel();runCurrent();stopped(early)
    check(runCatching { early.add(Item(1)) }.exceptionOrNull() is CancellationException)
    passed++

    // A caller can construct the actor after its owner was already cancelled.
    val deadOwner = SupervisorJob();deadOwner.cancel()
    val dead = CartActor(ownerScope(deadOwner), CheckoutService { error("must not run") })
    runCurrent();stopped(dead);passed++

    // Requests accepted before cancellation must also be released when startup is prevented.
    val queuedOwner = SupervisorJob()
    val queuedActor = CartActor(ownerScope(queuedOwner), CheckoutService { error("must not run") })
    val beforeStartup = async(start = CoroutineStart.UNDISPATCHED) { outcome(queuedActor) }
    queuedOwner.cancel();runCurrent()
    check(withTimeout(1_000) { beforeStartup.await() }.endsWith("CancellationException"));passed++

    // Stop one active request plus enough submissions to fill the buffer and suspend senders.
    val liveOwner = SupervisorJob()
    val entered = CompletableDeferred<Unit>()
    val live = CartActor(ownerScope(liveOwner), CheckoutService {
        entered.complete(Unit);awaitCancellation()
    })
    val active = async { outcome(live) };runCurrent();check(entered.isCompleted)
    val pending = List(256) { async { outcome(live) } };runCurrent()
    check(pending.none { it.isCompleted })
    liveOwner.cancel();runCurrent()
    val results = withTimeout(1_000) { (listOf(active) + pending).awaitAll() }
    check(results.all { it.endsWith("CancellationException") }) { results.toString() }
    stopped(live);passed++

    // Unexpected errors retain their reporting path and still release all waiters.
    val unexpectedOwner = SupervisorJob()
    val errors = mutableListOf<Throwable>()
    val handler = CoroutineExceptionHandler { _, error -> errors += error }
    val unexpected = CartActor(ownerScope(unexpectedOwner) + handler, CheckoutService { error("unexpected") })
    val broken = async { outcome(unexpected) };runCurrent()
    check(broken.await() == "IllegalStateException")
    check(errors.single().message == "unexpected")
    stopped(unexpected);unexpectedOwner.cancel();passed++

    // Regression for the teaching claim: two slots may share one boxed value.
    val boxed: List<*> = twice(Meters(1.0))
    check(boxed[0] === boxed[1]);passed++
    println("Kotlin regressions: $passed cases passed (including 257 active/queued/suspended requests).")
}

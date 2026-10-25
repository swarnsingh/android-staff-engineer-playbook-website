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
    // Service-local timeout must not kill an otherwise active actor.
    run {
        val owner = SupervisorJob()
        var calls = 0
        val actor = CartActor(CoroutineScope(owner + StandardTestDispatcher(testScheduler)), CheckoutService {
            if (calls++ == 0) withTimeout(1) { delay(10) }
            CheckoutResult("recovered")
        })
        val first = async { runCatching { actor.checkout() }.exceptionOrNull() }
        advanceUntilIdle()
        val second = async { runCatching { actor.checkout() }.getOrNull()?.value }
        advanceUntilIdle()
        println("Timeout probe: first=${first.await()?.javaClass?.simpleName}, second=${second.await()}, ownerActive=${owner.isActive}")
        check(second.await() == "recovered") { "Service-local timeout killed the actor" }
        check(first.await() is CheckoutRequestCancelledException)
        check(first.await()?.cause is TimeoutCancellationException)
        owner.cancel();runCurrent();passed++
    }
    suspend fun outcome(actor: CartActor): String = try {
        actor.checkout().value
    } catch (error: Exception) {
        error.javaClass.simpleName
    }
    suspend fun stopped(actor: CartActor) {
        val result = withTimeout(1_000) { outcome(actor) }
        check(result == "CartStoppedException") { "Stopped actor returned $result" }
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
    check(runCatching { early.add(Item(1)) }.exceptionOrNull() is CartStoppedException)
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
    check(withTimeout(1_000) { beforeStartup.await() }.equals("CartStoppedException"));passed++

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
    check(results.all { it.equals("CartStoppedException") }) { results.toString() }
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

    // A cancellation thrown by a service while the worker stays active is a request error.
    val localOwner = SupervisorJob()
    var localCalls = 0
    val local = CartActor(ownerScope(localOwner), CheckoutService {
        if (localCalls++ == 0) throw CancellationException("service cancelled its work")
        CheckoutResult("ok")
    })
    val localFailure = async { outcome(local) };runCurrent()
    check(localFailure.await() == "CheckoutRequestCancelledException")
    val localRecovery = async { outcome(local) };runCurrent();check(localRecovery.await() == "ok")
    localOwner.cancel();runCurrent();passed++

    // An independent UI caller must display actor shutdown, not silently cancel itself.
    val uiOwner = SupervisorJob()
    val uiScope = ownerScope(uiOwner)
    val serviceOwner = SupervisorJob()
    val uiEntered = CompletableDeferred<Unit>()
    val uiActor = CartActor(ownerScope(serviceOwner), CheckoutService { uiEntered.complete(Unit);awaitCancellation() })
    var shownError: Throwable? = null
    val uiCaller = uiScope.launch {
        try { uiActor.checkout() }
        catch (error: Exception) {
            if (error is CancellationException) throw error
            shownError = error
        }
    }
    runCurrent();check(uiEntered.isCompleted)
    serviceOwner.cancel();runCurrent();uiCaller.join()
    check(!uiCaller.isCancelled && uiOwner.isActive && shownError is CartStoppedException)
    // Already-stopped sends from active callers also use an ordinary failure.
    val newCall = uiScope.launch {
        try { uiActor.add(Item(2));error("must fail") }
        catch (error: Exception) {
            if (error is CancellationException) throw error
            check(error is CartStoppedException)
        }
    }
    runCurrent();newCall.join();check(!newCall.isCancelled)
    uiOwner.cancel();passed++

    // Cancelling the caller itself remains cancellation, without cancelling the actor owner.
    val callerOwner = SupervisorJob()
    val callerActor = CartActor(ownerScope(callerOwner), CheckoutService { delay(100);CheckoutResult("ok") })
    val caller = launch { callerActor.checkout() };runCurrent()
    caller.cancel();runCurrent();check(caller.isCancelled && callerOwner.isActive)
    advanceUntilIdle()
    val afterCaller = async { outcome(callerActor) };advanceUntilIdle();check(afterCaller.await() == "ok")
    callerOwner.cancel();runCurrent();passed++

    // A checkout whose submit() returns while its owner shuts down keeps its result. Failure
    // before the receipt arrives can still leave the outcome unknown; that is the service's
    // idempotency/reconciliation problem, not something the actor can rule out.
    val commitOwner = SupervisorJob()
    val commitStarted = CompletableDeferred<Unit>()
    var committed = false
    val commitActor = CartActor(ownerScope(commitOwner), CheckoutService {
        withContext(NonCancellable) {
            commitStarted.complete(Unit);delay(10);committed = true;CheckoutResult("committed")
        }
    })
    val commitCaller = async { outcome(commitActor) };runCurrent();check(commitStarted.isCompleted)
    commitOwner.cancel();advanceUntilIdle()
    check(committed && commitCaller.await() == "committed") { "Committed checkout returned ${commitCaller.await()}" }
    stopped(commitActor);passed++

    // Regression for the teaching claim: two slots may share one boxed value.
    val boxed: List<*> = twice(Meters(1.0))
    check(boxed[0] === boxed[1])
    check(Meters(1.0) == Meters(1.0))
    val firstBox: Any = Meters(1.0)
    val secondBox: Any = Meters(1.0)
    check(firstBox == secondBox && firstBox !== secondBox);passed++
    println("Kotlin regressions: $passed cases passed (including 257 active/queued/suspended requests).")
}

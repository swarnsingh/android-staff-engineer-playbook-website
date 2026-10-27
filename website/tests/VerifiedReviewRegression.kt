import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

lateinit var topLevelMessage: String
class Uri

/* SERVICE_FUNCTION */

@OptIn(ExperimentalCoroutinesApi::class)
fun main() = runBlocking {
    topLevelMessage = "ready"
    lateinit var localMessage: String
    localMessage = "local"
    check(topLevelMessage == "ready" && localMessage == "local")
    println("PASS top-level and local lateinit")

    check(processAudioFile(Uri()).take(2).toList() == listOf(1, 2))
    var rejected = false
    try {
        flow { withContext(Dispatchers.IO) { emit(1) } }.collect()
    } catch (expected: IllegalStateException) { rejected = true }
    check(rejected)
    println("PASS exact corrected service Flow, flowOn and invalid-context rejection")

    runTest {
        val calls = mutableListOf<Long>()
        backgroundScope.launch {
            while (isActive) { calls += currentTime; delay(30_000) }
        }
        runCurrent()
        check(calls.size == 1)
        advanceTimeBy(30_000)
        check(calls.size == 1)
        runCurrent()
        check(calls.size == 2)
        advanceTimeBy(60_000)
        check(calls.size == 3)
        runCurrent()
        check(calls == listOf(0L, 30_000L, 60_000L, 90_000L))
    }
    println("PASS virtual deadline exclusion and runCurrent endpoint assertions")

    runTest {
        val unbuffered = MutableSharedFlow<Int>()
        check(unbuffered.tryEmit(1) && unbuffered.replayCache.isEmpty())
        val seen = mutableListOf<Int>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { unbuffered.collect { seen += it } }
        check(!unbuffered.tryEmit(2))
        unbuffered.emit(3)
        check(seen == listOf(3))
        val replay = MutableSharedFlow<Int>(replay = 1)
        check(replay.tryEmit(4) && replay.replayCache == listOf(4))
    }
    println("PASS default unbuffered SharedFlow and retained replay distinction")
    check(flowOf(1, 2, 3).take(2).toList() == listOf(1, 2))
    println("PASS bounded Flow testing without Turbine")
}

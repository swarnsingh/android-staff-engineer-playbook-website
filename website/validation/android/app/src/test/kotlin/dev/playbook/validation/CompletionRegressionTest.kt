package dev.playbook.validation

import android.app.Application
import androidx.test.core.app.ApplicationProvider
import androidx.room.Room
import androidx.compose.runtime.snapshots.Snapshot
import androidx.lifecycle.*
import dev.playbook.validation.fixtures.repositorytransaction.*
import dev.playbook.validation.fixtures.snapshotcounter.CounterState
import dev.playbook.validation.fixtures.analyticsbatch.*
import dev.playbook.validation.fixtures.poller.*
import dev.playbook.validation.fixtures.overloads.OverloadContract
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import app.cash.turbine.test
import kotlin.time.Duration.Companion.seconds
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35], application=Application::class)
class CompletionRegressionTest {
 @Test fun roomRefreshCommitsRowsAndMetadataTogether() = runTest {
  val db = Room.inMemoryDatabaseBuilder(ApplicationProvider.getApplicationContext(), ProductDatabase::class.java).build()
  try {
   val repo = ProductRepository(db,db.products(),object:ProductApi { override suspend fun getProducts() = ProductsResponse(listOf(ProductDto(1,"one"))) })
   repo.refreshProducts()
   assertEquals(listOf(Product(1,"one")), repo.observeProducts().first())
   assertEquals(1, db.products().metadataCount())
  } finally { db.close() }
 }
 @Test fun roomMetadataFailureRollsBackProductWrite() = runTest {
  val db = Room.inMemoryDatabaseBuilder(ApplicationProvider.getApplicationContext(), ProductDatabase::class.java).build()
  try {
   withContext(Dispatchers.IO) { db.openHelper.writableDatabase.execSQL("CREATE TRIGGER reject_metadata BEFORE INSERT ON SyncMetadata BEGIN SELECT RAISE(ABORT, 'metadata rejected'); END") }
   val repo = ProductRepository(db,db.products(),object:ProductApi { override suspend fun getProducts() = ProductsResponse(listOf(ProductDto(1,"one"))) })
   assertTrue(runCatching { repo.refreshProducts() }.isFailure)
   assertEquals(emptyList<Product>(), repo.observeProducts().first())
   assertEquals(0, db.products().metadataCount())
  } finally { db.close() }
 }
 @Test fun customStateSnapshotDoesNotPublishUntilApplied() {
  val state=CounterState(1)
  val snapshot=Snapshot.takeMutableSnapshot()
  try {
   snapshot.enter { state.value=2; assertEquals(2,state.value) }
   assertEquals(1,state.value)
   snapshot.apply().check()
   assertEquals(2,state.value)
  } finally { snapshot.dispose() }
 }
 @Test fun customStateReadObserverSeesTheActualState() {
  val state=CounterState(5);val reads=mutableListOf<Any>()
  val snapshot=Snapshot.takeSnapshot { reads.add(it) }
  try { snapshot.enter { assertEquals(5,state.value) }; assertTrue(reads.any { it===state }) }
  finally { snapshot.dispose() }
 }
 @Test fun failedUploadIsRequeuedAndOwnershipReleased() = runTest {
  var fail=true;val uploaded=mutableListOf<List<Event>>()
  val tracker=AnalyticsTracker { if(fail) throw IOException("offline") else uploaded.add(it) }
  repeat(49) { tracker.trackEvent(Event(it)) }
  assertTrue(runCatching { tracker.trackEvent(Event(49)) }.exceptionOrNull() is IOException)
  fail=false;tracker.flush()
  assertEquals((0..49).map(::Event),uploaded.single())
 }
 @Test fun cancelledUploadCanBeRetriedByTheOwner() = runTest {
  var cancel=true;val uploaded=mutableListOf<List<Event>>()
  val tracker=AnalyticsTracker { if(cancel) throw CancellationException("owner cancelled") else uploaded.add(it) }
  tracker.trackEvent(Event(1))
  assertTrue(runCatching { tracker.flush() }.exceptionOrNull() is CancellationException)
  cancel=false;tracker.flush();assertEquals(listOf(Event(1)),uploaded.single())
 }
 @Test fun concurrentBatchArrivalsHaveNoLostEvents() = runTest {
  val uploaded=mutableListOf<Event>();val tracker=AnalyticsTracker { delay(1);uploaded.addAll(it) }
  coroutineScope { repeat(257) { launch { tracker.trackEvent(Event(it)) } } }
  tracker.flush();assertEquals((0..256).toSet(),uploaded.map{it.id}.toSet());assertEquals(257,uploaded.size)
 }
 @Test fun pollerDeadlineIsDrivenExplicitly() = runTest {
  var calls=0;val poller=Poller(object:PollApi { override suspend fun fetch() { calls++ } },backgroundScope)
  poller.start();assertEquals(0,calls);runCurrent();assertEquals(1,calls)
  advanceTimeBy(30.seconds);assertEquals(1,calls);runCurrent();assertEquals(2,calls)
  advanceTimeBy(60.seconds);runCurrent();assertEquals(4,calls)
 }
 @Test fun unconfinedEntryDoesNotMeanCompletion() = runTest {
  var done=false
  launch(UnconfinedTestDispatcher(testScheduler)) { delay(100);done=true }
  assertFalse(done);advanceUntilIdle();assertTrue(done)
 }
 @Test fun turbineConsumesFiniteCompletion() = runTest {
  flowOf("item").test { assertEquals("item",awaitItem());awaitComplete() }
 }
 @Test fun gatedStateMakesLoadingObservable() = runTest {
  val state=MutableStateFlow("Idle");val gate=CompletableDeferred<Unit>()
  state.test {
   assertEquals("Idle",awaitItem())
   launch { state.value="Loading";gate.await();state.value="Success" }
   runCurrent();assertEquals("Loading",awaitItem())
   gate.complete(Unit);runCurrent();assertEquals("Success",awaitItem());cancelAndIgnoreRemainingEvents()
  }
 }
 @Test fun lifecycleCollectorStopsAndRestartsAtStarted() = runTest {
  Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
  val owner=object:LifecycleOwner { val registry=LifecycleRegistry.createUnsafe(this);override val lifecycle:Lifecycle get()=registry }
  var starts=0;var stops=0
  try {
   owner.registry.currentState=Lifecycle.State.CREATED
   val job=backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
    owner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) { starts++;try { awaitCancellation() } finally { stops++ } }
   }
   assertEquals(0,starts);owner.registry.currentState=Lifecycle.State.STARTED;runCurrent();assertEquals(1,starts)
   owner.registry.currentState=Lifecycle.State.CREATED;runCurrent();assertEquals(1,stops)
   owner.registry.currentState=Lifecycle.State.STARTED;runCurrent();assertEquals(2,starts)
   owner.registry.currentState=Lifecycle.State.DESTROYED;job.join();assertEquals(2,stops)
  } finally { Dispatchers.resetMain() }
 }
 @Test fun jvmOverloadsRetainsRequiredMiddleParameter() {
  val methods=OverloadContract::class.java.declaredMethods.filter { it.name=="connect" }
  assertEquals(setOf(1,2,3),methods.map{it.parameterCount}.toSet())
  assertEquals("1:required:2",OverloadContract::class.java.getDeclaredMethod("connect",String::class.java).invoke(OverloadContract(),"required"))
 }
}

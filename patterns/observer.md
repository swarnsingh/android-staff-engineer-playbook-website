# Observer Pattern

> The Observer pattern is the absolute bedrock of modern Android architecture. Because the UI thread must never be blocked, Android applications are inherently asynchronous and event-driven. A Staff engineer must understand the evolution of the Observer pattern on Android—from the raw listener interfaces and `BroadcastReceiver`s of 2012, to `LiveData` and RxJava, to the modern standard of Kotlin's `Flow` and `StateFlow`. Crucially, you must know how to manage observer lifecycles to prevent memory leaks and background crashes.

---

## Overview

The Observer pattern defines a one-to-many dependency between objects so that when one object (the Subject/Publisher) changes state, all its dependents (the Observers/Subscribers) are notified and updated automatically.

In Android, this pattern is used to solve the fundamental architectural challenge: **Data lives in the background (network, database, repository), but it must be displayed on the Main (UI) thread.** The background cannot safely hold a reference to the UI (which leads to `Activity` leaks), so the UI must *observe* the background data.

---

## 1. The Evolution of Android Observers

### Era 1: Callbacks & Interfaces (2008 - 2014)
The classic approach was to pass a listener interface.

```kotlin
// The Observer Interface
interface OnDataLoadedListener {
    fun onSuccess(data: List<String>)
    fun onError(exception: Exception)
}

// The Subject
class UserRepository {
    fun fetchUsers(listener: OnDataLoadedListener) {
        // Run background thread...
        // Call listener.onSuccess() on Main thread
    }
}
```
**Fatal Flaw:** Callback hell, no lifecycle awareness, massive memory leaks if the `Activity` was destroyed before the background thread finished.

### Era 2: BroadcastReceivers & EventBuses (2014 - 2016)
Global publish-subscribe systems decoupled the components completely.

```kotlin
// Sending (Publisher)
EventBus.getDefault().post(UserLoggedInEvent(user))

// Receiving (Observer)
@Subscribe(threadMode = ThreadMode.MAIN)
fun onUserEvent(event: UserLoggedInEvent) {
    updateUi(event.user)
}
```
**Fatal Flaw:** Unstructured global state. It became impossible to trace where events originated. "Spaghetti architecture."

### Era 3: RxJava (2015 - 2019)
Functional Reactive Programming introduced streams of data.

```kotlin
userRepository.getUsers()
    .subscribeOn(Schedulers.io())
    .observeOn(AndroidSchedulers.mainThread())
    .subscribe(
        { users -> updateUi(users) }, // onNext
        { error -> showError(error) } // onError
    )
    .addTo(compositeDisposable)
```
**Fatal Flaw:** Massive learning curve, bloated APK size, and easy to cause leaks if `dispose()` wasn't called in `onDestroy()`.

### Era 4: LiveData (2017 - 2021)
Google's first official, lifecycle-aware observer.

```kotlin
// In ViewModel (Subject)
val users = MutableLiveData<List<User>>()

// In Fragment (Observer)
viewModel.users.observe(viewLifecycleOwner) { userList ->
    updateUi(userList)
}
```
**Fatal Flaw:** Tied to the Android SDK (cannot be used in Kotlin Multiplatform's `commonMain`), lacks rich operators (like `combine` or `flatMap`), and always dispatches on the Main thread.

### Era 5: Kotlin Flow & StateFlow (2021 - Present)
The modern standard. Language-level, coroutine-powered, multiplatform streams.

---

## 2. The Modern Standard: `StateFlow` and `SharedFlow`

Staff engineers build architectures using Kotlin's Coroutines and Flow APIs. The Observer pattern in modern Android is split into two distinct use cases: renderable state and transient delivery contracts. StateFlow is a state primitive; SharedFlow broadcasts, while a Channel can hand an element to one consumer. Neither establishes exactly-once handling or process-death durability.

### Observing State (`StateFlow`)
State represents data that *is*. It always has a value, new observers immediately get the latest value, and identical consecutive values are conflated (ignored).

```kotlin
class UserViewModel(repository: UserRepository) : ViewModel() {
    val uiState: StateFlow<UiState> = repository.getUserStream()
        .map<User, UiState> { UiState.Success(it) }
        .catch { emit(UiState.Error("Unable to load user")) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), UiState.Loading)
}
```

### Required UI Progress: State and Acknowledgement

For a single checkout UI, represent the pending receipt destination as state. It remains available across collector gaps until the UI acknowledges that request. This example assumes one checkout at a time and one navigation consumer; it is in-memory state, not process-death persistence or exactly-once navigation.

```kotlin
data class ReceiptNavigation(val requestId: Long, val orderId: String)
data class CheckoutUiState(val navigation: ReceiptNavigation? = null)

class CheckoutNavigationState {
    private val nextRequestId = java.util.concurrent.atomic.AtomicLong(0)
    private val _uiState = MutableStateFlow(CheckoutUiState())
    val uiState: StateFlow<CheckoutUiState> = _uiState.asStateFlow()

    fun onCheckoutSucceeded(orderId: String) {
        val request = ReceiptNavigation(nextRequestId.incrementAndGet(), orderId)
        _uiState.update { it.copy(navigation = request) }
    }

    fun navigationHandled(requestId: Long) {
        _uiState.update { state ->
            if (state.navigation?.requestId == requestId) state.copy(navigation = null)
            else state // An old acknowledgement must not clear a newer request.
        }
    }
}
```

The ViewModel owns this state holder and forwards confirmed checkout results and UI acknowledgements:

```kotlin
class CheckoutViewModel : ViewModel() {
    private val navigation = CheckoutNavigationState()
    val uiState = navigation.uiState
    fun onCheckoutSucceeded(orderId: String) = navigation.onCheckoutSucceeded(orderId)
    fun navigationHandled(requestId: Long) = navigation.navigationHandled(requestId)
}

// Fragment view owner; navigateToReceiptIfNeeded is an app callback that checks
// the current destination/order before synchronously navigating. No suspension
// between that callback and acknowledgement. Render navigation failures explicitly.
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            state.navigation?.let { request ->
                navigateToReceiptIfNeeded(request.orderId)
                viewModel.navigationHandled(request.requestId)
            }
        }
    }
}
```

Do not acknowledge before navigation succeeds. If handling is interrupted before acknowledgement, the state can be seen again; destination-aware navigation makes that replay safe. Recover the verified order/payment state from durable storage/backend after process death rather than treating this in-memory request as the purchase record.

### Loss-Tolerant Alternatives

A Channel exposed with `receiveAsFlow()` hands an element to one collector, but delivery and processing are not guaranteed: cancellation after receiving and before processing can lose the element, including during lifecycle collection. Use it only when that loss is acceptable, such as an optional notice:

```kotlin
private val notices = Channel<String>(
    capacity = Channel.BUFFERED,
    onUndeliveredElement = { diagnostics.recordDroppedNotice() },
)
val noticeEvents: Flow<String> = notices.receiveAsFlow()
```

The app-owned diagnostic callback must be fast, nonblocking and nonthrowing; it can report an undelivered element without logging its content, but does not guarantee handling or recover every processing failure. Bound producers too. SharedFlow broadcasts to active collectors; replay-zero emissions are lost with no subscriber, and extra buffer capacity does not retain them across that gap. Required progress uses acknowledged state rather than either lossy alternative.

---

## 3. Safe UI Observation (The Android Lifecycle Trap)

The most complex part of the Observer pattern on Android is ensuring the observer stops listening when the UI is hidden. A collector outliving the Fragment view can access a destroyed binding, retain UI objects or do unwanted background work. A stopped view is not automatically invalid, so a crash is a risk rather than a guaranteed result.

### In the View System (XML)
You must use `repeatOnLifecycle` or `flowWithLifecycle` to pause collection when the Activity/Fragment goes to the background.

```kotlin
class UserFragment : Fragment() {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // CRITICAL: Launch in the View's lifecycle scope
        viewLifecycleOwner.lifecycleScope.launch {
            // CRITICAL: Suspend collection when the UI is stopped (e.g. backgrounded)
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    renderUi(state)
                }
            }
        }
    }
}
```

### In Jetpack Compose
Compose handles observation elegantly using `collectAsStateWithLifecycle()`. This automatically subscribes and unsubscribes the observer as the Composable enters and leaves the composition, and pauses it when the app goes to the background.

```kotlin
@Composable
fun UserScreen(viewModel: UserViewModel) {
    // Collects the flow, automatically pausing when the app is backgrounded
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    when (val state = uiState) {
        is UiState.Loading -> CircularProgressIndicator()
        is UiState.Success -> Text("Hello, ${state.user.name}")
        is UiState.Error -> Text(state.message)
    }
}
```

---

## 4. Cold vs. Hot Observables

```mermaid
flowchart TD
    Cold["Cold Flow<br/>work starts per collector"] --> C1["Collector A execution"]
    Cold --> C2["Collector B execution"]
    Producer["Long-lived producer"] --> Hot["StateFlow / SharedFlow"]
    Hot --> H1["Collector A shared stream"]
    Hot --> H2["Collector B shared stream"]
```

Cold flows describe repeatable work, while hot flows represent shared state or events with an independent lifetime.

A fundamental concept for Staff engineers:

### Cold Observers (Flow)
A Cold observer only starts producing data when someone subscribes to it. It executes independently for *each* subscriber.

```kotlin
// This block runs from the beginning for EVERY collector
val countdownFlow = flow {
    for (i in 5 downTo 1) {
        emit(i)
        delay(1000)
    }
}
```
**Danger:** If you use a cold flow to execute a network request, and 3 different UI components observe it, the network request will be fired 3 times simultaneously.

### Hot Observers (StateFlow / SharedFlow)
A hot flow exists independently of collectors; whether upstream work runs without them depends on its producer and sharing policy. WhileSubscribed can stop upstream after its configured timeout.

```kotlin
// Converts a Cold flow into a Hot flow
val sharedCountdown = countdownFlow.shareIn(
    scope = viewModelScope,
    started = SharingStarted.WhileSubscribed(5000), // Keep alive for 5s after last observer leaves
    replay = 1 // New observers get the last emitted value
)
```
Using `shareIn` or `stateIn` is critical for preventing redundant work in the data layer.

---

## 5. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The "Background Crash"** | Observing a Flow via `launchWhenStarted` or raw `launch`. Raw lifecycle-scope collection can remain active while stopped; launchWhenStarted suspends its block and can leave upstream work active. Neither behavior guarantees a crash, but both can waste work or misuse view state. | Always use `repeatOnLifecycle` (Views) or `collectAsStateWithLifecycle` (Compose). |
| **Dropped Events** | Emitting an event into a `MutableSharedFlow` while the Fragment is recreating (e.g., config change). No observer is currently listening. | Keep required progress in state until acknowledgement. A Channel can lose a received element on collector cancellation; onUndeliveredElement can report that loss but is not a delivery guarantee. Use Channel/SharedFlow only for explicitly loss-tolerant delivery. replay=1 can repeat stale commands. |
| **Memory Leak** | Storing a reference to a `View` or `Activity` inside an observer that outlives the UI component (e.g., in a Singleton Repository). | Ensure the subscription is tied to a `LifecycleOwner` that automatically disposes when destroyed. |
| **Redundant Network Calls** | Exposing a Cold `Flow` from a Repository directly to the UI. If the screen rotates, the UI re-subscribes, triggering a new API call. | Use `stateIn` in the ViewModel to cache the latest result and survive configuration changes. |

---

## 6. Common Pitfalls

### Pitfall 1: Using LiveData for Single Events
Many legacy codebases use `SingleLiveEvent` to trigger navigation or Snackbars. This is an anti-pattern. LiveData is inherently designed for state, not events. If a user receives an error Snackbar, backgrounds the app, and returns, the `LiveData` re-emits the last value, and the Snackbar shows again.
*Fix:* Model required UI progress as state with a matching acknowledgement. Channels and replay-zero SharedFlow are loss-tolerant alternatives, not guaranteed navigation. Recover required business progress from durable state after process death.

### Pitfall 2: Blocking the Collector
Kotlin Flows are sequential by default. If you perform heavy work inside the `collect` block, you block the upstream flow from emitting new values.

```kotlin
viewModel.locationUpdates.collect { location ->
    // BAD: This blocks the flow. We miss new locations while saving!
    database.saveLocationBlocking(location) 
}
```
*Fix:* Use a suspending Room DAO or move blocking I/O off main. A bounded buffer can decouple stages while retaining order; conflate only when losing intermediate values is allowed. Launching an unbounded child per value is not a general backpressure fix.

---

## Probing Questions

1.  **StateFlow vs LiveData:** Both represent observable state. `StateFlow` requires an initial value, while `LiveData` does not. Why did the Kotlin language designers enforce an initial value for `StateFlow`, and how does this affect your UI layer design?
2.  **Backpressure:** In RxJava, backpressure (what happens when the publisher emits faster than the observer can consume) is explicitly handled via `Flowable`. How does Kotlin Coroutines and `Flow` handle backpressure natively?
3.  **Lifecycle Semantics:** Compare `launchWhenStarted` to `repeatOnLifecycle(STARTED)`. They sound identical, but `launchWhenStarted` is deprecated. What exactly happens to the coroutine in both cases when the user presses the Home button?
4.  **SharedFlow Configuration:** You create a `MutableSharedFlow<Event>(replay = 1, extraBufferCapacity = 10, onBufferOverflow = BufferOverflow.DROP_OLDEST)`. Explain exactly what happens to a new observer that subscribes to this flow 5 seconds after 20 events were emitted.
5.  **Multiplatform Context:** You are moving an Android ViewModel to KMP's `commonMain`. The iOS team wants to observe your `StateFlow` from Swift. What bridging library or pattern (e.g., SKIE) is required to translate Kotlin's `suspend` collection into something Swift's Combine or AsyncSequence can understand?

## Answer Key

1. **StateFlow vs LiveData:** `StateFlow` enforces an initial value because state must always exist. This forces developers to explicitly define the initial UI state (like `Loading`), making the initial modeled state explicit. Nullable state is still possible when T is nullable, and unrelated startup races are not removed.
2. **Backpressure:** `Flow` handles backpressure natively via coroutine suspension. If the collector is slow, the emitter suspends until the collector is ready, bounding demand in an ordinary sequential cold flow. Buffers, hot producers and callback bridges have their own retention/overflow policies and can still exhaust memory.
3. **Lifecycle Semantics:** `launchWhenStarted` simply suspends the coroutine but keeps it alive in memory. `repeatOnLifecycle` cancels the repeating child block below the target lifecycle state and starts it again on re-entry. The outer lifecycle coroutine remains; resource cleanup and upstream sharing still follow their own cancellation/lifetime contracts.
4. **SharedFlow Configuration:** The new observer receives only the very last event (because `replay = 1`), and ignores the previous 19. If no subscribers existed, only the replay cache mattered: extraBufferCapacity did not retain the earlier events. Values do not expire merely because five seconds passed. With active slow collectors, overflow follows the configured DROP_OLDEST policy.
5. **Multiplatform Context:** You use libraries like SKIE or KMP-NativeCoroutines, which automatically generate Swift wrappers to convert Kotlin `StateFlow` and `SharedFlow` into a supported Swift observation surface (for example, SKIE's async sequence support or KMP-NativeCoroutines wrappers). These are different libraries/contracts; they do not universally generate ObservableObject. A hand-written bridge is also possible.

## Further Reading

- [`../android/architecture/state-management.md`](../android/architecture/state-management.md) — Deep dive into modeling UI state with Sealed Classes and StateFlow.
- [`../kotlin/coroutines-and-flow/coroutines.md`](../kotlin/coroutines-and-flow/coroutines.md) — Understanding the underlying Coroutine scopes that power Flows.
- [`../android/compose/recomposition-and-state.md`](../android/compose/recomposition-and-state.md) — How Compose observes State changes to trigger UI updates.
- [`../backend-for-mobile/api-design-for-mobile.md`](../backend-for-mobile/api-design-for-mobile.md) — Emitting network responses into observable streams.
- [SharedFlow broadcast, replay and no-subscriber behavior](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)
- [StateFlow equality conflation and initial value](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)
- [Channel receiveAsFlow fan-out and cancellation limits](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/receive-as-flow.html)
- [Android lifecycle-aware coroutine collection](https://developer.android.com/topic/libraries/architecture/coroutines#restart)
- [Android UI events and state](https://developer.android.com/topic/architecture/ui-layer/events)
- [SKIE Flow bridging contract](https://skie.touchlab.co/features/flows)

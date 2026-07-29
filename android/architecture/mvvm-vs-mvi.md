# MVVM vs. MVI: State Management Architectures

> For years MVVM was Android's unquestioned default. As UIs grew reactive (especially with Compose), MVVM cracked under multi-stream race conditions. MVI emerged to enforce a single source of truth with atomic state transitions. The staff-level decision isn't "MVI everywhere" — it's knowing exactly which screens need it and which don't.

---

## Quick Recap of the Lineage

- **MVC** — Activities were the Controller; quickly became God classes.
- **MVP** — Presenter lived alongside Activity; better separation, but coupled to Android lifecycle and hard to test through configuration changes.
- **MVVM** — ViewModel survives rotation; UI observes streams. Default since ~2017 (Android Architecture Components).
- **MVI** — Single immutable state + explicit user Intents + atomic reducer. Popularized by Redux on the web; mature on Android since ~2019.

Each step traded boilerplate for testability and correctness under concurrency. MVI is the current ceiling for state-heavy reactive screens.

---

## The Problem with MVVM at Scale

In typical MVVM, a ViewModel exposes **multiple independent state streams**:

```kotlin
class CheckoutViewModel : ViewModel() {
    // ❌ Independent streams — easy to fall out of sync
    private val _isLoading = MutableStateFlow(false)
    val isLoading = _isLoading.asStateFlow()

    private val _promoCode = MutableStateFlow("")
    val promoCode = _promoCode.asStateFlow()

    private val _totalPrice = MutableStateFlow(100.0)
    val totalPrice = _totalPrice.asStateFlow()

    private val _errorMessage = MutableSharedFlow<String>()
    val errorMessage = _errorMessage.asSharedFlow()

    fun applyPromoCode(code: String) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val discount = api.validatePromo(code)
                _promoCode.value = code
                _totalPrice.value = 100.0 - discount
            } catch (e: Exception) {
                _errorMessage.emit("Invalid code")
            } finally {
                _isLoading.value = false
            }
        }
    }
}
```

### Three failure modes

1. **Tearing / race conditions.** Between `_promoCode.value = code` and `_totalPrice.value = …`, observers can see the *new* promo with the *old* total. Microseconds, but visible during fast user interaction (e.g., typing into a field while a previous request resolves).
2. **State explosion.** Add free shipping, taxes, gift cards, loyalty points — each becomes another `MutableStateFlow`. The ViewModel grows; the relationships between streams aren't enforced anywhere.
3. **No audit trail.** When the UI renders an impossible combination, you can't replay the sequence that got there. The ViewModel's mutations are scattered across many methods.

For simple screens — settings toggles, profile edit forms — this doesn't matter. For a checkout flow, a real-time feed, or a video player, every microsecond of inconsistency is a customer-visible bug.

---

## The MVI Pattern

Three constraints:

1. **State** — a single immutable `data class` describing the entire screen.
2. **Intent** — a `sealed interface` listing every user action.
3. **Reducer** — pure function: `(State, Intent) -> State`. The only place state changes.

```kotlin
data class CheckoutState(
    val isLoading: Boolean = false,
    val promoCode: String = "",
    val totalPrice: Double = 100.0,
    val error: String? = null,
)

sealed interface CheckoutIntent {
    data class ApplyPromoCode(val code: String) : CheckoutIntent
    data object DismissError : CheckoutIntent
}

class CheckoutViewModel : ViewModel() {
    private val _state = MutableStateFlow(CheckoutState())
    val state: StateFlow<CheckoutState> = _state.asStateFlow()

    fun processIntent(intent: CheckoutIntent) {
        when (intent) {
            is CheckoutIntent.ApplyPromoCode -> applyPromoCode(intent.code)
            CheckoutIntent.DismissError -> _state.update { it.copy(error = null) }
        }
    }

    private fun applyPromoCode(code: String) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            try {
                val discount = api.validatePromo(code)
                _state.update {
                    it.copy(
                        isLoading = false,
                        promoCode = code,
                        totalPrice = 100.0 - discount,
                    )
                }
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                _state.update { it.copy(isLoading = false, error = "Invalid code") }
            }
        }
    }
}
```

### Why each rule pays off

- **Atomic updates** — `_state.update { it.copy(...) }` is a single CAS write. Subscribers see only fully-formed states.
- **Replayable.** Every emission is the full state — perfect for analytics, time-travel debugging, screenshot tests.
- **Testable.** One assertion: `assertEquals(expectedState, viewModel.state.value)`.

---

## UI Events — State First, Best-Effort Effects by Exception

Navigation and messages are often described as "one-off events," but a ViewModel-produced action that matters to correctness should be reduced to UI state. The UI observes that state, performs the UI behavior while active, then reports consumption as another user event. This avoids losing a critical action when the ViewModel outlives its collector and can be made restorable with saved state.

Actions originating entirely in the UI, such as opening help after a tap, should normally stay in the UI. A `Channel` is reasonable only for explicitly best-effort, process-local effects whose loss while no collector exists is acceptable:

```kotlin
sealed interface CheckoutEffect {
    data object NavigateBack : CheckoutEffect
    data class ShowToast(val msg: String) : CheckoutEffect
}

class CheckoutViewModel : ViewModel() {
    private val _state = MutableStateFlow(CheckoutState())
    val state: StateFlow<CheckoutState> = _state.asStateFlow()

    // Best-effort process-local effects; not durable across collector gaps/process death.
    private val _effects = Channel<CheckoutEffect>(Channel.BUFFERED)
    val effects: Flow<CheckoutEffect> = _effects.receiveAsFlow()

    fun checkout() {
        viewModelScope.launch {
            // ... do work ...
            _effects.send(CheckoutEffect.NavigateBack)
        }
    }
}
```

UI side:

```kotlin
@Composable
fun CheckoutScreen(vm: CheckoutViewModel, navController: NavController) {
    val state by vm.state.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) {
        vm.effects.collect { effect ->
            when (effect) {
                CheckoutEffect.NavigateBack -> navController.popBackStack()
                is CheckoutEffect.ShowToast -> snackbar(effect.msg)
            }
        }
    }
    // render state
}
```

`Channel` distributes each element to one receiver, while a `SharedFlow` broadcasts to all active collectors and can replay or buffer according to configuration. Neither provides durable "exactly once" UI processing across lifecycle gaps or process death. If losing the action can leave the product inconsistent, model it as state instead.

---

## Compose Integration

Compose was built for unidirectional data flow. MVI is its natural fit.

```kotlin
@Composable
fun CheckoutScreen(vm: CheckoutViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    CheckoutContent(
        state = state,
        onIntent = vm::processIntent,
    )
}

@Composable
private fun CheckoutContent(
    state: CheckoutState,
    onIntent: (CheckoutIntent) -> Unit,
) {
    when {
        state.isLoading -> Spinner()
        state.error != null -> ErrorBanner(state.error) {
            onIntent(CheckoutIntent.DismissError)
        }
        else -> CheckoutForm(state, onIntent)
    }
}
```

Two perf-critical details:

1. **`collectAsStateWithLifecycle`** (not `collectAsState`) — stops collecting when the lifecycle stops; restarts on resume. Saves CPU and battery for off-screen tabs.
2. **Pass `onIntent` as a stable lambda** — `vm::processIntent` is a method reference; stable, recomposition-friendly. Avoid `{ vm.processIntent(it) }` which allocates a new lambda each composition.

The Composable becomes a pure function: `UiState → UI`. Snapshot testing (Paparazzi) is trivial: pass a `CheckoutState`, capture the bitmap.

---

## Testing MVI

```kotlin
@Test
fun applyPromo_success_updatesTotalAndPromoAtomically() = runTest {
    val vm = CheckoutViewModel(fakeApi)
    vm.state.test {
        assertEquals(CheckoutState(), awaitItem())                          // initial

        vm.processIntent(CheckoutIntent.ApplyPromoCode("SAVE10"))
        assertEquals(CheckoutState(isLoading = true), awaitItem())          // loading

        val final = awaitItem()
        assertEquals("SAVE10", final.promoCode)
        assertEquals(90.0, final.totalPrice)
        assertFalse(final.isLoading)
    }
}
```

Using [Turbine](https://github.com/cashapp/turbine) for flow testing. Each `awaitItem()` asserts an emission. The intermediate `isLoading = true` is verifiable — proof that the UI sees a clean loading-then-loaded transition.

Compare to MVVM testing — you must observe four flows independently and assert the cross-stream invariants yourself. The defect rate of those assertions is the cost of MVVM.

---

## Decision: When to Use What

```
Screen complexity → primary criterion

Settings toggle / profile form / simple list
   ↓ no state dependencies between fields
   → MVVM is fine.

Checkout / video player / real-time feed / map / wizard
   ↓ multiple fields whose values must agree
   ↓ async writes happening concurrently
   ↓ undo/redo or replay required
   → MVI is a strong fit.
```

**Default to MVVM. Promote to MVI when one of:**
- 3+ fields must stay consistent through async updates.
- Race conditions are revenue-visible (checkout, payment, real-time chat).
- Analytics needs a per-action audit trail.
- Snapshot testing is required.
- Team has been bitten by tearing bugs in this screen before.

A mixed codebase is normal — most apps have ~10 MVI screens and the rest MVVM.

---

## MVI Libraries (Pick One or Roll Your Own)

| Library | Boilerplate | Coroutine-first | Notable |
|---|---|---|---|
| [Orbit](https://orbit-mvi.org/) | Low | Yes | Reducer + side effects as suspend; popular |
| [MVIKotlin](https://github.com/arkivanov/MVIKotlin) | Medium | Yes | KMP-first; strong testing story |
| [Mavericks](https://airbnb.io/projects/mavericks/) | Low | No (Async wrapper) | Airbnb's lib; opinionated for large teams |
| Roll your own | None | n/a | Most teams end up here after evaluating libs |

For most Android teams: **roll your own.** MVI is small enough that a library mostly costs you flexibility. A 30-line ViewModel base class plus `StateFlow` + `Channel<Effect>` gets you 80% of any library.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Toast re-fires after rotation | One-off event modeled as state | Move to `Channel<Effect>` |
| Multiple `Spinner`s flicker between requests | Multiple `MutableStateFlow`s updated sequentially | Single `_state.update { it.copy(...) }` |
| Test asserts pass but UI looks wrong | MVVM with cross-stream invariants | Migrate to MVI; assertions become exhaustive |
| `_state.update` lambda blocks recursively | Doing work inside the reducer | Reducer must be pure; do work in `processIntent` before calling `update` |
| State god-object with 30 fields | Single screen doing too much | Split into composed sub-states |
| Excessive Compose recomposition | Unstable params (e.g., `List`) inside state | `@Immutable` annotation; use `ImmutableList` |
| Effect channel grows unbounded | Buffered too generously, consumer slow | Use `Channel.RENDEZVOUS` (default) or rate-limit at source |
| `viewModelScope.launch` races overlap | Two intents racing for the same field | Use `Mutex` inside ViewModel or model as a sequential queue |
| Compose recomposes the entire screen on tiny field change | Whole state passed to every composable | Split: `CheckoutContent(items, total, onIntent)` instead of `(state, onIntent)` |
| `LaunchedEffect(state) { … }` runs constantly | Recomputed on every state change | Key on the specific field, not whole state |
| Hard to introduce middleware (logging, analytics) | Reducer inlined into ViewModel | Extract reducer to interface; wrap with middleware |
| Snapshot tests flaky | State carries time/randomness | Inject clock + seed; state must be deterministic |

---

## Common Pitfalls

- **Wrapping every line in an Intent.** Intents represent user-facing actions. If you have `IntentSetField1`, `IntentSetField2`, …, you've reinvented method calls. Group related fields into a single intent or accept that some sub-state changes are direct mutations of derived data.
- **Multiple StateFlows in an "MVI" ViewModel.** Defeats the entire purpose. If there are multiple `StateFlow`s, it's MVVM with a different name.
- **Treating `processIntent` as the public API.** It's a code-organization technique. Most teams expose typed methods (`viewModel.applyPromo(code)`) instead — same atomicity, less ceremony.
- **Reducer doing async work.** A reducer is `(State, Intent) → State`, pure. Async work happens in `processIntent` *before or after* calling `_state.update`. Mixing the two creates re-entrancy bugs.
- **Ignoring backpressure on effects.** A spammy intent (typing in a text field, scrolling) producing one effect per event will buffer effects. Use a `RENDEZVOUS` channel + downstream `debounce`/`sample`.
- **No middleware for cross-cutting concerns.** Analytics, logging, undo — these belong in a thin wrapper around `processIntent`, not duplicated in every ViewModel.
- **"MVI everywhere" mandate.** Settings screens turn into 200-line files. Pick MVI for screens that need it.

---

## Probing Questions

1. Explain the unidirectional data flow rule and how MVI enforces it at the language level (immutable state, sealed intents, pure reducer).
2. Walk through a concrete MVVM race condition that MVI prevents. Why does `_state.update { it.copy(...) }` succeed where two `MutableStateFlow.value =` writes fail?
3. How do you handle one-off events (navigation, toast, vibrate) in MVI without re-firing on configuration change?
4. When is `Channel<Effect>` acceptable, how does it differ from `SharedFlow`, and which delivery guarantees does it *not* provide?
5. When is MVVM the *correct* choice? Give two concrete screen examples where MVI would be overkill.
6. In Compose, what's the difference between `collectAsState` and `collectAsStateWithLifecycle`? Why does it matter for battery?
7. How do you test atomicity in MVI with Turbine? Walk through assert + `awaitItem()` for a loading → loaded transition.
8. Your MVI ViewModel has 35 fields in the state class. What's wrong, and how would you refactor?
9. Two intents race on the same field — `processIntent(Increment)` fires twice concurrently. How do you serialize them inside the ViewModel?
10. Why is "every intent should be a sealed case" sometimes wrong? When does it devolve into method-call-with-extra-steps?
11. Compose recomposes the whole screen on every state change. Diagnose: what's likely unstable in the state class, and how do you fix it?
12. Walk through how you'd integrate analytics middleware that logs every intent without duplicating code in every ViewModel.

## Answer Key

1. UDF sends state down to the UI and user actions up to the state holder. Immutable state prevents in-place mutation, sealed intents make the accepted action set explicit, and a pure reducer centralizes deterministic transitions.
2. Two independent flows can expose a new promo code with an old total between sequential writes. One `_state.update { it.copy(...) }` atomically updates a single state value, so collectors observe either the old complete state or the new complete state.
3. Keep UI-originated behavior such as direct navigation in the UI; for a ViewModel-originated critical action, represent the condition or message in UI state and let the UI acknowledge consumption. This avoids both replaying an uncleared action and losing an uncollected one.
4. A `Channel` sends each element to one receiver and can suit a best-effort process-local effect; a `SharedFlow` broadcasts to active collectors and may replay or buffer. Neither guarantees durable exactly-once processing across an absent collector, lifecycle gap, or process death.
5. MVVM fits screens with few cross-field invariants and little competing async work—for example, settings toggles and a simple profile form. Intent/reducer ceremony buys little consistency on those screens.
6. `collectAsState()` collects while the composable is present; `collectAsStateWithLifecycle()` starts and stops with the configured lifecycle state. Lifecycle-aware collection avoids upstream work and recompositions for stopped UI, reducing CPU and battery use.
7. Assert the initial Turbine item, trigger the intent, then `awaitItem()` for loading and again for loaded. Assert all dependent fields on the final single emission to prove that no torn intermediate result escaped.
8. Thirty-five flat fields signal excessive screen responsibility and broad invalidation. Split the feature or compose cohesive immutable sub-states, then pass each composable only the smallest state slice it needs.
9. Route competing intents through one sequential consumer, or protect the whole read/side-effect/write operation with a `Mutex`. Atomic `StateFlow.update` prevents a lost state write but does not serialize surrounding asynchronous work.
10. Intents should represent meaningful user or external actions, not mechanically wrap every setter. If each field gets a `SetX` case with no policy value, typed methods or a grouped domain action provide the behavior with less indirection.
11. The state or one of its members is likely unstable, recreated unnecessarily, or passed wholesale to every child. Use immutable/stable types and collections, avoid rebuilding equal values, and pass narrow slices so Compose can skip unaffected call sites.
12. Put intent handling behind a dispatcher/reducer interface and wrap it with middleware that records the intent before delegation. Inject the wrapper once and enforce a centralized policy that redacts sensitive payloads.

---

## Further Reading

- [`viewmodel.md`](viewmodel.md) — ViewModel lifecycle, the host for both patterns.
- [`structured-concurrency.md`](structured-concurrency.md) — `viewModelScope` for intent processing.
- [`flow.md`](flow.md) — StateFlow vs SharedFlow vs Channel comparison.
- [`modularization-strategies.md`](modularization-strategies.md) — how MVI states travel across module boundaries.
- [`state-management.md`](state-management.md) — state holder patterns deeper.
- [`../compose/recomposition-and-state.md`](../compose/recomposition-and-state.md) — Compose recomposition rules MVI rides on.
- [`../data-and-di/room-vs-datastore.md`](../data-and-di/room-vs-datastore.md) — persisting MVI state across process death.
- [`../../kotlin/language-core/sealed-classes.md`](../../kotlin/language-core/sealed-classes.md) — modeling Intent / Effect / UiState.
- [`../../kotlin/language-core/data-classes.md`](../../kotlin/language-core/data-classes.md) — immutable state with `copy()`.
- [Hannes Dorfmann — "Reactive Apps with Model-View-Intent"](http://hannesdorfmann.com/android/mosby3-mvi-1/) — the seminal series.
- [Manuel Vivo (Android) — UI layer guidance](https://developer.android.com/topic/architecture/ui-layer) — official Google take.
- [Android Developers — UI events](https://developer.android.com/topic/architecture/ui-layer/events) — state-first handling and delivery guarantees.
- [Android Developers — Architecture recommendations](https://developer.android.com/topic/architecture/recommendations) — current ViewModel and UDF guidance.
- [Orbit MVI documentation](https://orbit-mvi.org/) — battle-tested library reference.
- [Cash App — Turbine](https://github.com/cashapp/turbine) — flow testing tool MVI tests live on.

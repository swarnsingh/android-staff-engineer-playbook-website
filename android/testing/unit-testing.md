# Unit Testing — JUnit, MockK, Turbine, Coroutines Test

> The fastest tests are the ones that run on the JVM, not on an Android device. A staff engineer's job is to keep the test pyramid wide at the bottom: thousands of unit tests on the JVM, hundreds of integration tests on Robolectric, dozens of UI tests on a real device. Staff-level mastery means knowing JUnit 5 idioms, when to mock vs use a real fake, how to test coroutines and Flow deterministically, and how to architect for testability *before* the tests get hard to write.

---

## The Test Pyramid (Android Edition)

```
                ▲
               / \      End-to-end / Journey (dozens)
              /   \     - Real device or Firebase Test Lab
             /─────\
            /       \   Integration / UI (hundreds)
           /         \  - Robolectric, Compose UI tests, screenshot tests
          /───────────\
         /             \ Unit (thousands)
        /               \ - Pure JVM, milliseconds
       ─────────────────
```

The trade-off: speed vs realism.

| Level | Speed | Realism | Tool |
|---|---|---|---|
| Unit | ~5ms / test | Low (mocked deps) | JUnit 5 + MockK |
| Robolectric | ~100ms / test | Medium (faked Android framework) | Robolectric + JUnit |
| Compose UI | ~1s / test | Medium-high | ComposeTestRule |
| Instrumentation | ~3s / test | High (real device) | Espresso |
| Journey (E2E) | ~30s / test | Highest | Firebase Test Lab, real device |

A 30-second flake on a journey test is acceptable for catching real bugs. A 30-second flake on a unit test is unacceptable.

This file covers **unit testing**. Companion file: [`ui-testing.md`](ui-testing.md).

### Staff-level test portfolio

A large Android org needs a portfolio, not a pile of tests. Each layer should have an owner, a budget, and a reason to exist.

| Layer | Primary purpose | Owner | Merge gate |
|---|---|---|---|
| Pure unit tests | Business rules, reducers, mappers, validation | Feature team | Every PR |
| Contract tests | Client/server schema and error-shape compatibility | Mobile + backend owners | Every API change |
| Integration tests | Repository, Room, fake network, sync engine | Feature/platform team | Every PR for touched module |
| Screenshot tests | Component visual states, themes, localization | Design system + feature team | Every PR touching UI |
| Macrobenchmarks | Startup, scroll, critical performance paths | Platform/performance owner | Nightly + release gate |
| Journey tests | Login, checkout, sync, payment, onboarding | Release owner + feature team | Release candidate |

The Staff review question is: "Which production failure does this test prevent, and is this the cheapest layer that can catch it?" If a journey test can be replaced by five deterministic unit and contract tests, replace it. If only a real device can expose the risk, keep the journey test and invest in flake control.

### Contract tests beat mocked optimism

Mocks prove your assumptions. Contract tests prove your assumptions still match the backend.

For mobile APIs, contract fixtures should include:
- current response shape;
- N-2 or N-3 old-client response shape;
- unknown enum values;
- missing optional fields;
- typed business errors;
- malformed but historically observed payloads.

Run these fixtures against generated clients and parsers in CI. A backend PR that removes a field still used by an old Android app should fail before it reaches production.

---

## What "Unit" Means

A unit test:
- Runs on the JVM (not a device or emulator).
- Tests one class (or a small group of related classes).
- Has no real I/O, no real network, no real database — only fakes.
- Runs in milliseconds.

If a test takes >50ms, it's not really a unit test. Common causes:
- Real Room DB (use `inMemoryDatabaseBuilder` for "fast integration" — still seconds for setup).
- Real network (use OkHttp `MockWebServer`).
- Real coroutine `delay` (use `runTest` with virtual time).

The 80/20: 80% of bugs are caught by 20% of the tests, and that 20% is the fast, focused unit test.

---

## JUnit 5 Setup

```kotlin
// libs.versions.toml
[versions]
junit-jupiter = "5.10.2"
turbine = "1.0.0"
mockk = "1.13.10"

[libraries]
junit-jupiter = { module = "org.junit.jupiter:junit-jupiter", version.ref = "junit-jupiter" }
junit-jupiter-engine = { module = "org.junit.jupiter:junit-jupiter-engine", version.ref = "junit-jupiter" }
turbine = { module = "app.cash.turbine:turbine", version.ref = "turbine" }
mockk = { module = "io.mockk:mockk", version.ref = "mockk" }
```

```kotlin
// :feature:cart:impl/build.gradle.kts
dependencies {
    testImplementation(libs.junit.jupiter)
    testRuntimeOnly(libs.junit.jupiter.engine)
    testImplementation(libs.turbine)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
}

tasks.withType<Test>().configureEach {
    useJUnitPlatform()
}
```

Why JUnit 5 over JUnit 4:
- `@DisplayName` for human-readable test names.
- `@Nested` for grouping related tests.
- `@TestFactory` for parameterized tests without `@Parameterized`.
- Lifecycle extensions (richer than `@Rule`).
- Lambda-based assertions.

If your project still uses JUnit 4, migration is straightforward but optional. Most new projects start on 5.

---

## A Good Unit Test

```kotlin
class CartViewModelTest {

    private val repository: CartRepository = mockk()
    private val dispatcher = StandardTestDispatcher()
    private lateinit var viewModel: CartViewModel

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(dispatcher)
        viewModel = CartViewModel(repository, dispatcher)
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `addItem updates the cart count`() = runTest(dispatcher) {
        coEvery { repository.add(any()) } returns Unit
        coEvery { repository.observeCart() } returns flowOf(listOf(item1))

        viewModel.addItem(item1)
        advanceUntilIdle()

        viewModel.state.test {
            val state = awaitItem()
            assertEquals(1, state.items.size)
        }
    }
}
```

Six things going right:

1. **Mocked dependencies** — `repository` is a MockK mock.
2. **Test dispatcher** — `StandardTestDispatcher` with virtual time.
3. **Main dispatcher swap** — `Dispatchers.setMain(dispatcher)` for `viewModelScope`.
4. **Clean teardown** — `Dispatchers.resetMain()` for test isolation.
5. **Turbine `.test { }`** — deterministic Flow collection.
6. **`advanceUntilIdle()`** — runs all pending coroutines.

---

## Coroutines Testing

### `runTest` and Virtual Time

```kotlin
@Test
fun `polling happens every 30 seconds`() = runTest {
    val poller = Poller(api, scope = backgroundScope)
    poller.start()
    
    coVerify(exactly = 1) { api.fetch() }
    
    advanceTimeBy(30.seconds)
    coVerify(exactly = 2) { api.fetch() }
    
    advanceTimeBy(60.seconds)
    coVerify(exactly = 4) { api.fetch() }
}
```

`runTest` provides:
- A `TestScope` with virtual time.
- `advanceTimeBy(duration)` to skip ahead instantly.
- `advanceUntilIdle()` to run all pending coroutines.
- `backgroundScope` for "fire and forget" work that doesn't block test completion.

A `delay(30_000)` in production code becomes instant in tests. A 60-minute test scenario runs in milliseconds.

### `StandardTestDispatcher` vs `UnconfinedTestDispatcher`

| Dispatcher | Behavior | Use case |
|---|---|---|
| `StandardTestDispatcher` | Coroutines are queued; require `advanceUntilIdle()` or `advanceTimeBy()` to run | Tests that need to verify exact ordering of dispatches |
| `UnconfinedTestDispatcher` | Coroutines run eagerly on the test thread | Most tests where you just want to check the final state |

A common pattern: use `UnconfinedTestDispatcher` everywhere unless you're testing dispatch timing.

```kotlin
val dispatcher = UnconfinedTestDispatcher()
// Now `viewModel.addItem(...)` synchronously updates state — no `advanceUntilIdle()` needed.
```

### Injecting `Dispatcher` for Testability

```kotlin
class CartViewModel @Inject constructor(
    private val repo: CartRepository,
    private val ioDispatcher: CoroutineDispatcher,    // injected
) : ViewModel() {

    fun load() = viewModelScope.launch(ioDispatcher) {
        repo.load()
    }
}
```

In production, Hilt provides `Dispatchers.IO`. In tests, replace with `UnconfinedTestDispatcher`. No `Dispatchers.IO` mocking gymnastics.

---

## Flow Testing with Turbine

[Turbine](https://github.com/cashapp/turbine) makes Flow testing deterministic:

```kotlin
@Test
fun `state emits Loading then Success`() = runTest {
    coEvery { repo.fetch() } returns flowOf(items)
    val viewModel = ItemsViewModel(repo)

    viewModel.state.test {
        assertEquals(ItemsState.Loading, awaitItem())
        assertEquals(ItemsState.Success(items), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

Key APIs:

| API | What it does |
|---|---|
| `flow.test { ... }` | Subscribes; runs the block; cancels on block exit |
| `awaitItem()` | Suspends until next emission; returns it |
| `awaitComplete()` | Asserts the Flow finished normally |
| `awaitError()` | Asserts the Flow finished exceptionally |
| `expectNoEvents()` | Asserts no further emissions |
| `cancelAndConsumeRemainingEvents()` | Drain remaining; useful at end |
| `cancelAndIgnoreRemainingEvents()` | Stop without asserting |

Without Turbine, Flow testing involves manual `Job` management and is brittle. Turbine has become the standard.

### Pitfall: never `collect { }` without Turbine in tests

```kotlin
// BAD — collect never returns; test hangs
@Test fun hang() = runTest {
    flow.collect { /* never returns */ }
}

// GOOD — Turbine handles cancellation
@Test fun ok() = runTest {
    flow.test {
        assertEquals(item, awaitItem())
    }
}
```

---

## Mocks, Fakes, and Spies

Three different things often conflated:

| Tool | What it is | Use when |
|---|---|---|
| **Mock** | A library-generated double; you specify behavior per call | The dep has many methods; you only care about a few |
| **Fake** | A hand-written real implementation backed by in-memory state | The dep has stateful behavior; you want realistic interactions |
| **Spy** | A mock that wraps a real object; you can verify calls AND let real impl run | Rare; usually a smell |

### MockK (preferred for Kotlin)

```kotlin
class CartRepositoryTest {

    private val api: CartApi = mockk()
    private val dao: CartDao = mockk(relaxUnitFun = true)   // unit-returning calls no-op

    @Test
    fun `add stores via dao and posts to api`() = runTest {
        coEvery { api.add(any()) } returns true
        every { dao.observeAll() } returns flowOf(emptyList())

        val repo = CartRepositoryImpl(api, dao)
        repo.add(item)

        coVerify(exactly = 1) { api.add(item) }
        coVerify(exactly = 1) { dao.insert(item.toEntity()) }
    }
}
```

`coEvery`/`coVerify` work with suspending functions. `relaxUnitFun = true` makes void-returning calls no-op by default.

### Mockito-Kotlin (alternative)

```kotlin
import org.mockito.kotlin.*

private val api: CartApi = mock()

whenever(api.fetch()).thenReturn(items)
verify(api).fetch()
```

Both work; MockK has better Kotlin support (sealed classes, top-level functions, coroutines). Older projects on Mockito don't need to migrate.

### Fakes

Often clearer than mocks:

```kotlin
class FakeCartRepository(
    initialItems: List<CartItem> = emptyList(),
) : CartRepository {
    private val itemsFlow = MutableStateFlow(initialItems)

    override fun observeCart(): Flow<List<CartItem>> = itemsFlow

    override suspend fun add(item: CartItem) {
        itemsFlow.update { it + item }
    }

    override suspend fun remove(itemId: String) {
        itemsFlow.update { items -> items.filter { it.id != itemId } }
    }
}
```

This fake **is** a working CartRepository — same `Flow` semantics, same `add`/`remove`. Tests against it are more realistic than tests against mocks.

When to mock vs fake:

- Mock when the dep has > 5 methods and you only test 1–2.
- Fake when the dep has 2–4 methods and stateful behavior matters.
- Live in `:test:fixtures` so all features share fakes (see [`multi-module.md`](../os-internals/multi-module.md)).

---

## Assertions — AssertJ / Kotlin-Test / Truth

Plain JUnit assertions are clunky. Three popular libraries:

```kotlin
// kotlin.test (built-in)
import kotlin.test.*
assertEquals(expected, actual)
assertTrue(value > 0)

// Truth (Google)
import com.google.common.truth.Truth.assertThat
assertThat(list).containsExactly("a", "b").inOrder()
assertThat(map).hasSize(3)
assertThat(throwable).hasMessageThat().contains("error")

// AssertK
import assertk.assertThat
import assertk.assertions.*
assertThat(list).containsExactly("a", "b")
assertThat(state).isInstanceOf(CartState.Success::class)
```

Truth and AssertK both produce excellent error messages. Truth is Google's; AssertK is Kotlin-native. Either is a strict improvement over plain JUnit.

For Compose UI testing, `androidx.test.espresso` has its own assertions; see [`ui-testing.md`](ui-testing.md).

---

## Testing ViewModels

The most common unit test target:

```kotlin
class CheckoutViewModelTest {

    private val repository = FakeCheckoutRepository()
    private val analytics = FakeAnalytics()
    private val dispatcher = UnconfinedTestDispatcher()
    private lateinit var viewModel: CheckoutViewModel

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(dispatcher)
        viewModel = CheckoutViewModel(repository, analytics)
    }

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `initial state is Idle`() = runTest {
        assertEquals(CheckoutState.Idle, viewModel.state.value)
    }

    @Test
    fun `submit transitions to Loading then Success`() = runTest {
        repository.submitResult = CheckoutResult.Success("order123")

        viewModel.state.test {
            assertEquals(CheckoutState.Idle, awaitItem())
            viewModel.submit(items, paymentMethod)
            assertEquals(CheckoutState.Loading, awaitItem())
            val final = awaitItem()
            assertTrue(final is CheckoutState.Success)
            assertEquals("order123", (final as CheckoutState.Success).orderId)
        }
    }

    @Test
    fun `submit failure transitions to Error with retryable flag`() = runTest {
        repository.submitResult = CheckoutResult.Error("Network down", retryable = true)

        viewModel.submit(items, paymentMethod)
        advanceUntilIdle()

        val state = viewModel.state.value
        assertTrue(state is CheckoutState.Error)
        assertTrue((state as CheckoutState.Error).retryable)
    }

    @Test
    fun `submit fires analytics event`() = runTest {
        viewModel.submit(items, paymentMethod)
        advanceUntilIdle()

        assertEquals(1, analytics.events.size)
        assertEquals("checkout_submit", analytics.events[0].name)
    }
}
```

Pattern:
1. Fake all dependencies.
2. Construct ViewModel with TestDispatcher.
3. Trigger action; await state changes via Turbine.
4. Assert state, side effects (analytics), and behavior (repository called correctly).

---

## Testing Repositories

```kotlin
class CartRepositoryTest {

    private val api: CartApi = mockk()
    private val dao = FakeCartDao()
    private lateinit var repo: CartRepositoryImpl

    @BeforeEach
    fun setUp() {
        repo = CartRepositoryImpl(api, dao)
    }

    @Test
    fun `observe emits cart from dao changes`() = runTest {
        repo.observeCart().test {
            assertEquals(emptyList(), awaitItem())
            dao.insert(itemEntity1)
            assertEquals(listOf(item1), awaitItem())
        }
    }

    @Test
    fun `add posts to api and inserts to dao`() = runTest {
        coEvery { api.add(any()) } returns true

        repo.add(item1)

        coVerify(exactly = 1) { api.add(item1.toDto()) }
        assertEquals(1, dao.items.size)
    }

    @Test
    fun `add does not insert to dao when api fails`() = runTest {
        coEvery { api.add(any()) } returns false

        repo.add(item1)

        assertEquals(0, dao.items.size)
    }
}
```

Critical: test the behaviors that constitute the contract. Don't test private helpers.

---

## Parameterized Tests

```kotlin
@TestFactory
fun `cart total calculation`() = listOf(
    listOf(item(100), item(200)) to 300,
    listOf(item(100), item(200), item(50)) to 350,
    emptyList<CartItem>() to 0,
).map { (items, expected) ->
    DynamicTest.dynamicTest("$items sums to $expected") {
        val cart = Cart(items)
        assertEquals(expected, cart.total)
    }
}
```

JUnit 5's `@TestFactory` generates a test per data row. Useful when verifying many input/output pairs cleanly.

---

## Time and Randomness

Inject these dependencies so tests are deterministic:

```kotlin
class TimerViewModel @Inject constructor(
    private val clock: Clock,
    private val random: Random,
) : ViewModel() { /* ... */ }
```

Test setup:

```kotlin
private val clock = Clock.fixed(Instant.parse("2024-01-15T10:00:00Z"), ZoneOffset.UTC)
private val random = Random(seed = 42)
```

Tests now produce identical output regardless of when or where they run.

---

## Coverage — Set a Floor, Not a Ceiling

JaCoCo or Kover for coverage:

```kotlin
plugins {
    id("org.jetbrains.kotlinx.kover")
}

koverReport {
    verify {
        rule {
            bound { minValue = 70; metric = MetricType.LINE; aggregation = AggregationType.COVERED_PERCENTAGE }
        }
    }
}
```

The 70% line-coverage floor catches catastrophic regressions. Don't chase 100% — covering trivial getters wastes time and produces brittle tests.

**Per-class threshold is more meaningful than overall percentage.** Critical paths should be > 90%; trivial UI scaffolding can be lower.

---

## Test Naming and Structure

Adopt a convention. Two popular ones:

### "Should ... when ..."

```kotlin
@Test fun `should emit Loading then Success when submit succeeds`() { /* ... */ }
@Test fun `should emit Error when submit fails`() { /* ... */ }
```

Readable. The backtick syntax is JVM-only.

### "Given ... When ... Then ..."

```kotlin
@Test fun `given empty cart when add called then cart has one item`() { /* ... */ }
```

More verbose; clearer intent for complex tests.

### Structure inside each test

Three-phase pattern:

```kotlin
@Test fun `submit triggers analytics`() = runTest {
    // ARRANGE
    repo.submitResult = CheckoutResult.Success("o1")
    
    // ACT
    viewModel.submit(items, paymentMethod)
    advanceUntilIdle()
    
    // ASSERT
    assertEquals(1, analytics.events.size)
}
```

Comments optional; the blank lines separate the phases.

---

## Common Anti-Patterns

### Anti-pattern: testing internals

```kotlin
// BAD
@Test fun `private helper returns correct value`() {
    val vm = CartViewModel(...)
    val result = vm.calculateTotalInternal(items)   // accessing private method!
    assertEquals(300, result)
}
```

Test the public behavior. If `calculateTotal` matters, test it via the public `submit()` flow.

### Anti-pattern: brittle mock expectations

```kotlin
// BAD — fails if you re-order verifications
coVerify(ordering = Ordering.SEQUENCE) {
    repo.fetch()
    repo.cache(any())
    analytics.track("fetch")
    analytics.track("cache")
}
```

Verify only the orderings that matter for correctness. Over-specifying makes tests brittle.

### Anti-pattern: real time / random in tests

```kotlin
// BAD
val now = System.currentTimeMillis()
```

Inject `Clock` and use `Clock.fixed`.

### Anti-pattern: each test creates ViewModel from scratch

```kotlin
@Test fun a() { val vm = CheckoutViewModel(...); ... }
@Test fun b() { val vm = CheckoutViewModel(...); ... }
@Test fun c() { val vm = CheckoutViewModel(...); ... }
```

Hoist to `@BeforeEach`:

```kotlin
@BeforeEach fun setUp() { viewModel = CheckoutViewModel(...) }
@Test fun a() { viewModel.submit(...); ... }
```

DRY; updates propagate.

### Anti-pattern: long test names

```kotlin
@Test fun `should emit Loading state then transition to Success when user submits valid checkout form with valid credit card`() { ... }
```

Split into multiple tests, each verifying one thing.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Test hangs forever | `flow.collect { }` without Turbine | Always wrap in `flow.test { }` |
| Test fails with `IllegalStateException: Module with the Main dispatcher had failed to initialize` | `Dispatchers.setMain()` not called | Set up before constructing ViewModel |
| Tests flaky on CI but pass locally | Race condition; missing `advanceUntilIdle()` | Add explicit virtual-time advances |
| MockK records but doesn't match | `mockk()` vs `mockk<Type>()` for generic types | Use the typed form |
| `coEvery` returns Unit but should suspend | `mockk(relaxUnitFun = true)` not used | Use `relaxUnitFun = true` or specify `coEvery { } just runs` |
| `runTest` swallows exception | Caught in `Job` tree | Use `runTest(StandardTestDispatcher()) { ... }` and assert |
| Tests pass but coverage dropped | New code untested | Set coverage floor in `kover` |
| Multiple tests share state | Forgot `@BeforeEach` to reset | Re-initialize per test |
| `@Nested` test classes don't see outer setup | JUnit 5 default lifecycle is `PER_METHOD` | Annotate `@TestInstance(Lifecycle.PER_CLASS)` |
| Slow test suite | Real DB / network / sleeps | Audit; switch to fakes + virtual time |
| Compose state not updated in test | Tests don't use `ComposeTestRule` | See [`ui-testing.md`](ui-testing.md) |
| `LiveData` value is null in tests | No `InstantTaskExecutorRule` | Use `JUnit 5 LiveData test extension`; or migrate to `StateFlow` |
| Mock returns null for non-nullable | MockK strict mode | `every { ... } returns ...` for the call |
| `kotlin.test.assertEquals` produces unhelpful diff | Plain message | Use Truth or AssertK |
| Test order matters | Static / global state | Eliminate; use proper test isolation |
| `MainCoroutineRule` works but causes warnings | Old-school JUnit 4 rule with JUnit 5 | Use `Dispatchers.setMain` directly |
| Build fails: "No tests found" | JUnit 5 platform not configured | `tasks.withType<Test> { useJUnitPlatform() }` |

---

## Common Pitfalls

- **Over-mocking.** Every dep mocked means every test is brittle. Prefer fakes for stateful deps.
- **Asserting on internal state.** Test behaviors, not field values.
- **Test setup in `@BeforeAll` (PER_METHOD lifecycle).** Shared state between tests. Use `@BeforeEach` unless you really want shared.
- **Skipping coroutine setup.** Tests pass locally because dispatcher coincides with test thread; fail on CI. Always set up `Dispatchers.setMain`.
- **Forgetting `Dispatchers.resetMain()`.** Test leakage across the file.
- **Naming tests after methods.** `submitTest1`, `submitTest2` is worse than meaningless. Describe the behavior.
- **No coverage floor.** Coverage drops slowly over time without a guardrail.
- **Real time in tests.** A `delay(5_000)` test takes 5 real seconds. Use virtual time.
- **Coupling tests to private implementation.** Refactoring breaks tests even when behavior is unchanged.
- **Testing the framework.** Don't test that `Room.upsert` works — test that *your repository* uses it correctly.

---

## Probing Questions

1. Test pyramid for Android — explain each level and the speed/realism tradeoff.
2. `StandardTestDispatcher` vs `UnconfinedTestDispatcher` — when to use each?
3. Walk through testing a coroutine that uses `delay(60_000)`. How do you make it run instantly?
4. Mocks vs fakes — give a concrete example of each being the better choice.
5. Why does `flow.collect { }` in a test hang? What's the Turbine alternative?
6. Inject `Dispatcher` into a class. Walk through how this makes the class testable.
7. JUnit 5 `@TestFactory` — what problem does it solve?
8. Test a ViewModel that fires analytics on submit. What's mocked, what's faked?
9. A class has 80% line coverage. How do you decide if that's good or bad?
10. Property-based tests in Kotlin — when is the investment worth it?
11. `@BeforeEach` vs `@BeforeAll` — when does each apply?
12. A new engineer mocks every dependency. What's the code-review pushback?

---

## Further Reading

- [`ui-testing.md`](ui-testing.md) — Compose UI tests, Robolectric, Paparazzi.
- [`../architecture/viewmodel.md`](../architecture/viewmodel.md) — ViewModels as test targets.
- [`../architecture/mvvm-vs-mvi.md`](../architecture/mvvm-vs-mvi.md) — testable UI state.
- [`../data-and-di/hilt-vs-koin-vs-manual-di.md`](../data-and-di/hilt-vs-koin-vs-manual-di.md) — `@TestInstallIn` for module-level test fakes.
- [`../os-internals/multi-module.md`](../os-internals/multi-module.md) — `:test:fixtures` shared fakes.
- [`../../kotlin/coroutines.md`](../../kotlin/coroutines.md) — `runTest`, virtual time.
- [`../../kotlin/sealed-classes.md`](../../kotlin/sealed-classes.md) — sealed types make testing simpler.
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/) — official.
- [MockK](https://mockk.io/) — Kotlin mocking library.
- [Turbine](https://github.com/cashapp/turbine) — Flow testing.
- [Kotlinx Coroutines Test](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/) — official coroutine test library.
- [Google Truth](https://truth.dev/) — assertions.
- [AssertK](https://github.com/willowtreeapps/assertk) — Kotlin-native assertions.

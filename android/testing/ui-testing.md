# UI Testing — Compose, Espresso, Robolectric, Paparazzi

> UI tests sit in an uncomfortable middle: too slow to run on every save, too fast to skip. Done well, they catch regressions a unit test can't — interaction bugs, layout breaks, accessibility violations, theme drift. Staff-level mastery means knowing when to reach for Compose UI tests vs Robolectric vs Paparazzi snapshots, structuring tests to avoid the flakiness curse, and using Semantics + test tags effectively across the entire app's component library.

---

## The UI-Test Landscape

| Tool | Runs on | Speed | What it tests |
|---|---|---|---|
| **Compose UI Tests** | Device or emulator | ~1s/test | Real Compose with framework |
| **Robolectric** | JVM (faked Android) | ~100ms/test | Compose/Views without an emulator |
| **Paparazzi** | JVM (Layoutlib) | ~50ms/test | Screenshot diff testing |
| **Espresso (Views)** | Device or emulator | ~2s/test | Legacy XML-based UI |
| **UI Automator** | Device | ~3s/test | Cross-app, system UI |

You'll usually use **two or three of these**, not all five. A modern Compose-only codebase typically uses:
- **Paparazzi** for component-level visual regression.
- **Compose UI tests** (on Robolectric) for behavior tests.
- **Compose UI tests on device** for the most critical journeys.

This file is the **practical guide**. Companion file: [`unit-testing.md`](unit-testing.md).

---

## UI Test Governance At Scale

UI tests fail in two ways: they catch real regressions, or they teach engineers to ignore CI. Staff engineers protect the first outcome by aggressively managing the second.

### Flake policy

| Signal | Action |
|---|---|
| Test fails once, passes on retry | Track as flake; do not hide it |
| Same test flakes twice in 7 days | Quarantine from merge gate and create owner ticket |
| Quarantined test not fixed in 14 days | Delete or rewrite it |
| Critical journey flakes | Treat as release risk; fix before next train |
| Whole device pool flakes | Platform owner investigates infrastructure |

Quarantine is not forgiveness. It is a time-boxed safety valve so one bad test does not block the org while the owning team fixes it.

### Stable UI test design

Rules for long-lived UI tests:
- Prefer semantics and stable test tags over text that changes with copy.
- Disable or control animations in test builds.
- Inject fake clocks, fake repositories, and fake network states.
- Avoid sleeps; wait on UI state or idling resources.
- Keep one assertion theme per test: navigation, validation, rendering, or accessibility.
- Run broad visual coverage on JVM screenshots; reserve devices for flows that need the OS.

The test should fail because the product behavior changed, not because a spinner took 400 ms longer on one emulator.

---

## Compose UI Testing Setup

```kotlin
// :feature:cart:impl/build.gradle.kts
dependencies {
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}

android {
    defaultConfig {
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
}
```

A basic Compose UI test:

```kotlin
@RunWith(AndroidJUnit4::class)
class CartScreenTest {

    @get:Rule val composeRule = createComposeRule()

    @Test
    fun displaysEmptyState_whenCartEmpty() {
        composeRule.setContent {
            CartScreen(state = CartUiState.Empty)
        }

        composeRule.onNodeWithText("Your cart is empty").assertIsDisplayed()
        composeRule.onNodeWithTag("addItemButton").assertIsDisplayed()
    }

    @Test
    fun clickingAdd_callsOnAddCallback() {
        var clicked = false
        composeRule.setContent {
            CartScreen(
                state = CartUiState.Empty,
                onAdd = { clicked = true },
            )
        }

        composeRule.onNodeWithTag("addItemButton").performClick()
        assertTrue(clicked)
    }
}
```

Three patterns visible:
1. **`createComposeRule()`** — sets up the Compose host.
2. **`setContent { ... }`** — renders your composable.
3. **`onNodeWithText`/`onNodeWithTag`** — query the semantic tree.

---

## Semantics — The Foundation

Compose UI tests don't traverse the rendered pixel tree. They traverse the **semantics tree** — an abstraction that mirrors what accessibility services and tests see.

```kotlin
@Composable
fun CartItem(name: String, price: Money, onRemove: () -> Unit) {
    Row(
        modifier = Modifier
            .testTag("cart_item")                       // for tests
            .semantics { 
                contentDescription = "$name: $price"     // for accessibility AND tests
            },
    ) {
        Text(name)
        Text(price.toString())
        IconButton(onClick = onRemove) {
            Icon(Icons.Default.Close, contentDescription = "Remove $name")
        }
    }
}
```

`testTag` is for tests only — invisible to users, invisible to accessibility (mostly). `contentDescription` serves both.

The **goal**: tests look like accessibility checks. If a feature is hard to test, it's also hard to use with a screen reader.

### Finder APIs

| API | Use |
|---|---|
| `onNodeWithTag("...")` | By `testTag` |
| `onNodeWithText("...")` | By visible text |
| `onNodeWithContentDescription("...")` | By `contentDescription` |
| `onNode(hasText("...") and hasClickAction())` | Composite matcher |
| `onAllNodesWithTag("...")` | Multiple nodes; use `.onFirst()`, `.onLast()`, `[0]` to disambiguate |
| `onRoot().printToLog("TAG")` | Debug: dump the semantic tree |

The `printToLog` is your best friend when a test fails — see what Compose actually rendered.

### Assertion APIs

```kotlin
composeRule.onNodeWithText("Submit").assertIsDisplayed()
composeRule.onNodeWithText("Submit").assertIsEnabled()
composeRule.onNodeWithText("Submit").assertHasClickAction()
composeRule.onNodeWithText("Spinner").assertDoesNotExist()
composeRule.onNodeWithText("Loading").assertIsDisplayed()
```

`assertIsDisplayed` ≠ `assertExists`. The former requires the node to be on-screen and have non-zero size; the latter just checks the semantic tree contains it.

### Action APIs

```kotlin
composeRule.onNodeWithTag("name_input").performTextInput("Alice")
composeRule.onNodeWithText("Submit").performClick()
composeRule.onNodeWithTag("password").performTextClearance()
composeRule.onNodeWithTag("settings").performScrollTo()
composeRule.onRoot().performGesture {
    swipeLeft()
}
```

---

## Robolectric — JVM-Hosted Android

Robolectric runs Android code on the JVM by reimplementing key framework APIs. For Compose UI tests, it means **device-free testing at ~10x speed**.

```kotlin
// build.gradle.kts
android {
    testOptions {
        unitTests {
            isIncludeAndroidResources = true
        }
    }
}

dependencies {
    testImplementation(libs.robolectric)
    testImplementation(libs.androidx.compose.ui.test.junit4)
    testImplementation(libs.androidx.test.ext.junit)
}
```

```kotlin
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class CartScreenRobolectricTest {

    @get:Rule val composeRule = createComposeRule()

    @Test
    fun displaysCart() {
        composeRule.setContent {
            CartScreen(state = CartUiState.Success(items = listOf(item1)))
        }
        composeRule.onNodeWithText("Item 1").assertIsDisplayed()
    }
}
```

What Robolectric handles:
- `Resources` (string lookups, dimensions, drawables).
- `Context` (Application context).
- Most lifecycle classes.
- Compose runtime (with proper setup).

What it doesn't handle:
- Real animations (they snap to final values).
- Real font rendering (uses Layoutlib's approximations).
- Network/disk I/O (just like a unit test — must be faked).

The trade-off: faster, more isolated, slightly less realistic. For 90% of UI tests, this is fine.

---

## Paparazzi — Screenshot Testing on JVM

[Paparazzi](https://github.com/cashapp/paparazzi) renders Compose to images on the JVM (using Layoutlib, the same engine the Android Studio Preview uses).

```kotlin
// app/build.gradle.kts
plugins {
    id("app.cash.paparazzi") version "1.3.4"
}
```

```kotlin
class CartItemSnapshotTest {

    @get:Rule val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_5,
        theme = "android:Theme.Material.Light.NoActionBar",
    )

    @Test
    fun renders_default() {
        paparazzi.snapshot {
            AppTheme {
                CartItem(name = "Laptop", price = Money(1299_99), onRemove = {})
            }
        }
    }

    @Test
    fun renders_longName() {
        paparazzi.snapshot {
            AppTheme {
                CartItem(name = "A very long product name that should truncate gracefully", price = Money(1299_99), onRemove = {})
            }
        }
    }

    @Test
    fun renders_darkMode() {
        paparazzi.snapshot {
            AppTheme(darkTheme = true) {
                CartItem(name = "Laptop", price = Money(1299_99), onRemove = {})
            }
        }
    }
}
```

Workflow:
1. Run tests once: golden images are recorded.
2. Commit goldens to git (under `src/test/snapshots/`).
3. CI runs tests: compares fresh renders against goldens.
4. Any pixel diff fails the test.
5. Re-record with `./gradlew :feature:cart:impl:recordPaparazzi` when intentional.

### Why use Paparazzi

- Catches visual regressions humans miss (1px misalignment, color shift, theme leakage).
- Documents every component in every state with images (browse `src/test/snapshots/` like a design system gallery).
- Cheap to run (~50ms per test).
- Catches accidental layout changes early — before they reach QA.

### What Paparazzi isn't

- Not a behavior test — it doesn't click buttons or assert state.
- Not pixel-perfect realistic — Layoutlib differs subtly from real devices for fonts and gradients.
- Not a replacement for Compose UI tests — those test interactions.

Pair both: Paparazzi for visual, Compose UI tests for behavior.

### Variant testing

```kotlin
@Test
fun renders_allCardStyles() {
    listOf(CardStyle.Primary, CardStyle.Secondary, CardStyle.Outlined).forEach { style ->
        paparazzi.snapshot(name = "card_${style.name.lowercase()}") {
            AppTheme { Card(style = style, content = { Text("Sample") }) }
        }
    }
}
```

One test → three snapshot images, named.

---

## Test Tags vs Semantic Properties

Two ways to identify nodes:

```kotlin
// Approach A: testTag
Box(modifier = Modifier.testTag("cart_button")) { /* ... */ }
// Test: onNodeWithTag("cart_button")

// Approach B: Semantics (preferred for accessible components)
Box(modifier = Modifier.semantics { 
    contentDescription = "Cart button"
    role = Role.Button
}) { /* ... */ }
// Test: onNodeWithContentDescription("Cart button")
```

**Rule:** prefer semantic queries when the element is user-facing. Use `testTag` only when the element has no natural accessibility text (e.g., internal scaffolding).

Tests that match production accessibility behavior are more robust to UI refactors.

### `mergeDescendants`

```kotlin
Column(modifier = Modifier.semantics(mergeDescendants = true) {
    contentDescription = "Product card"
}) {
    Text("Laptop")
    Text("$1,299.99")
    Image(painter = painterResource(R.drawable.laptop), contentDescription = null)
}
```

Marks the whole subtree as one semantic unit (good for accessibility AND for tests). Otherwise the test sees three separate `Text` nodes.

---

## Hilt + Compose Tests

For dependency injection in UI tests:

```kotlin
@HiltAndroidTest
@RunWith(AndroidJUnit4::class)
class CartScreenHiltTest {

    @get:Rule(order = 0) val hiltRule = HiltAndroidRule(this)
    @get:Rule(order = 1) val composeRule = createAndroidComposeRule<HiltTestActivity>()

    @Inject lateinit var fakeRepository: FakeCartRepository

    @BeforeEach
    fun setUp() {
        hiltRule.inject()
    }

    @Test
    fun cartUpdates_whenRepositoryEmits() {
        composeRule.setContent {
            CartScreen()
        }

        composeRule.onNodeWithText("Empty").assertIsDisplayed()
        fakeRepository.addItem(item1)
        composeRule.onNodeWithText("Item 1").assertIsDisplayed()
    }
}
```

Override modules per test:

```kotlin
@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [CartRepositoryModule::class],
)
object FakeCartRepositoryModule {
    @Provides @Singleton
    fun provideRepo(): CartRepository = FakeCartRepository()
}
```

---

## ScreenshotTesting

A newer Android-official screenshot testing alternative to Paparazzi:

```kotlin
plugins {
    id("com.android.compose.screenshot") version "0.0.1-alpha15"
}

android {
    experimentalProperties["android.experimental.enableScreenshotTest"] = true
}
```

```kotlin
@PreviewTest
@Preview(showBackground = true)
@Composable
fun CartItemPreview() {
    AppTheme {
        CartItem(name = "Laptop", price = Money(1299_99), onRemove = {})
    }
}
```

Place `@PreviewTest`-annotated previews in the `screenshotTest` source set. The plugin renders them during `./gradlew :feature:cart:impl:validateDebugScreenshotTest` and compares the output with approved references.

Trade-off vs Paparazzi:
- Google-official; first-class IDE support.
- Slower than Paparazzi.
- Still experimental/alpha as of the official June 2026 documentation; APIs and required versions can change.

Paparazzi remains a mature third-party option. Choose based on IDE integration, rendering fidelity, execution cost, KMP constraints, and the Android plugin's experimental status; do not base the decision on a predicted graduation date.

---

## Testing Custom Modifiers

Custom modifiers (`Modifier.fadeIn()`, `Modifier.shimmer()`) often need their own tests:

```kotlin
@Test
fun shimmer_modifierAppliesGradient() {
    composeRule.setContent {
        Box(
            modifier = Modifier
                .size(100.dp)
                .shimmer()
                .testTag("shimmered"),
        )
    }
    composeRule.onNodeWithTag("shimmered").assertIsDisplayed()
    // Pair with Paparazzi for visual verification
}
```

The behavior is mostly visual — Paparazzi captures it more usefully than Compose UI tests.

---

## Test Robustness — Avoiding Flakiness

Flaky UI tests destroy test-suite credibility. Common causes and fixes:

### 1. Animations

```kotlin
@Before
fun disableAnimations() {
    composeRule.mainClock.autoAdvance = false      // pause clock
    // Run actions
    composeRule.mainClock.advanceTimeByFrame()     // step manually
    composeRule.mainClock.autoAdvance = true        // resume
}
```

Or globally:

```kotlin
// android/test/manifest:
<application android:name="androidx.test.core.app.testing.HiltTestApplication">
    <activity android:name="androidx.compose.ui.test.junit4.android.ComponentActivity"/>
</application>
```

And in build.gradle: `android.testOptions.animationsDisabled = true` for instrumentation tests.

### 2. Async work

```kotlin
composeRule.waitUntil(timeoutMillis = 3_000) {
    composeRule.onAllNodesWithText("Loaded").fetchSemanticsNodes().isNotEmpty()
}
```

Wait for an assertion to become true, not for a fixed time.

### 3. Coroutine awaits

```kotlin
// In test:
composeRule.awaitIdle()    // waits for all pending Compose work + coroutines
```

### 4. Idling resources

For complex async chains:

```kotlin
val idlingResource = CountingIdlingResource("Cart loading")

// In production code:
idlingResource.increment()
viewModelScope.launch {
    repo.load()
    idlingResource.decrement()
}

// In test:
composeRule.registerIdlingResource(idlingResource)
// ... assertions ...
composeRule.unregisterIdlingResource(idlingResource)
```

### Avoiding Flakes — Best Practices

- Never use `Thread.sleep` in tests. Always `waitUntil` or `awaitIdle`.
- Disable animations.
- Use unique test data (avoid global state).
- Reset all dependencies in `@BeforeEach`.
- Don't depend on test execution order.
- Fail loud — better to crash than silently pass.

---

## Accessibility Testing

```kotlin
@Test
fun cart_meetsAccessibilityRequirements() {
    composeRule.setContent {
        AppTheme { CartScreen(state = CartUiState.Success(items)) }
    }

    val node = composeRule.onNodeWithTag("cart_item").fetchSemanticsNode()

    // Tap targets at least 48dp
    val width = with(composeRule.density) { node.boundsInRoot.width.toDp() }
    val height = with(composeRule.density) { node.boundsInRoot.height.toDp() }
    assertTrue(width >= 48.dp && height >= 48.dp)

    // Has contentDescription
    val description = node.config[SemanticsProperties.ContentDescription]
    assertNotNull(description)
    assertTrue(description!!.first().isNotEmpty())
}
```

For systematic accessibility audits:

```kotlin
@get:Rule val a11yRule = AccessibilityChecksRule()
    .enableAccessibilityChecks()
    .enableThrowingOnFailure()
```

The rule runs Google's Accessibility Test Framework checks against every Compose hierarchy — catches contrast, tap targets, missing labels.

---

## Multi-Device Testing — Firebase Test Lab

For instrumentation tests on a matrix of real devices:

```bash
gcloud firebase test android run \
  --type instrumentation \
  --app app-debug.apk \
  --test app-debug-androidTest.apk \
  --device model=Pixel6,version=33 \
  --device model=Pixel6,version=34 \
  --device model=SamsungS21,version=33
```

CI integration available via [Gradle Play Publisher](https://github.com/Triple-T/gradle-play-publisher) and [Fladle](https://github.com/runningcode/fladle). Most teams use this for critical-path tests only — it's expensive.

---

## Real Patterns

### Pattern 1: Component-level Paparazzi gallery

```kotlin
@Test
fun renderAllButtonStyles() {
    listOf(
        ButtonStyle.Primary, ButtonStyle.Secondary,
        ButtonStyle.Destructive, ButtonStyle.Ghost,
    ).forEach { style ->
        paparazzi.snapshot(name = "button_${style.name.lowercase()}") {
            AppTheme {
                CompanyButton(style = style, onClick = {}) {
                    Text("Action")
                }
            }
        }
    }
}
```

One test, dozens of snapshots. Visual regression coverage for the entire design system in minutes.

### Pattern 2: Screen-level UI test with Hilt

```kotlin
@HiltAndroidTest
class CheckoutScreenTest {
    @get:Rule(order = 0) val hiltRule = HiltAndroidRule(this)
    @get:Rule(order = 1) val composeRule = createAndroidComposeRule<HiltTestActivity>()

    @Inject lateinit var fakeRepo: FakeCheckoutRepository

    @Before fun setUp() = hiltRule.inject()

    @Test
    fun submitSuccess_navigatesToConfirmation() {
        var navigatedTo: String? = null
        composeRule.setContent {
            CheckoutScreen(onNavigate = { navigatedTo = it })
        }
        composeRule.onNodeWithTag("submit_button").performClick()
        composeRule.waitUntil { navigatedTo == "confirmation/order123" }
        assertEquals("confirmation/order123", navigatedTo)
    }
}
```

### Pattern 3: State-driven Compose test (no Hilt)

```kotlin
@Test
fun loadingState_showsSpinner() {
    composeRule.setContent {
        AppTheme { CartScreen(state = CartUiState.Loading) }
    }
    composeRule.onNodeWithTag("loading_spinner").assertIsDisplayed()
}

@Test
fun errorState_showsRetryButton() {
    composeRule.setContent {
        AppTheme { CartScreen(state = CartUiState.Error("oops")) }
    }
    composeRule.onNodeWithText("Try again").assertIsDisplayed()
}
```

Faster — no DI graph init. Use for screens that accept state as a parameter (recommended pattern anyway).

### Pattern 4: Snapshot tests in multiple themes / locales

```kotlin
@get:Rule val paparazzi = Paparazzi(
    deviceConfig = DeviceConfig.PIXEL_5.copy(locale = "ar-XB"),
    theme = "android:Theme.Material.Light",
)

@Test
fun rtlLayout() {
    paparazzi.snapshot {
        AppTheme { CartItem(name = "Laptop", price = Money(1299_99), onRemove = {}) }
    }
}
```

Catches RTL bugs early. Most apps test LTR, dark mode, and one RTL locale per component.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Test passes locally, fails on CI | Animations enabled, race condition | Disable animations; use `waitUntil` |
| `onNodeWithText("...")` finds 0 nodes | Text inside a merged-descendant block | Use `useUnmergedTree = true` or query parent |
| Paparazzi reports diff but visually identical | Font hinting / pixel-level differences | Increase tolerance; use Paparazzi's `maxPercentDifference` |
| Compose Test hangs forever | Coroutine collecting in non-test scope | `composeRule.awaitIdle()` not enough — register IdlingResource |
| `HiltAndroidRule` works but `composeRule` doesn't see deps | Rule order wrong | `@get:Rule(order = 0)` for Hilt, `order = 1` for compose |
| `androidx.compose.ui.test.manifest` not in debug | Missing manifest dep | Add `debugImplementation` |
| Robolectric fails: "no Activity in test config" | Default activity not set | Use `createAndroidComposeRule<MyActivity>()` |
| `performTextInput` doesn't trigger TextField update | Test runs faster than Compose recomposition | `composeRule.waitForIdle()` after input |
| Screenshot fails on Linux but works on macOS | Font fallback differences | Pin to a single OS in CI; or commit per-OS goldens (rare) |
| `onAllNodesWithTag` selects too many | Duplicate `testTag` | Make tags unique or use indexed `[i]` |
| `@HiltAndroidTest` not picked up | Forgot Hilt test runner | Add `testInstrumentationRunner` or `HiltTestApplication` |
| Slow test suite (5min) | Mix of unit and instrumentation tests | Split into separate Gradle tasks |
| Flaky `waitUntil` | Polling interval too long or timeout too short | Tune; or use IdlingResource |
| Tests don't dismiss snackbars between cases | Reusing scope across tests | Reset state in `@BeforeEach` |
| `mergeDescendants` blocks individual child queries | Semantic boundary set | Use `useUnmergedTree = true` |
| Paparazzi golden out of date | Intentional UI change but not re-recorded | `./gradlew recordPaparazzi` to update |

---

## Common Pitfalls

- **Compose UI tests on every PR.** Slower than unit tests; run fewer in CI per PR, full suite on main.
- **No testTag strategy.** Engineers invent them ad-hoc; no consistent pattern. Add lint rule for naming.
- **Mixing test types in same module.** Keep `src/test/` (unit) and `src/androidTest/` (instrumentation) separate.
- **Testing internal implementation.** A test that checks "view is a `LinearLayout`" breaks on refactor. Test behavior.
- **Snapshot tests of dynamic content.** Date/time changes per run, so do random IDs. Inject `Clock` and seed `Random`.
- **No baseline diff review.** When 50 snapshots change in a PR, you can't eyeball each. Use Paparazzi's HTML diff report; have a designer review.
- **Paparazzi for behavior tests.** Wrong tool — use Compose UI tests.
- **Compose UI tests for visual regression.** Wrong tool — use Paparazzi.
- **No Hilt + Compose pattern.** Each team invents their own. Document in convention plugins.
- **Treating Robolectric as "real Android."** It approximates. Real-device tests still needed for production critical paths.
- **Tests pass with `Thread.sleep(5_000)`.** Slow + flaky. Always use `waitUntil`.

---

## Probing Questions

1. Compose UI test vs Paparazzi vs Robolectric — when each?
2. Semantic queries vs `testTag` — when use each?
3. Walk through structuring a Hilt + Compose UI test with `HiltAndroidRule`.
4. Why are animation-related test failures the most common flakes? How do you fix them globally?
5. `mergeDescendants` — what does it do? How does it interact with test queries?
6. Paparazzi vs Compose Screenshot Testing — what's the trade-off?
7. A new engineer writes a Compose UI test that fails on CI with 50% reliability. Walk through your debugging.
8. Multi-theme / multi-locale snapshot testing — how to set up?
9. Accessibility testing in Compose — what tools, what assertions?
10. Why do you sometimes need `IdlingResource` even with `awaitIdle()`?
11. A junior creates 200 testTags called "button1", "button2", etc. What's the code-review pushback?
12. Component-level Paparazzi vs screen-level Compose UI tests — which catches what?

---

## Further Reading

- [`unit-testing.md`](unit-testing.md) — JVM-only tests.
- [`../compose/recomposition-and-state.md`](../compose/recomposition-and-state.md) — what gets tested.
- [`../compose/stability.md`](../compose/stability.md) — recomposition during tests.
- [`../compose/snapshot-system.md`](../compose/snapshot-system.md) — state changes during test.
- [`../data-and-di/hilt-vs-koin-vs-manual-di.md`](../data-and-di/hilt-vs-koin-vs-manual-di.md) — `@TestInstallIn` patterns.
- [`../performance/rendering.md`](../performance/rendering.md) — rendering tests catch.
- [`../build-tooling/multi-module.md`](../build-tooling/multi-module.md) — `:test:fixtures` shared fakes.
- [Compose UI testing official docs](https://developer.android.com/jetpack/compose/testing) — official.
- [Robolectric](http://robolectric.org/) — official.
- [Paparazzi](https://github.com/cashapp/paparazzi) — screenshot tests.
- [Android Compose Screenshot Testing](https://developer.android.com/studio/preview/compose-screenshot-testing) — official alpha.
- [Espresso (for legacy)](https://developer.android.com/training/testing/espresso) — official.
- [Firebase Test Lab](https://firebase.google.com/docs/test-lab) — cross-device matrix.

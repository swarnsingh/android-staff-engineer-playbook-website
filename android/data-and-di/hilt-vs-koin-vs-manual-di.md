# Dependency Injection: Hilt vs Koin vs Manual DI

> Every Android app has DI — the question is whether it's intentional. Done well, DI gives you fast tests, swappable implementations, and clean module boundaries. Done badly, it tanks build time, crashes on first launch, or forces every test to construct the entire object graph. **Hilt** is the conventional Android-integrated choice, **Koin** is a serious option for KMP and runtime-configured graphs, and **manual DI** is often the smallest and most transparent choice for libraries and modest graphs. Verify current compiler/plugin capabilities before choosing.

---

> [!NOTE]
> **Kotlin Multiplatform Deep Dive:** For a comprehensive guide on sharing Koin graphs across Android and iOS within a KMP module, resolving cross-platform initializations, and dealing with platform-specific injections, see [`../kotlin-multiplatform/ecosystem/dependency-injection.md`](../kotlin-multiplatform/ecosystem/dependency-injection.md).

---

## Why DI Matters (Briefly)

Without DI, your `CheckoutViewModel` constructs its own `Repository`, which constructs its own `Retrofit`, which constructs its own `OkHttp`. Every test of the ViewModel runs a real network. Every change to `OkHttp`'s init touches `CheckoutViewModel`.

With DI:

- Dependencies are **passed in** (constructor params).
- Tests substitute fakes trivially.
- Lifecycle scopes are explicit.
- Modules are testable in isolation.

The mechanism — Hilt, Koin, manual — affects ergonomics, build time, and crash-class profile. The underlying *principle* is the same.

### DI ≠ Service Locator

A subtle but important distinction:

- **DI** — the container *gives* you your dependencies via constructor parameters. The class is unaware of the container.
- **Service Locator** — the class *asks* the container for its dependencies (`container.get<Repo>()`). The class depends on the container.

Service Locator hides dependencies behind global accessors. DI makes them visible in the constructor signature. **Always prefer DI.** Koin started as a Service Locator and has evolved toward DI semantics; we'll come back to this.

---

## Option 1: Manual DI

Before reaching for a framework, know what it's saving you from.

```kotlin
class NetworkService(client: OkHttpClient)
class UserRepository(private val api: NetworkService)
class CheckoutViewModel(private val repo: UserRepository) : ViewModel()

class AppContainer(applicationContext: Context) {
    val okHttp by lazy { OkHttpClient.Builder().build() }
    val networkService by lazy { NetworkService(okHttp) }
    val userRepository by lazy { UserRepository(networkService) }

    fun checkoutViewModelFactory(): ViewModelProvider.Factory =
        object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                CheckoutViewModel(userRepository) as T
        }
}

// MainApplication
class MainApplication : Application() {
    lateinit var container: AppContainer
    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}

// Activity
val vm: CheckoutViewModel by viewModels {
    (application as MainApplication).container.checkoutViewModelFactory()
}
```

**Pros:**
- Zero build-time overhead.
- No reflection, no annotation processors, no library upgrade risk.
- 100% explicit — you see every wire.
- Required for SDKs (you can't force consumers to use your DI framework).

**Cons:**
- Massive boilerplate at scale. `AppContainer` grows to thousands of lines.
- Scoping (per-Activity, per-Session) is manual and error-prone.
- ViewModelFactory plumbing for every ViewModel.
- Renaming a constructor parameter is a multi-file change.

**Verdict:** SDKs, libraries, and very small apps (< 5 screens). Anything bigger needs a framework.

---

## Option 2: Hilt (Dagger Wrapped)

Hilt is Google's opinionated Dagger wrapper, generating the factory code at compile time.

```kotlin
@HiltAndroidApp
class MainApplication : Application()

@Singleton
class NetworkService @Inject constructor(private val okHttp: OkHttpClient)

@Singleton
class UserRepository @Inject constructor(private val api: NetworkService)

@HiltViewModel
class CheckoutViewModel @Inject constructor(
    private val repository: UserRepository,
) : ViewModel()

@AndroidEntryPoint
class CheckoutActivity : AppCompatActivity() {
    private val vm: CheckoutViewModel by viewModels()
}
```

For things you don't own (interfaces, Retrofit instances), use modules:

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides @Singleton
    fun provideOkHttp(): OkHttpClient =
        OkHttpClient.Builder()
            .addInterceptor(HttpLoggingInterceptor())
            .build()

    @Provides @Singleton
    fun provideRetrofit(okHttp: OkHttpClient): Retrofit =
        Retrofit.Builder()
            .baseUrl("https://api.example.com/")
            .client(okHttp)
            .build()
}
```

### Hilt Scope Hierarchy

Hilt's killer feature: predefined scopes that match Android's lifecycle.

| Scope | Lives as long as | Use for |
|---|---|---|
| `@Singleton` | Application | Retrofit, Room DB, analytics, app-wide caches |
| `@ActivityRetainedScoped` | Activity (survives rotation) | ViewModels via `@HiltViewModel` |
| `@ActivityScoped` | Activity instance | Activity-specific state (rare) |
| `@ViewModelScoped` | ViewModel | Per-screen repositories, use-cases |
| `@FragmentScoped` | Fragment | Fragment-specific UI helpers |
| `@ViewScoped` | View | Custom view helpers |
| `@ServiceScoped` | Service | Service-local resources |

Each scope corresponds to a `Component` (`SingletonComponent`, `ActivityComponent`, etc.). Dependencies installed in a lower-scope component can access higher-scope dependencies, but not the reverse.

### Hilt Assisted Inject

For dependencies that need *runtime* parameters (a `productId` that comes from a deeplink):

```kotlin
@HiltViewModel(assistedFactory = DetailViewModel.Factory::class)
class DetailViewModel @AssistedInject constructor(
    @Assisted val productId: String,
    private val repo: ProductRepository,
) : ViewModel() {

    @AssistedFactory
    interface Factory {
        fun create(productId: String): DetailViewModel
    }
}

// Composable
val vm: DetailViewModel = hiltViewModel<DetailViewModel, DetailViewModel.Factory>(
    creationCallback = { factory -> factory.create(productId) }
)
```

### Entry Points (For Non-Hilt-Aware Classes)

When you need a Hilt-provided object inside something Hilt doesn't manage (`ContentProvider`, third-party callbacks):

```kotlin
@EntryPoint
@InstallIn(SingletonComponent::class)
interface AnalyticsEntryPoint {
    fun analytics(): Analytics
}

// Then anywhere:
val analytics = EntryPointAccessors
    .fromApplication(context, AnalyticsEntryPoint::class.java)
    .analytics()
```

### Hilt + Compose ViewModel

```kotlin
@Composable
fun CartScreen() {
    val vm: CartViewModel = hiltViewModel()    // resolves via @HiltViewModel
    val state by vm.state.collectAsStateWithLifecycle()
    // ...
}
```

### Hilt + WorkManager

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted params: WorkerParameters,
    private val repo: SyncRepository,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result { /* ... */ }
}
```

### The Build-Time Cost

Hilt was historically built on **KAPT** (Kotlin Annotation Processing Tool) — slow, single-threaded, breaks incremental compilation. Since Hilt 2.48 + Dagger 2.48, **KSP** support is stable. KSP is 2× faster than KAPT and incremental.

```kotlin
plugins {
    id("com.google.dagger.hilt.android")
    id("com.google.devtools.ksp")
}

dependencies {
    implementation("com.google.dagger:hilt-android:2.50")
    ksp("com.google.dagger:hilt-compiler:2.50")
}
```

Still: Hilt generates a lot of code. On a 100-module project, the Hilt step is often the bottleneck. Run `./gradlew assembleDebug --scan` and inspect "Annotation processing" time. If it's > 30%, the Hilt step is your slowest task.

### Pros / Cons

**Pros:**
- Compile-time safety. Forget a `@Provides` and the build fails.
- Predefined Android scopes match Android's lifecycle exactly.
- Deep Jetpack integration (Compose, ViewModel, WorkManager, Navigation).
- Google-supported.

**Cons:**
- Build time, even on KSP, is significant.
- Cryptic compile errors (`error: [Dagger/MissingBinding]`) require Dagger fluency.
- Tied to Android — does not work for pure-Kotlin / KMP modules.
- Heavyweight if your project is small.

---

## Option 3: Koin (Now With Compiler Plugin)

Koin started as a **Service Locator** — dependencies resolved at runtime via a global registry. Mostly perceived as "lightweight, fast build, but no compile-time safety." That's no longer the full story.

Since **Koin Annotations 1.4+** (using Koin's native Kotlin Compiler Plugin), Koin offers compile-time graph verification matching Hilt's safety, while preserving its faster build time.

### Basic Koin (DSL Style)

The original Koin API uses a DSL:

```kotlin
val networkModule = module {
    single { OkHttpClient.Builder().build() }
    single { NetworkService(get()) }
    single { UserRepository(get()) }
    viewModel { CheckoutViewModel(get()) }
}

class MainApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        startKoin {
            androidContext(this@MainApplication)
            modules(networkModule)
        }
    }
}

class CheckoutActivity : AppCompatActivity() {
    private val vm: CheckoutViewModel by viewModel()
}
```

DSL-style is "runtime DI" — the graph is built at startup; missing dependencies crash at first access. Quick to write; crashes ship to prod.

### Koin Annotations (Modern, Compile-Time Safe)

With Koin Annotations + the compiler plugin:

```kotlin
@Single
class NetworkService(private val okHttp: OkHttpClient)

@Single
class UserRepository(private val api: NetworkService)

@KoinViewModel
class CheckoutViewModel(
    private val repository: UserRepository,
) : ViewModel()

@Module
@ComponentScan("com.example.app")
class AppModule

class MainApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        startKoin {
            androidContext(this@MainApplication)
            modules(AppModule().module)
        }
    }
}
```

The compiler plugin generates the module registration code, validates the graph at compile time, and supports KMP.

### Koin Scopes

| Definition | Lives | Equivalent Hilt |
|---|---|---|
| `single { }` / `@Single` | App | `@Singleton` |
| `factory { }` / `@Factory` | New each request | None (Hilt = no annotation) |
| `scoped { }` / `@Scope` | Custom scope (e.g., feature) | Closest to `@ActivityRetainedScoped` |
| `viewModel { }` / `@KoinViewModel` | ViewModel | `@HiltViewModel` |

Koin's scopes are more flexible than Hilt's (you can define your own), but they don't match Android's lifecycle as automatically.

### Pros / Cons

**Pros:**
- Build time is much faster than Hilt (no Dagger codegen volume).
- KMP-friendly — works for iOS / desktop / web targets.
- DSL is approachable; annotations are familiar.
- With the compiler plugin: compile-time graph validation.

**Cons:**
- DSL-style still allows you to ship runtime crashes (`NoBeanDefFoundException`).
- Less rigid scope hierarchy than Hilt — Android lifecycle integration is less automatic.
- Smaller community than Hilt (though active and growing).
- Mixing DSL and annotations in the same codebase is confusing.

---

## Manual DI vs Hilt vs Koin: Side-by-Side

| Property | Manual DI | Hilt | Koin (DSL) | Koin (Annotations) |
|---|---|---|---|---|
| Compile-time safety | Manual | Yes | No | Yes |
| Build time impact | None | High | Low | Low–Medium |
| Boilerplate | High | Low | Low | Low |
| Multi-module wiring | Manual | First-class | Manual | First-class |
| KMP support | Yes | No | Yes | Yes |
| Scope flexibility | Manual | Fixed set | Flexible | Flexible |
| Compose integration | Manual factory | `hiltViewModel()` | `koinViewModel()` | `koinViewModel()` |
| WorkManager | Manual | `@HiltWorker` | Manual `module` | `@KoinWorker` |
| Testing fakes | Direct construction | `@TestInstallIn` | `loadKoinModules` | `loadKoinModules` |

---

## Multi-Module DI

The pattern modern Android codebases use:

```
:feature:cart:api    — interfaces, sealed UI states
:feature:cart:impl   — Hilt modules + ViewModel + Repository
:app                 — wires everything together
```

### Hilt multi-module

Each `:impl` module ships a `@Module @InstallIn(SingletonComponent::class)` that binds its `:api` interfaces. The `:app` module installs the Hilt application. No additional configuration: Hilt walks the classpath and merges all `@Module`s automatically.

### Koin multi-module

Each module exports a `Module` value. The `:app` collects them and passes to `startKoin`:

```kotlin
startKoin {
    androidContext(this@MainApplication)
    modules(
        listOf(
            cartModule,
            paymentsModule,
            analyticsModule,
        )
    )
}
```

Slightly more manual; trivially testable per module.

---

## Testing

### Hilt — `@TestInstallIn`

```kotlin
@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [NetworkModule::class],
)
object FakeNetworkModule {
    @Provides @Singleton
    fun provideApi(): Api = FakeApi()
}

@HiltAndroidTest
class CheckoutTest {
    @get:Rule val hiltRule = HiltAndroidRule(this)
    @Inject lateinit var vm: CheckoutViewModel
    @Test fun checkout_emitsSuccess() { /* ... */ }
}
```

### Koin — `loadKoinModules` + override

```kotlin
@Before
fun setup() {
    startKoin {
        modules(appModule)
    }
    loadKoinModules(
        module(override = true) {
            single<Api> { FakeApi() }
        }
    )
}

@After fun teardown() { stopKoin() }
```

---

## Migration Paths

| From | To | Notes |
|---|---|---|
| Manual → Hilt | Add `@HiltAndroidApp`; annotate one module at a time. Hilt happily coexists with manual code for the migration period. |
| Manual → Koin | Add `startKoin` + a single module first, retire `AppContainer` gradually. |
| Dagger → Hilt | Use Hilt's `@HiltAndroidApp` + migrate components one at a time. Dagger and Hilt coexist via `@DefineComponent`. |
| Koin DSL → Koin Annotations | Coexist freely; annotate gradually. |
| Hilt → Koin | Rare. Usually because of KMP needs or build time. Module-by-module migration. |
| Koin → Hilt | Rare. Usually after a runtime crash from a missing definition. Rip-and-replace; both can't coexist easily. |

---

## When Each Wins

| Scenario | Pick |
|---|---|
| Public SDK | **Manual DI** — never force consumers into a framework |
| KMP app | **Koin** — Hilt is Android-only |
| Android-only enterprise app, 50+ modules | **Hilt** — scoping discipline + compile-time safety pay off |
| Android-only app where build time is killing morale | **Koin (annotations)** — drop in 2x speedup |
| New small app (< 10 screens) | **Either**, leaning Koin for simplicity |
| Legacy Dagger codebase | **Migrate to Hilt** — same compile-time safety, much less ceremony |
| Need fastest test cycle | **Koin** — DSL fakes load instantly |

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Build fails: `[Dagger/MissingBinding]` | Hilt can't construct a dep | Add `@Provides` or `@Inject constructor` |
| Build fails: `[Dagger/DuplicateBindings]` | Two `@Provides` for the same type | Use `@Qualifier` or remove one |
| Build time 90s on every change | KAPT in use | Migrate to KSP (Hilt 2.48+) |
| Runtime crash `NoBeanDefFoundException` (Koin DSL) | Module forgot the definition | Migrate to Koin Annotations for compile check, or add the definition |
| Hilt complains "non-Hilt-managed class" | Activity / Fragment not `@AndroidEntryPoint` | Annotate it |
| ViewModel constructor needs runtime param | Hilt can't inject it directly | Use `@AssistedInject` + `@AssistedFactory` |
| Mock isn't injected in test | Hilt picks production module first | `@TestInstallIn(replaces = [...])` |
| Circular dependency | A → B → A | Refactor (often via interface) or introduce `Provider<T>` for lazy resolution |
| Memory leak — singleton holds Activity | Wrong scope | Use `@ActivityRetainedScoped` / `@ActivityScoped`, never `@Singleton` for Activity-coupled state |
| `EntryPointAccessors` returns wrong scope | Wrong component | Match the component to the lifetime (Application/Activity) |
| ProGuard/R8 strips Hilt classes | Missing keep rules | `consumer-rules.pro` from Hilt is automatic; verify R8 isn't stripping yours |
| Koin `single` recreated every test | `stopKoin()` not called | `@After fun teardown() { stopKoin() }` |
| Hilt + Compose fails with "no ViewModelProvider.Factory" | `LocalContext.current` not Hilt-aware | Use `hiltViewModel()` from `androidx.hilt.navigation.compose` |

---

## Common Pitfalls

- **Mixing Koin DSL and Annotations carelessly.** Pick one style per module to keep mental model consistent.
- **Wrong Hilt scope.** `@Singleton` for an Activity-tied object = memory leak forever. Pick the smallest scope that fits.
- **Forgetting `@Qualifier`.** Two `OkHttpClient`s (auth vs unauthenticated)? Without qualifiers, Hilt can't disambiguate.
- **Service Locator usage of Koin DSL.** Calling `getKoin().get<Repo>()` throughout your code defeats DI — it's now a runtime locator. Use constructor injection.
- **Heavy work in `@HiltAndroidApp` `onCreate`.** Every `@Provides` graph is wired eagerly for `@Singleton`. Defer with `Lazy<T>`.
- **`@Singleton` for everything.** Then your test container holds half the world. Smaller scopes = faster tests.
- **No `@HiltWorker` for WorkManager.** `WorkManagerInitializer` doesn't see Hilt-managed Workers without the annotation + `androidx.hilt:hilt-work` dep.
- **Manual `ViewModelFactory` with Hilt installed.** Just annotate `@HiltViewModel` and inject via `hiltViewModel()` / `by viewModels()`.

---

## Probing Questions

1. Explain DI vs Service Locator. Why is constructor injection preferred?
2. Walk through Hilt's scope hierarchy. Why does `@Singleton` matter vs `@ActivityRetainedScoped`?
3. KAPT vs KSP — concrete build time difference. How do you migrate Hilt from KAPT to KSP?
4. Your app needs runtime parameters in a ViewModel (a `productId` from a deeplink). How do you wire it with Hilt?
5. Why is Koin's DSL form considered a Service Locator? How do Koin Annotations + compiler plugin change that?
6. You're building a public SDK. Which DI approach do you ship, and why?
7. A KMP project must share business logic between Android and iOS. Pick Hilt or Koin. Justify.
8. Hilt complains `[Dagger/MissingBinding]` for `Foo` requested from `Bar`. Walk through your debugging.
9. Two `OkHttpClient`s in your graph (authenticated vs unauthenticated). How do you wire both?
10. Compare the testing story: how do you swap a real `Api` for a `FakeApi` in Hilt vs Koin?
11. A circular dependency `UserRepo → AuthClient → UserRepo`. How do you fix it (two valid approaches)?
12. Build times jumped 40% after migrating to Hilt. Walk through investigation.

---

## Further Reading

- [`components.md`](components.md) — Hilt component hierarchy deep dive.
- [`scopes.md`](scopes.md) — Hilt scopes vs coroutine scopes compared.
- [`dependency-injection.md`](dependency-injection.md) — DI patterns canonical.
- [`room-vs-datastore.md`](room-vs-datastore.md) — injecting DAOs / DataStore.
- [`../architecture/modularization-strategies.md`](../architecture/modularization-strategies.md) — DI across `:api` / `:impl` modules.
- [`../architecture/viewmodel.md`](../architecture/viewmodel.md) — `@HiltViewModel` and factories.
- [`../../platform-engineering/build-graph-scaling.md`](../../platform-engineering/build-graph-scaling.md) — KAPT → KSP migration impact.
- [`../../kotlin/language-core/delegation.md`](../../kotlin/language-core/delegation.md) — `by viewModels()` / `by hiltViewModel()` mechanics.
- [Hilt documentation](https://developer.android.com/training/dependency-injection/hilt-android) — official.
- [Koin documentation](https://insert-koin.io/) — official.
- [Koin Annotations](https://insert-koin.io/docs/reference/koin-annotations/start) — compiler plugin reference.
- [Manuel Vivo — Hilt deep dive](https://medium.com/androiddevelopers/) — Google DevRel posts.

# Dependency Injection in KMP

> Dependency Injection is the glue that binds the shared `commonMain` logic to the platform-specific implementations (Android's `Context`, iOS's `NSURLSession`, the correct SQL driver). In Android, you use Hilt/Dagger — but Dagger generates JVM code via KAPT/KSP that cannot compile on Kotlin/Native. A Staff engineer must know how to architect a Koin-based DI graph that spans `commonMain`, `androidMain`, and `iosMain`, and critically, how to initialize it from Swift's `AppDelegate` without exposing Kotlin's `reified` generics or inline functions.

---

## Overview

### Why Not Hilt/Dagger?

Dagger's code generation pipeline:
```text
Kotlin source → KSP/KAPT → Generated Java stubs → javac compiles stubs
                                                    → Produces Dagger_Component.java
```

Every step in this chain depends on the JVM:
- KSP runs as a JVM process that generates `.java` files.
- The generated Dagger components use `javax.inject` annotations.
- The `Provider<T>` pattern uses `java.lang.reflect.Constructor`.

None of this exists in Kotlin/Native's LLVM pipeline. **Dagger is architecturally impossible on iOS.**

### The KMP DI Landscape

| Framework | Resolution | KMP Support | Compile-Time Safety |
|---|---|---|---|
| **Dagger / Hilt** | Compile-time (codegen) | ❌ JVM only | ✅ Full |
| **Koin** | Runtime (service locator) | ✅ Full KMP | ⚠️ Runtime crashes on missing deps |
| **Koin + Compiler Plugin** | Compile-time verification | ✅ Full KMP | ✅ Verified at build time |
| **kotlin-inject** | Compile-time (KSP codegen) | 🟡 Partial (JVM + iOS) | ✅ Full |
| **Manual DI** | None (hand-wired) | ✅ Trivially | ✅ Compile-time by definition |

**Staff Recommendation:** Use **Koin with the Compiler Plugin** for KMP projects. You get runtime flexibility with compile-time graph validation.

---

## 1. Architecting the Koin Module Graph

### The Three-Layer Module Architecture

```text
┌────────────────────────────────────────────────────────┐
│ Layer 3: Platform Modules (androidMain / iosMain)      │
│ Provides: SqlDriver, HttpClientEngine, Context, etc.   │
│ These modules are DIFFERENT on each platform.           │
├────────────────────────────────────────────────────────┤
│ Layer 2: Feature Modules (commonMain)                   │
│ Provides: ViewModels, UseCases                          │
│ Consumes: Repositories, APIs from Layer 1               │
├────────────────────────────────────────────────────────┤
│ Layer 1: Core Modules (commonMain)                      │
│ Provides: HttpClient, Database, Repositories, APIs      │
│ Consumes: SqlDriver, HttpClientEngine from Layer 3      │
└────────────────────────────────────────────────────────┘
```

### Layer 1: Core Module (`commonMain`)

```kotlin
// shared/src/commonMain/kotlin/di/CoreModule.kt

val coreModule = module {
    // HttpClient — uses the engine from the platform module
    single<HttpClient> {
        createHttpClient(
            engine = get(),           // Platform provides HttpClientEngine
            baseUrl = "https://api.example.com",
            authTokenProvider = { get<AuthRepository>().getToken() }
        )
    }
    
    // Database — uses the driver from the platform module
    single<AppDatabase> {
        AppDatabase(driver = get())   // Platform provides SqlDriver
    }
    
    // Repositories
    single<ProductRepository> { ProductRepositoryImpl(get(), get()) }
    single<UserRepository> { UserRepositoryImpl(get(), get()) }
    single<AuthRepository> { AuthRepositoryImpl(get(), get()) }
    
    // API clients
    single<ProductApi> { ProductApi(get()) }
    single<UserApi> { UserApi(get()) }
    single<AuthApi> { AuthApi(get()) }
}
```

### Layer 2: Feature Module (`commonMain`)

```kotlin
// shared/src/commonMain/kotlin/di/FeatureModule.kt

val featureModule = module {
    // ViewModels — created as factories (new instance each time)
    factory { HomeViewModel(get(), get()) }
    factory { CheckoutViewModel(get(), get(), get()) }
    factory { ProfileViewModel(get()) }
    factory { SearchViewModel(get()) }
    
    // Use Cases (if using Clean Architecture)
    factory { GetProductsUseCase(get()) }
    factory { SubmitOrderUseCase(get(), get()) }
    factory { ValidatePromoUseCase(get()) }
}
```

### Layer 3: Platform Modules (the `expect`/`actual` boundary)

```kotlin
// shared/src/commonMain/kotlin/di/PlatformModule.kt

/**
 * Each platform must provide this module.
 * It supplies the platform-specific implementations that the core module needs.
 */
expect fun platformModule(): Module
```

**Android implementation:**
```kotlin
// shared/src/androidMain/kotlin/di/PlatformModule.android.kt

actual fun platformModule(): Module = module {
    // SQL Driver — needs Android Context
    single<SqlDriver> {
        AndroidSqliteDriver(
            schema = AppDatabase.Schema,
            context = get(),    // androidContext() provides this
            name = "app.db",
            callback = object : AndroidSqliteDriver.Callback(AppDatabase.Schema) {
                override fun onOpen(db: SupportSQLiteDatabase) {
                    db.execSQL("PRAGMA journal_mode=WAL")
                    db.execSQL("PRAGMA foreign_keys=ON")
                }
            }
        )
    }
    
    // HTTP Engine — OkHttp on Android
    single<HttpClientEngine> {
        OkHttp.create {
            config {
                connectTimeout(10, TimeUnit.SECONDS)
                readTimeout(30, TimeUnit.SECONDS)
            }
        }
    }
    
    // Platform-specific services
    single<LocationService> { AndroidLocationService(get()) }
    single<CrashReporter> { FirebaseCrashReporter() }
    single<NotificationService> { AndroidNotificationService(get()) }
}
```

**iOS implementation:**
```kotlin
// shared/src/iosMain/kotlin/di/PlatformModule.ios.kt

actual fun platformModule(): Module = module {
    // SQL Driver — no Context needed on iOS
    single<SqlDriver> {
        NativeSqliteDriver(
            schema = AppDatabase.Schema,
            name = "app.db"
        )
    }
    
    // HTTP Engine — Darwin (NSURLSession) on iOS
    single<HttpClientEngine> {
        Darwin.create {
            configureSession {
                setTimeoutIntervalForRequest(30.0)
            }
        }
    }
    
    // Platform-specific services
    single<LocationService> { IOSLocationService() }
    single<CrashReporter> { SentryCrashReporter() }
    single<NotificationService> { IOSNotificationService() }
}
```

---

## 2. Initializing Koin

### On Android (Standard)

```kotlin
// androidApp/src/main/java/com/example/MyApplication.kt

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        
        initKoin {
            androidContext(this@MyApplication)  // Provides Context to the graph
            modules(coreModule, featureModule, platformModule())
        }
    }
}
```

### On iOS (The Tricky Part)

Swift cannot call `startKoin` directly because Koin's DSL uses Kotlin `inline` functions with `reified` type parameters. These don't bridge through Objective-C.

**Step 1: Create an iOS-specific initialization function in `iosMain`:**

```kotlin
// shared/src/iosMain/kotlin/di/KoinIOS.kt

fun initKoinIOS() {
    initKoin {
        modules(coreModule, featureModule, platformModule())
    }
}

// Helper: Direct Koin access for Swift (since Swift can't use reified generics)
private val koinApp = KoinPlatform.getKoin()

object ViewModelFactory {
    fun createHomeViewModel(): HomeViewModel = koinApp.get()
    fun createCheckoutViewModel(): CheckoutViewModel = koinApp.get()
    fun createProfileViewModel(): ProfileViewModel = koinApp.get()
    fun createSearchViewModel(): SearchViewModel = koinApp.get()
}
```

**Step 2: Call from Swift:**

```swift
// iosApp/iOSApp.swift

@main
struct IOSApp: App {
    init() {
        KoinIOSKt.initKoinIOS()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

// Using ViewModels in SwiftUI
struct HomeScreen: View {
    let viewModel = ViewModelFactory.shared.createHomeViewModel()
    @State private var state = HomeState.companion.initial
    
    var body: some View {
        VStack { /* ... */ }
        .task {
            for await newState in viewModel.state {
                self.state = newState
            }
        }
    }
}
```

---

## 3. Koin Compiler Plugin (Compile-Time Safety)

Koin's biggest criticism is that it's a service locator — if you forget to provide a dependency, the app crashes at runtime with `NoBeanFoundException`. The **Koin Compiler Plugin** (introduced in Koin 3.5+) solves this.

### Setup

```kotlin
// shared/build.gradle.kts
plugins {
    id("org.koin.kmp") version "1.3.1"  // Koin KSP Plugin
}

dependencies {
    // KSP runs at compile time and verifies the module graph
    add("kspCommonMainMetadata", libs.koin.ksp.compiler)
}
```

### How It Works

You annotate your classes with `@Single`, `@Factory`, or `@KoinViewModel`:

```kotlin
// Instead of manually writing Koin modules...

@Single
class ProductRepositoryImpl(
    private val api: ProductApi,
    private val database: AppDatabase
) : ProductRepository {
    // ...
}

@Factory
class HomeViewModel(
    private val productRepository: ProductRepository,
    private val userRepository: UserRepository
) {
    // ...
}
```

The Koin KSP compiler:
1. Scans all annotated classes.
2. Resolves the dependency graph at compile time.
3. **Reports missing dependencies as build errors**, not runtime crashes.
4. Generates the `module { }` DSL code automatically.

### Compile-Time Error Example

If you annotate `HomeViewModel` with `@Factory` but forget to annotate `ProductRepository`:

```
error: [Koin] Missing definition for type 'ProductRepository'
       required by 'HomeViewModel' constructor parameter 'productRepository'
```

This error appears **during compilation**, not at runtime. The app cannot be built until the dependency is provided.

---

## 4. Manual DI (The Zero-Framework Approach)

For small KMP modules or teams that distrust service locators, manual DI is viable:

```kotlin
// shared/src/commonMain/kotlin/di/SharedContainer.kt

class SharedContainer(
    private val sqlDriver: SqlDriver,
    private val httpEngine: HttpClientEngine
) {
    // Singletons
    private val database: AppDatabase by lazy { AppDatabase(sqlDriver) }
    private val httpClient: HttpClient by lazy { createHttpClient(httpEngine, "https://api.example.com") { null } }
    
    // Repositories
    private val productApi: ProductApi by lazy { ProductApi(httpClient) }
    private val productRepository: ProductRepository by lazy { ProductRepositoryImpl(productApi, database) }
    
    // ViewModels (factory — new instance each call)
    fun homeViewModel() = HomeViewModel(productRepository)
    fun checkoutViewModel() = CheckoutViewModel(productRepository)
}
```

```kotlin
// androidMain
val container = SharedContainer(
    sqlDriver = AndroidSqliteDriver(AppDatabase.Schema, context, "app.db"),
    httpEngine = OkHttp.create()
)

// iosMain
val container = SharedContainer(
    sqlDriver = NativeSqliteDriver(AppDatabase.Schema, "app.db"),
    httpEngine = Darwin.create()
)
```

**Pros:** Zero framework dependency, full compile-time safety, trivial to understand.
**Cons:** No scoping, no lazy initialization control, becomes unwieldy past ~30 dependencies.

---

## Common Pitfalls

### 1. The Missing `androidContext()` Crash
If you call `initKoin { }` without `androidContext(this)`, any dependency that needs a `Context` (like `AndroidSqliteDriver`) will crash:
```
org.koin.core.error.NoBeanDefFoundException: No definition found for 'android.content.Context'
```

### 2. The `reified` Bridge Problem
Koin's `get<T>()` function uses `reified` type parameters. Reified types are erased in the Objective-C bridge — Swift cannot call `koin.get<HomeViewModel>()`. You must always wrap it:
```kotlin
// This is REQUIRED for Swift consumption
fun getHomeViewModel(): HomeViewModel = koin.get()
```

### 3. The Scope Mismatch
On Android, `single<T>` lives as long as the `Application`. On iOS, `single<T>` lives as long as the Koin container — which lives as long as the process. If the iOS app is killed and restarted, the singleton is recreated. This is usually fine, but be aware that iOS apps are killed more aggressively than Android apps.

### 4. The Circular Dependency Silent Failure
If `RepositoryA` depends on `RepositoryB` and `RepositoryB` depends on `RepositoryA`, Koin will throw `StackOverflowError` at runtime (not at compile time, unless you use the Compiler Plugin):
```
java.lang.StackOverflowError: Circular dependency detected for type 'RepositoryA'
```

---

## Probing Questions

1.  **Dagger Impossibility:** Trace the exact technical reason why Dagger/Hilt cannot compile for Kotlin/Native. Which specific JVM API in the generated code fails, and at what stage of the Kotlin/Native compilation pipeline?
2.  **The `reified` Problem:** Explain why Koin's `inline fun <reified T> get(): T` cannot be called from Swift. What does "reified" mean at the bytecode level, and what happens when the Objective-C bridge encounters it?
3.  **Three-Layer Architecture:** In the module graph above, Layer 1 (Core) has `single<HttpClient> { createHttpClient(engine = get(), ...) }`. How does Koin know that `get<HttpClientEngine>()` should resolve to the Android OkHttp engine on Android and the Darwin engine on iOS? Trace the module loading order.
4.  **Koin Compiler Plugin:** The Compiler Plugin uses KSP to verify the dependency graph at compile time. How does KSP handle `expect fun platformModule(): Module`? Can it verify the `actual` implementations on both platforms in a single compilation pass?
5.  **Manual DI vs Koin:** Your KMP project has 8 feature modules, each with 3-5 dependencies. At what point does manual DI become worse than Koin? What specific maintenance burden does manual DI create that Koin eliminates?

## Further Reading

- [`../../android/data-and-di/hilt-vs-koin-vs-manual-di.md`](../../android/data-and-di/hilt-vs-koin-vs-manual-di.md) — The comprehensive Android DI comparison (Hilt vs Koin vs Manual).
- [`architecture-and-module-boundaries.md`](architecture-and-module-boundaries.md) — The Inversion of Control pattern that DI implements.
- [`persistence.md`](persistence.md) — Why `SqlDriver` requires DI to inject the Android `Context`.
- [`networking-with-ktor.md`](networking-with-ktor.md) — Why `HttpClientEngine` requires DI to inject platform-specific engines.
- [`swift-interop.md`](swift-interop.md) — Why `reified` generics don't bridge to Swift.

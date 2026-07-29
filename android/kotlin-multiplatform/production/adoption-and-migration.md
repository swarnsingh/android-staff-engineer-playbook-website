# KMP Adoption & Migration Strategy

> Moving a large production codebase to Kotlin Multiplatform is both a technical migration and an organizational change. A Staff engineer must create reversible seams, preserve delivery, include Android and iOS owners in API decisions, and measure whether the chosen sharing boundary improves outcomes against the team's own baseline.

---

## Overview

KMP can follow the **Strangler Fig** pattern: introduce a shared implementation behind an existing boundary, move one independently testable slice at a time, and keep the production path reversible until the replacement meets its exit criteria. Some components may still require a planned rewrite; the important property is controlled coexistence and rollback, not pretending every migration is a file move.

---

## 1. When NOT to Use KMP

Before writing a single line of shared code, you must justify KMP to leadership. Not every project benefits from it.

### Evidence That Should Stop or Delay Adoption

| Signal | Why it matters | Response |
|---|---|---|
| The valuable behavior is mostly platform hardware/UI code | The proposed shared boundary may add indirection without removing meaningful duplication | Keep that capability native; pilot a smaller pure-logic boundary if one exists |
| iOS owners cannot review, debug, or release the shared artifact | A cross-platform dependency without cross-platform ownership is an operational risk | Fund training, API design, tooling, and ownership before production adoption |
| No reproducible macOS CI or iOS artifact pipeline | Android-only CI cannot prove the Apple binary or integration | Establish the empty-framework pipeline and rollback path first |
| The pilot has no measurable duplicated problem | Code-reuse percentage alone is not a business or reliability outcome | Define the defect, lead-time, consistency, or maintenance hypothesis before coding |
| A fixed deadline leaves no rollback or validation window | Introducing a new toolchain and runtime boundary raises delivery risk | Ship through the proven path and schedule a bounded post-release pilot |

### Evidence That Makes a Pilot Worthwhile

| Scenario | Testable hypothesis | Pilot evidence |
|---|---|---|
| Complex rules or state machines exist twice | One tested implementation may reduce same-domain divergence | Contract-test parity, production defects, and change lead time before/after |
| Networking, caching, or sync policy is intentionally equivalent | A shared implementation may centralize retries, parsing, and conflict rules | Reliability, observability, offline behavior, and target performance on one vertical slice |
| The team is capacity-constrained | Sharing selected high-change logic may reduce duplicate implementation work | End-to-end delivery time and ownership load, including build/tooling cost |
| Shared UI is under consideration | Compose Multiplatform may fit selected screens without sacrificing required native behavior | Accessibility, design fidelity, startup/render performance, and iteration time on representative devices |

---

## 2. The Incremental Migration Path (Strangler Fig)

### Phase 0: The Foundation

Before touching any business logic, set up the infrastructure:

```text
1. Create the `shared` module with the Kotlin Multiplatform plugin and the current `com.android.kotlin.multiplatform.library` plugin; configure the Android target inside `kotlin { android { ... } }`
2. Add `iosArm64` and `iosSimulatorArm64`; add `iosX64` only when Intel simulator support is an explicit requirement
3. Set up CI with macOS runner (even if it only compiles an empty module)
4. Choose documented local integration (direct or CocoaPods) or remote XCFramework distribution (SwiftPM or CocoaPods) from repository ownership and release requirements
5. Verify the iOS team can import the empty SharedCode framework in Xcode
```

**Success criteria:** The iOS engineer types `import SharedCode` in Xcode and it compiles. The actual framework is empty — it has no useful code. But the pipeline works.

### Phase 1: Data Models & Pure Utilities

Start with the absolute leaf nodes of the dependency graph — code with zero platform dependencies:

```kotlin
// Move from Android's app/src/main/kotlin/model/ to shared/src/commonMain/kotlin/model/

@Serializable
data class User(
    @SerialName("user_id") val id: String,
    @SerialName("full_name") val name: String,
    val email: String,
    val createdAt: Instant
)

@Serializable
data class Product(
    val id: String,
    val name: String,
    @SerialName("price_cents") val priceCents: Long,
    val currency: String
) {
    fun formattedPrice(): String {
        val dollars = priceCents / 100
        val cents = priceCents % 100
        return "$currency $dollars.${cents.toString().padStart(2, '0')}"
    }
}

// Pure utilities
object Validators {
    fun isValidEmail(email: String): Boolean {
        return email.contains("@") && email.contains(".")
    }
    
    fun isValidPassword(password: String): Boolean {
        return password.length >= 8 
            && password.any { it.isUpperCase() }
            && password.any { it.isDigit() }
    }
}
```

**Migration steps:**
1. Move the Kotlin files from the Android module to `shared/commonMain`.
2. Replace `Moshi`/`Gson` annotations with `@Serializable` / `@SerialName`.
3. Replace `java.time.Instant` with `kotlinx.datetime.Instant`.
4. In the Android app, change `import com.example.app.model.User` to `import com.example.shared.model.User`.
5. The iOS team now gets these DTOs for free — no more manually maintaining Swift `Codable` structs.

**Risk:** Usually low, but verify serialized field names/defaults, time and locale semantics, binary API exposure to Swift, and compatibility with stored/network payloads.

### Phase 2: Networking / API Layer

This can be a high-risk phase when it replaces mature Retrofit/OkHttp behavior. Preserve exact URL, encoding, auth, retry, timeout, error, cancellation, and observability semantics through contract tests and staged rollout.

**Before (Android-only Retrofit):**
```kotlin
interface ProductApi {
    @GET("api/v1/products")
    suspend fun getProducts(
        @Query("category") category: String,
        @Query("page") page: Int,
        @Query("limit") limit: Int = 20
    ): ProductListResponse
    
    @POST("api/v1/orders")
    suspend fun submitOrder(
        @Body request: OrderRequest
    ): OrderResponse
}
```

**After (KMP Ktor in `commonMain`):**
```kotlin
class ProductApi(private val client: HttpClient) {
    
    suspend fun getProducts(
        category: String,
        page: Int,
        limit: Int = 20
    ): ProductListResponse {
        return client.get("api/v1/products") {
            parameter("category", category)
            parameter("page", page)
            parameter("limit", limit)
        }.body()
    }
    
    suspend fun submitOrder(request: OrderRequest): OrderResponse {
        return client.post("api/v1/orders") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
}
```

**Migration Checklist:**

| Step | Action | Risk |
|---|---|---|
| 1 | Add Ktor dependencies to `shared/build.gradle.kts` | Low |
| 2 | Create `HttpClient` factory in `commonMain` with `ContentNegotiation` plugin | Low |
| 3 | Create platform-specific engine factories (`OkHttp` in `androidMain`, `Darwin` in `iosMain`) | Low |
| 4 | Rewrite each Retrofit interface as a Ktor class | Medium — must preserve exact query/body semantics |
| 5 | Move custom OkHttp interceptors (auth, logging) to Ktor plugins | Medium |
| 6 | Delete the old Retrofit interface and its Hilt `@Provides` function | Low |
| 7 | Update all callers (Repositories) to use the new Ktor-based API class | Medium |

### Phase 3: Database / Persistence

Choose the persistence migration rather than assuming a rewrite. Room now supports KMP, so an existing Room codebase can first test moving supported entities and asynchronous DAOs to common code. SQLDelight remains an alternative when a SQL-first source of truth and its driver model justify the larger rewrite. The example below illustrates the SQLDelight path, not a universal requirement.

**Before (Room):**
```kotlin
@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val name: String,
    val email: String,
    @ColumnInfo(name = "last_synced") val lastSynced: Long
)

@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE id = :id")
    fun getUserById(id: String): Flow<UserEntity?>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertUser(user: UserEntity)
}
```

**After (SQLDelight in `commonMain`):**
```sql
-- shared/src/commonMain/sqldelight/com/example/db/User.sq

CREATE TABLE UserEntity (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    last_synced INTEGER NOT NULL
);

getUserById:
SELECT * FROM UserEntity WHERE id = ?;

upsertUser:
INSERT OR REPLACE INTO UserEntity(id, name, email, last_synced)
VALUES (?, ?, ?, ?);

getAllUsers:
SELECT * FROM UserEntity ORDER BY name ASC;
```

```kotlin
// Generated by SQLDelight — typesafe Kotlin API
val userFlow: Flow<UserEntity?> = database.userQueries
    .getUserById(userId)
    .asFlow()
    .mapToOneOrNull(Dispatchers.IO)
```

### Phase 4: Domain & ViewModels

Domain logic and ViewModels can be a high-value sharing boundary when both applications intentionally use the same state machine and business rules.

AndroidX `ViewModel` supports KMP. Put the ViewModel and its business logic in `commonMain` and use the lifecycle-owned `viewModelScope`; do not create a second home-grown ViewModel abstraction just to target iOS:

```kotlin
// shared/src/commonMain/kotlin/com/example/checkout/CheckoutViewModel.kt

class CheckoutViewModel(
    private val repository: CheckoutRepository
) : ViewModel() {
    fun submit() = viewModelScope.launch {
        repository.submitOrder()
    }
}
```

Android obtains this class from its normal `ViewModelStoreOwner`. SwiftUI has no built-in AndroidX store owner, so follow the official integration pattern: retain an `IosViewModelStoreOwner` as a `@StateObject`, resolve the shared ViewModel through it, and clear its `ViewModelStore` when that owner is deinitialized.

```swift
struct CheckoutScreen: View {
    @StateObject private var storeOwner = IosViewModelStoreOwner()

    var body: some View {
        let viewModel: CheckoutViewModel = storeOwner.viewModel(
            factory: CheckoutViewModelKt.checkoutViewModelFactory
        )
        CheckoutContent(viewModel: viewModel)
    }
}
```

`onDisappear` is not a reliable ownership boundary: a SwiftUI screen can disappear temporarily and return. Scope the store owner to the navigation/screen lifetime that actually owns the ViewModel, then test deinitialization and cancellation.

---

## 3. Measuring KMP ROI

### Quantitative Metrics

| Metric | How to Measure | Decision use |
|---|---|---|
| **Intended sharing coverage** | Shared production code and tests inside the boundaries selected in the ADR; do not count generated code | Detect whether high-value logic remains duplicated; no universal percentage is healthy |
| **Cross-platform defects** | Same-domain divergence defects per release compared with the pre-KMP baseline | Confirm that sharing reduces inconsistency without hiding platform-specific defects |
| **Feature lead time** | Median and p95 time from implementation start to both-platform release, before and after the pilot | Test the velocity hypothesis rather than promising a percentage |
| **Delivery cost** | CI minutes/cost per merged change, queue time, cache hit rate, and failed-build causes | Expose macOS capacity and build-system regressions |
| **Developer iteration** | Median and p95 clean/incremental Android builds and Xcode edit-build-run loops | Protect both teams' daily feedback loops |

### Qualitative Signals

- **Healthy:** Android and iOS owners review shared APIs, can debug the framework, and choose shared or native implementations from explicit boundaries.
- **Unhealthy:** teams repeatedly bypass the shared module because APIs, build latency, release ownership, or observability are poor.
- **Critical:** production delivery depends on a shared component with no cross-platform owner, rollback path, or reproducible release process.

---

## 4. Using Case Studies Responsibly

Vendor case studies are useful for discovering architectures and questions, not for importing another company's outcome as your forecast. For each candidate example, record:

- The product and feature scope that actually used KMP—not merely the company name.
- Whether it shared logic, UI, or both; the target platforms; and the Kotlin/tooling versions at the time.
- The source date and whether the claim comes from the implementing team, a vendor, or a consultant.
- The measured baseline and outcome, including build/release costs and negative tradeoffs.
- Which constraints transfer to your organization and which do not.

Use the official Kotlin Multiplatform case-study catalog as a starting index, then follow its primary implementation sources. Your pilot ADR should stand on your measurements even if no famous company made the same choice.

---

## 5. Organizational Buy-In Strategies

### Selling to the iOS Team
1. **Preserve the agreed UI boundary.** Keep SwiftUI where native UI is a requirement; evaluate shared UI separately.
2. **Review the exported Swift API.** Use official interop/Swift export and add third-party tooling only when its benefits and lifecycle are validated.
3. **Choose integration from topology.** Remote XCFramework distribution can hide Gradle/JDK from consumers; direct local integration deliberately makes Kotlin builds part of Xcode iteration.
4. **Share ownership.** iOS engineers review common and `iosMain` code, release mechanics, observability, and rollback paths.

### Selling to Product Managers
1. **Parity hypothesis:** Measure whether sharing selected rules reduces same-domain divergence defects; it cannot eliminate platform-specific bugs.
2. **Lead-time hypothesis:** Compare end-to-end both-platform delivery before and after the pilot, including review and release queues.
3. **Capacity hypothesis:** Measure duplicated work avoided and new tooling/ownership cost; do not promise a staffing reduction.

### Selling to Engineering Leadership
1. **Portability option:** A well-bounded common module may lower the cost of an additional supported target, but every target still needs dependency, behavior, performance, and UI validation.
2. **Ownership model:** Define how Kotlin and platform specialists jointly design, review, debug, and release shared code.
3. **Debt trade:** Track duplicated-domain debt removed against new build, interop, dependency, and release-system debt introduced.

---

## Probing Questions

1.  **Strangler Fig:** You have a monolithic Android app with 500 files. Explain the exact sequence of steps to migrate the `UserRepository` (which depends on Retrofit, Room, and SharedPreferences) to a KMP shared module without breaking any existing Android functionality during the migration.
2.  **Organizational Resistance:** The iOS tech lead says "We already have a perfectly good Swift codebase. KMP will make our app worse." How do you respond? What concrete evidence do you present?
3.  **ROI Measurement:** After 6 months, only 25% of production code is shared. Why is that number insufficient to judge the migration, what evidence do you inspect, and when do you expand, hold, or reverse the investment?
4.  **ViewModel Lifecycle:** Android supplies a `ViewModelStoreOwner`. In SwiftUI, what object owns and clears the shared AndroidX ViewModels, and why is calling `onCleared()` from every `onDisappear` incorrect?
5.  **Phase Ordering:** Why can DTOs → networking → persistence be a low-risk order, and when should dependency structure or an existing Room KMP investment lead you to migrate persistence first?

## Answer Key

1. **Strangler Fig:** First freeze the observable `UserRepository` contract with Android tests and telemetry. Create the KMP module and platform seams while the existing Retrofit, Room, and SharedPreferences implementation remains the production delegate. Move portable models and mapping code, then migrate one dependency behind its interface at a time: Ktor or a platform network adapter; Room KMP, SQLDelight, or a database adapter chosen from a migration spike; and a preferences/secure-storage contract with platform implementations where needed. Assemble the shared repository beside the old one, compare safe reads or contract-test both implementations, switch a small cohort with a kill switch, monitor correctness and performance, and retain a rollback path. Avoid unsynchronized dual writes. Delete the Android path only after the new implementation and its iOS consumer meet explicit exit criteria.
2. **Organizational resistance:** Treat the objection as a design constraint, not a sales problem. Agree on the pain being tested, keep SwiftUI and native capabilities, and run a bounded pilot on a high-value but reversible slice. Present measured build/iteration time, Swift API ergonomics, crash and performance data, release/rollback mechanics, debugging workflow, ownership load, and change lead time against the native baseline. Give the iOS lead approval rights over exported APIs and pre-agree stop conditions; adoption is justified by pilot evidence, not company logos or promised reuse.
3. **ROI measurement:** Twenty-five percent can be excellent if it contains duplicated pricing, sync, or validation logic, or wasteful if it contains low-value DTOs while delivery slows. Inspect which boundaries are shared, defects avoided, median/p95 lead time, build latency, CI cost, production reliability, duplicated work, and team sentiment against the pre-migration baseline. Expand only when the pilot improves the intended outcomes; hold and repair tooling/API ownership when value is plausible but friction dominates; reverse when repeated evidence misses the agreed thresholds and a native boundary is cheaper.
4. **ViewModel lifecycle:** Retain an `IosViewModelStoreOwner` for the actual SwiftUI screen/navigation scope, commonly as a `@StateObject`; it owns the `ViewModelStore` and clears it when that owner is deinitialized. Clearing on every `onDisappear` is premature because disappearance can be temporary. Never ask Swift to call a protected lifecycle callback directly: make ownership explicit and verify that deinitialization cancels `viewModelScope`, otherwise work and references can outlive the screen.
5. **Phase ordering:** Portable models are leaf dependencies, so moving them first creates shared types with little runtime risk; networking can then consume those types before persistence adds schemas, files, and migration compatibility. That is a heuristic, not a law. Migrate persistence first when offline/sync logic is the valuable seam, the dependency graph makes the database foundational, or existing Room code can move incrementally with Room KMP. In either order, use dependency analysis, production migration tests, reversible adapters, and one independently releasable slice at a time.

## Further Reading

- [Add KMP to an existing Android project](https://developer.android.com/kotlin/multiplatform/migrate) — Current shared-module setup and prerequisites.
- [Kotlin iOS integration methods](https://kotlinlang.org/docs/multiplatform/multiplatform-ios-integration-overview.html) — Local versus remote integration choices.
- [Migrate an existing app to Room KMP](https://developer.android.com/codelabs/kmp-migrate-room) — An official incremental persistence path.
- [AndroidX ViewModel for KMP](https://developer.android.com/kotlin/multiplatform/viewmodel) — Shared ViewModels and SwiftUI `ViewModelStoreOwner` lifecycle integration.
- [Kotlin Multiplatform case studies](https://kotlinlang.org/lp/multiplatform/case-studies/) — Discovery index; validate transferable claims against each primary implementation source.
- [`architecture-and-module-boundaries.md`](../foundations/architecture-and-module-boundaries.md) — The architectural end-state you are migrating towards.
- [`ios-distribution.md`](../tooling/ios-distribution.md) — How to hide the build system from the iOS team via SPM.
- [`swift-interop.md`](../tooling/swift-interop.md) — How SKIE makes the shared API pleasant for iOS engineers.
- [`libraries-ecosystem.md`](../ecosystem/libraries-ecosystem.md) — The target-support and ownership checks used to choose libraries during each migration phase.
- [`ci-cd-for-kmp.md`](ci-cd-for-kmp.md) — Setting up the macOS CI infrastructure (Phase 0).

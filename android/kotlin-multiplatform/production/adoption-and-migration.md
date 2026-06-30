# KMP Adoption & Migration Strategy

> Moving a large, production Android codebase to Kotlin Multiplatform is not a technical problem — it is an organizational, political, and strategic problem. A Staff engineer must know how to incrementally adopt KMP without halting feature delivery, how to sell the transition to skeptical iOS engineers and product managers, and how to measure whether KMP is actually delivering ROI.

---

## Overview

KMP adoption follows the **Strangler Fig** pattern — you gradually wrap existing native code with shared implementations, letting the shared module grow until the native implementations can be deleted. You never "rewrite" — you migrate function by function, module by module, with the old and new code coexisting throughout.

---

## 1. When NOT to Use KMP

Before writing a single line of shared code, you must justify KMP to leadership. Not every project benefits from it.

### KMP Is Wrong When:

| Scenario | Why KMP Fails | Better Alternative |
|---|---|---|
| App is 90% hardware interaction (AR, BLE, Camera) | Almost no shareable logic; 90% is platform API calls | Native-only development |
| iOS team refuses to learn Kotlin | Political resistance → sabotage → project failure | Invest in relationship-building first |
| No macOS CI infrastructure | Cannot compile iOS artifacts; manual builds are unsustainable | Set up macOS runners first |
| App has <10% logic overlap between platforms | Sharing 10% of code doesn't justify the tooling overhead | Separate codebases |
| Tight deadline (<3 months to ship) | KMP migration introduces risk during a deadline | Ship native, migrate after launch |

### KMP Is Right When:

| Scenario | Why KMP Excels | Concrete Benefit |
|---|---|---|
| Heavy business logic (finance, e-commerce, health) | Complex validation rules, calculations, state machines must be identical on both platforms | Zero divergence bugs |
| Networking + caching layer | Every API call, JSON parsing, and caching strategy is identical | Write once, test once |
| Real-time sync (chat, collaboration) | WebSocket management, conflict resolution, retry logic is identical | Shared reliability |
| Startup with small team (3-5 engineers) | Can't afford 2 separate codebases | 40-60% code reuse |
| B2B / internal tooling | iOS design fidelity less critical | Compose Multiplatform viable |

---

## 2. The Incremental Migration Path (Strangler Fig)

### Phase 0: The Foundation (Week 1-2)

Before touching any business logic, set up the infrastructure:

```text
1. Create the `shared` Gradle module with KMP plugin
2. Add iosArm64, iosSimulatorArm64, iosX64, and androidTarget
3. Set up CI with macOS runner (even if it only compiles an empty module)
4. Choose distribution method (SPM for polyrepo, Direct Xcode for monorepo)
5. Verify the iOS team can import the empty SharedCode framework in Xcode
```

**Success criteria:** The iOS engineer types `import SharedCode` in Xcode and it compiles. The actual framework is empty — it has no useful code. But the pipeline works.

### Phase 1: Data Models & Pure Utilities (Week 3-4)

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

**Risk:** Near zero. These are pure data classes with no side effects.

### Phase 2: Networking / API Layer (Week 5-8)

This is the hardest migration phase because it requires replacing Retrofit with Ktor.

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

### Phase 3: Database / Persistence (Week 9-12)

Replace Room with SQLDelight. This is a significant effort because Room uses annotations + DAO interfaces, while SQLDelight uses raw `.sq` SQL files.

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

### Phase 4: Domain & ViewModels (Week 13-16)

This is the crown jewel — the phase with the highest ROI. Move Use Cases and ViewModels into `commonMain`.

**The ViewModel Lifecycle Problem:**
On Android, ViewModels survive configuration changes because `androidx.lifecycle.ViewModel` is tied to the `ViewModelStore`. On iOS, there is no equivalent — SwiftUI views are value types that can be recreated at any time.

**Solution:** Use a KMP ViewModel base class that manages its own `CoroutineScope`:

```kotlin
// shared/src/commonMain/kotlin/com/example/base/SharedViewModel.kt

open class SharedViewModel {
    // On Android, this scope is bound to the Android ViewModel's lifecycle
    // On iOS, this scope must be cancelled manually when the View disappears
    val viewModelScope: CoroutineScope = CoroutineScope(
        SupervisorJob() + Dispatchers.Main.immediate
    )
    
    open fun onCleared() {
        viewModelScope.cancel()
    }
}
```

On Android, you wrap this in an actual `androidx.lifecycle.ViewModel`:
```kotlin
// androidApp
class AndroidCheckoutViewModel : ViewModel() {
    val shared = CheckoutViewModel()  // The KMP ViewModel
    
    override fun onCleared() {
        shared.onCleared()
        super.onCleared()
    }
}
```

On iOS, the SwiftUI view manages the lifecycle:
```swift
struct CheckoutScreen: View {
    let viewModel = CheckoutViewModel()
    
    var body: some View {
        VStack { /* ... */ }
        .onDisappear {
            viewModel.onCleared()  // Cancel coroutines
        }
    }
}
```

---

## 3. Measuring KMP ROI

### Quantitative Metrics

| Metric | How to Measure | Healthy Target |
|---|---|---|
| **Code Reuse %** | `shared LOC / (shared + android + ios) LOC × 100` | 40-60% |
| **Bug Parity** | # of "works on Android but not iOS" bugs per quarter | 0 (the point of sharing) |
| **Feature Velocity** | Days from spec to both-platform ship | 30-50% faster than pre-KMP |
| **CI Cost** | macOS runner spend per month | <$500/month for small team |
| **iOS Build Time** | Time from CMD+R to running on simulator | <30s with SPM, <90s with Direct |

### Qualitative Signals

- **Healthy:** iOS team voluntarily starts adding `iosMain` code without being asked.
- **Unhealthy:** iOS team writes duplicate Swift implementations instead of using the shared module.
- **Critical:** iOS team forks the repo and removes the KMP dependency entirely.

---

## 4. Industry Case Studies (With Technical Detail)

### Cash App (Block, Inc.)
- **KMP since:** 2018 (one of the earliest production adopters).
- **Sharing:** Business logic, networking, database (SQLDelight was created by Cash App for this purpose).
- **Architecture:** Paradigm A (shared logic, native UI). Uses their own `Workflow` framework for state management.
- **Team structure:** ~50 mobile engineers. Dedicated "Mobile Platform" team owns the shared modules.
- **Key learning:** "Start with the database layer. If your offline sync logic isn't shared, nothing else matters."

### Netflix
- **KMP since:** 2020.
- **Sharing:** Internal studio tools (Prodicle, production management apps). NOT the consumer Netflix app.
- **Architecture:** Paradigm A for internal tools, evaluating Paradigm B (CMP) for admin dashboards.
- **Key learning:** "KMP is perfect for internal tooling where iOS design fidelity is secondary to engineering velocity."

### McDonald's
- **KMP since:** 2022.
- **Sharing:** Ordering flow, payment logic, loyalty programs — the revenue-critical paths.
- **Architecture:** Paradigm A. Massive modular architecture with 20+ KMP modules.
- **Key learning:** "The Strangler Fig pattern works. We migrated one feature at a time over 18 months. No big bang."

### Touchlab
- **Role:** Premier KMP consulting firm. Creators of SKIE, Kermit, KMMBridge.
- **Clients:** McDonald's, Philips, BMW, and others.
- **Key learning:** "The #1 failure mode is ignoring the iOS team. If they hate the API surface, the project dies."

---

## 5. Organizational Buy-In Strategies

### Selling to the iOS Team
1. **Don't force Compose Multiplatform first.** Let them keep writing SwiftUI. KMP's strength is *invisible* shared logic.
2. **Use SKIE.** The API surface must feel like a first-class Swift library.
3. **Use SPM distribution.** They should never install the JDK.
4. **Invite them to code review shared code.** They must feel ownership.

### Selling to Product Managers
1. **Feature parity guarantee:** "We will never have a bug that works on Android but not iOS again."
2. **Velocity improvement:** "New features ship to both platforms simultaneously."
3. **Cost reduction:** "We need 30% fewer engineers to maintain the same feature set."

### Selling to Engineering Leadership
1. **Risk mitigation:** "If we ever need a web version (Wasm), the business logic is already portable."
2. **Talent pool:** "We can hire Kotlin engineers who contribute to both platforms."
3. **Technical debt reduction:** "We eliminate the 'two codebases diverged' problem permanently."

---

## Probing Questions

1.  **Strangler Fig:** You have a monolithic Android app with 500 files. Explain the exact sequence of steps to migrate the `UserRepository` (which depends on Retrofit, Room, and SharedPreferences) to a KMP shared module without breaking any existing Android functionality during the migration.
2.  **Organizational Resistance:** The iOS tech lead says "We already have a perfectly good Swift codebase. KMP will make our app worse." How do you respond? What concrete evidence do you present?
3.  **ROI Measurement:** After 6 months of KMP migration, your code reuse is only 25% (below the 40% target). What are the most likely causes, and how do you course-correct?
4.  **ViewModel Lifecycle:** On Android, `ViewModel.onCleared()` is called by the framework when the owning `Activity`/`Fragment` is permanently destroyed. On iOS, who calls `SharedViewModel.onCleared()`? What happens if they forget?
5.  **Phase Ordering:** Why does the guide recommend migrating DTOs (Phase 1) before networking (Phase 2) before database (Phase 3)? What happens if you try to migrate the database first?

## Further Reading

- [`architecture-and-module-boundaries.md`](../foundations/architecture-and-module-boundaries.md) — The architectural end-state you are migrating towards.
- [`ios-distribution.md`](../tooling/ios-distribution.md) — How to hide the build system from the iOS team via SPM.
- [`swift-interop.md`](../tooling/swift-interop.md) — How SKIE makes the shared API pleasant for iOS engineers.
- [`libraries-ecosystem.md`](../ecosystem/libraries-ecosystem.md) — The exact library swaps required during Phase 2 and Phase 3.
- [`ci-cd-for-kmp.md`](ci-cd-for-kmp.md) — Setting up the macOS CI infrastructure (Phase 0).

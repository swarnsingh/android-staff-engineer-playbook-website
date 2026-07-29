# Persistence in KMP

> Room and Preferences DataStore now support KMP, while SQLDelight and Multiplatform Settings remain established alternatives. The decision is no longer a mandatory Android-library replacement: compare target support, migrations, generated APIs, native access, and operational behavior for the exact versions in use.

---

## Overview

| Domain | KMP candidates | Architectural difference |
|---|---|---|---|
| Relational DB | **Room KMP**, **SQLDelight** | Room generates implementations from annotated Kotlin DAOs; SQLDelight generates Kotlin APIs from SQL |
| Preferences | **Preferences DataStore KMP**, **Multiplatform Settings** | DataStore owns a cross-platform file; Settings can wrap native preference stores |
| Typed schema store | Custom serialization/database | Proto DataStore is not currently supported for KMP; only Preferences DataStore is |

---

## 1. Room KMP or SQLDelight

Room supports KMP from version 2.7.0. Its compiler runs through KSP for every configured target, non-Android DAO operations must be asynchronous, and some Android Room features remain unavailable in common code. For an existing Room codebase, moving supported entities/DAOs to KMP may be lower risk than a database rewrite.

SQLDelight remains a strong alternative when SQL-first schemas, explicit queries, and its target driver model fit the team. Choose using a migration spike and the current [Room KMP limitations](https://developer.android.com/kotlin/multiplatform/room), not the obsolete premise that Room-generated code cannot target Kotlin/Native.

### The Paradigm Inversion

**Room:** You declare entities and DAOs in Kotlin, including SQL in annotated query methods. Room's KSP processor validates that contract and generates DAO/database implementations.

**SQLDelight:** You write `.sq` files containing raw SQL. SQLDelight's Gradle plugin generates typesafe Kotlin interfaces.

The inversion matters architecturally: SQLDelight makes SQL the source of truth, while Room makes annotated Kotlin declarations the source and generates implementations. Both can now target KMP; migration ownership, query complexity, schema tooling, missing platform APIs, and existing investment decide between them.

### Setting Up SQLDelight

**Dependencies (`build.gradle.kts`):**
```kotlin
plugins {
    alias(libs.plugins.sqldelight)
}

sqldelight {
    databases {
        create("AppDatabase") {
            packageName.set("com.example.db")
            // Generate Flow extensions for reactive queries
            generateAsync.set(true)
        }
    }
}

kotlin {
    sourceSets {
        androidMain.dependencies {
            implementation(libs.sqldelight.android.driver)
        }
        iosMain.dependencies {
            implementation(libs.sqldelight.native.driver)
        }
        commonMain.dependencies {
            implementation(libs.sqldelight.coroutines.extensions)
        }
    }
}
```

### Writing the Schema (`.sq` File)

```sql
-- shared/src/commonMain/sqldelight/com/example/db/Product.sq

-- 1. Schema Definition
CREATE TABLE Product (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    category TEXT NOT NULL,
    image_url TEXT,
    created_at INTEGER NOT NULL,     -- epoch millis
    updated_at INTEGER NOT NULL,
    is_active INTEGER AS Boolean NOT NULL DEFAULT 1  -- SQLDelight Boolean adapter
);

CREATE INDEX idx_product_category ON Product(category);
CREATE INDEX idx_product_active ON Product(is_active, category);

-- 2. Named Queries (SQLDelight generates Kotlin functions for each)

getProductById:
SELECT * FROM Product WHERE id = ?;

getProductsByCategory:
SELECT * FROM Product
WHERE category = ? AND is_active = 1
ORDER BY created_at DESC
LIMIT ? OFFSET ?;

searchProducts:
SELECT * FROM Product
WHERE (name LIKE '%' || ? || '%' OR description LIKE '%' || ? || '%')
AND is_active = 1
ORDER BY name ASC;

getProductCount:
SELECT COUNT(*) FROM Product WHERE is_active = 1;

-- 3. Mutations

insertProduct:
INSERT OR REPLACE INTO Product(
    id, name, description, price_cents, currency,
    category, image_url, created_at, updated_at, is_active
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);

deleteProduct:
DELETE FROM Product WHERE id = ?;

deactivateProduct:
UPDATE Product SET is_active = 0, updated_at = ? WHERE id = ?;

deleteAllProducts:
DELETE FROM Product;
```

### Generated Kotlin API

SQLDelight generates a `ProductQueries` class with typesafe functions:

```kotlin
// Simplified representative surface; exact generated declarations vary by version.

interface ProductQueries {
    fun getProductById(id: String): Query<Product>
    fun getProductsByCategory(category: String, limit: Long, offset: Long): Query<Product>
    fun searchProducts(query: String, query_: String): Query<Product>
    fun getProductCount(): Query<Long>
    
    fun insertProduct(
        id: String, name: String, description: String?,
        price_cents: Long, currency: String, category: String,
        image_url: String?, created_at: Long, updated_at: Long,
        is_active: Boolean
    )
    fun deleteProduct(id: String)
    fun deactivateProduct(updated_at: Long, id: String)
    fun deleteAllProducts()
}
```

### Using SQLDelight with Flow (Reactive Queries)

```kotlin
// shared/src/commonMain/kotlin/com/example/data/ProductRepository.kt

class ProductRepository(private val database: AppDatabase) {
    
    // Reactive query — emits a new list every time the Product table changes
    fun observeProducts(category: String): Flow<List<Product>> {
        return database.productQueries
            .getProductsByCategory(category, limit = 50, offset = 0)
            .asFlow()
            .mapToList(Dispatchers.IO)
    }
    
    // One-shot query
    suspend fun getProduct(id: String): Product? {
        return withContext(Dispatchers.IO) {
            database.productQueries
                .getProductById(id)
                .executeAsOneOrNull()
        }
    }
    
    // Transaction — atomic multi-statement operation
    suspend fun syncProducts(products: List<ProductDto>) {
        withContext(Dispatchers.IO) {
            database.transaction {
                database.productQueries.deleteAllProducts()
                products.forEach { dto ->
                    database.productQueries.insertProduct(
                        id = dto.id,
                        name = dto.name,
                        description = dto.description,
                        price_cents = dto.priceCents,
                        currency = dto.currency,
                        category = dto.category,
                        image_url = dto.imageUrl,
                        created_at = dto.createdAt,
                        updated_at = dto.updatedAt,
                        is_active = dto.isActive
                    )
                }
            }
        }
    }
}
```

### The Driver Injection (Platform Boundary)

SQLDelight's `SqlDriver` is the platform-specific component:

```kotlin
// shared/src/androidMain/kotlin/com/example/db/DriverFactory.kt
import app.cash.sqldelight.driver.android.AndroidSqliteDriver

class AndroidDriverFactory(private val context: Context) {
    fun create(): SqlDriver {
        return AndroidSqliteDriver(
            schema = AppDatabase.Schema,
            context = context,
            name = "app.db",
            callback = object : AndroidSqliteDriver.Callback(AppDatabase.Schema) {
                override fun onOpen(db: SupportSQLiteDatabase) {
                    db.execSQL("PRAGMA journal_mode=WAL")  // Write-ahead logging
                    db.execSQL("PRAGMA foreign_keys=ON")
                }
            }
        )
    }
}
```

```kotlin
// shared/src/iosMain/kotlin/com/example/db/DriverFactory.kt
import app.cash.sqldelight.driver.native.NativeSqliteDriver

class IOSDriverFactory {
    fun create(): SqlDriver {
        return NativeSqliteDriver(
            schema = AppDatabase.Schema,
            name = "app.db"
        )
    }
}
```

### Database Migrations

SQLDelight handles migrations via numbered `.sqm` files:

```sql
-- shared/src/commonMain/sqldelight/migrations/1.sqm
-- Migration from version 1 to version 2

ALTER TABLE Product ADD COLUMN rating REAL;
ALTER TABLE Product ADD COLUMN review_count INTEGER NOT NULL DEFAULT 0;
```

```sql
-- shared/src/commonMain/sqldelight/migrations/2.sqm
-- Migration from version 2 to version 3

CREATE TABLE Favorite (
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id),
    FOREIGN KEY (product_id) REFERENCES Product(id) ON DELETE CASCADE
);
```

The driver automatically runs pending migrations on app launch (both Android and iOS).

---

## 2. Multiplatform Settings (The SharedPreferences Replacement)

For simple key-value storage (user preferences, flags, tokens), a relational database is overkill.

### Setup

```kotlin
// commonMain.dependencies
implementation("com.russhwolf:multiplatform-settings:1.3.0")
implementation("com.russhwolf:multiplatform-settings-coroutines:1.3.0")
```

### Usage in `commonMain`

```kotlin
// shared/src/commonMain/kotlin/com/example/prefs/UserPreferences.kt

class UserPreferences(private val settings: Settings) {
    
    // Simple get/set
    var isDarkMode: Boolean
        get() = settings.getBoolean("DARK_MODE", defaultValue = false)
        set(value) = settings.putBoolean("DARK_MODE", value)
    
    var authToken: String?
        get() = settings.getStringOrNull("AUTH_TOKEN")
        set(value) {
            if (value != null) settings.putString("AUTH_TOKEN", value)
            else settings.remove("AUTH_TOKEN")
        }
    
    var onboardingCompleted: Boolean
        get() = settings.getBoolean("ONBOARDING_DONE", defaultValue = false)
        set(value) = settings.putBoolean("ONBOARDING_DONE", value)
    
    var lastSyncTimestamp: Long
        get() = settings.getLong("LAST_SYNC", defaultValue = 0L)
        set(value) = settings.putLong("LAST_SYNC", value)
    
    fun clearAll() {
        settings.clear()
    }
}
```

### Platform-Specific `Settings` Creation

```kotlin
// androidMain
val settings: Settings = SharedPreferencesSettings(
    context.getSharedPreferences("app_prefs", Context.MODE_PRIVATE)
)

// iosMain
val sharedDefaults = requireNotNull(
    NSUserDefaults(suiteName = "group.com.example.shared")
) {
    "App Group UserDefaults is unavailable; verify the suite identifier and entitlement"
}
val settings: Settings = NSUserDefaultsSettings(
    sharedDefaults
)
```

### Observable Settings (Reactive)

```kotlin
// With multiplatform-settings-coroutines
class UserPreferences(private val settings: ObservableSettings) {
    
    // Emits every time the value changes
    val isDarkModeFlow: Flow<Boolean> = settings.getBooleanFlow("DARK_MODE", false)
    
    val authTokenFlow: Flow<String?> = settings.getStringOrNullFlow("AUTH_TOKEN")
}
```

### Behavioral Differences Between Platforms

| Behavior | SharedPreferences (Android) | UserDefaults (Apple targets) |
|---|---|---|
| Wrapper used above | `SharedPreferencesSettings` | `NSUserDefaultsSettings` |
| Sharing boundary | The supplied preferences file within the app sandbox | The supplied defaults domain; an entitled App Group suite can be shared with extensions |
| Observation through this library | Available when the selected implementation implements `ObservableSettings` | `NSUserDefaultsSettings` implements `ObservableSettings` |
| Data contract | Small, nonsensitive preference values—not a database or large-object store | Small, nonsensitive property-list-compatible values—not a database or large-object store |
| Secrets | Use a platform vault backed by Android Keystore | Use Keychain with the required access group |

**Staff Warning:** Do NOT store auth tokens in Multiplatform Settings in production. Use `expect/actual` to access the Android Keystore / iOS Keychain for sensitive data.

---

## 3. Preferences DataStore KMP

DataStore supports KMP from version 1.1.0, but currently only **Preferences DataStore** is supported—not Proto DataStore. Current APIs construct common `DataStore<Preferences>` from a platform-provided `Storage<Preferences>` so each target owns its file location.

```kotlin
// commonMain
fun createPreferencesDataStore(
    storage: Storage<Preferences>
): DataStore<Preferences> = DataStoreFactory.create(storage = storage)

class UserPreferences(private val dataStore: DataStore<Preferences>) {
    // Reading
    val darkModeFlow: Flow<Boolean> = dataStore.data.map { prefs ->
        prefs[booleanPreferencesKey("dark_mode")] ?: false
    }

    // Writing
    suspend fun setDarkMode(enabled: Boolean) {
        dataStore.edit { prefs ->
            prefs[booleanPreferencesKey("dark_mode")] = enabled
        }
    }
}
```

### DataStore KMP vs Multiplatform Settings

| Factor | Multiplatform Settings | DataStore KMP |
|---|---|---|
| Backend on Android | `SharedPreferences` (system API) | Custom protobuf file (Okio) |
| Backend on iOS | `NSUserDefaults` (system API) | Custom protobuf file (Okio) |
| iOS native access | Swift can use the same configured `NSUserDefaults` suite | No supported native Swift Preferences DataStore API; share Kotlin or define another contract |
| Async API | Optional (coroutines extension) | Mandatory (everything is `suspend` / `Flow`) |
| Schema safety | String keys with typed accessors | Typed `PreferencesKey<T>` objects, but still no predefined schema or compile-time key registry |
| Migration support | Library/backend-specific | Validate the migration API on the target and version in use |

If an app extension needs the same preferences, an App Group only makes a container/suite reachable by both processes—it does not make a storage library multi-process safe. Two Preferences DataStore instances in the app and widget can have process-local coordination/caches, concurrent-write races, and stale reads unless the exact target/version provides an explicitly supported multi-process storage mechanism.

Prefer one of these verified contracts:

- A storage/coordinator documented to support multiple iOS processes for the selected library version.
- A single writer that publishes a small, versioned, atomically replaced snapshot for a read-only widget.
- A native interoperable store such as a deliberately configured App Group `NSUserDefaults` suite when its semantics fit the data.

Swift also has no supported native Preferences DataStore reader. Reusing the shared Kotlin API in both processes solves language reuse, not cross-process consistency.

---

## Probing Questions

1.  **SQLDelight vs Room KMP:** Compare their source-of-truth and code-generation models. Now that Room supports KMP, which migration and feature constraints—not a claimed Kotlin/Native impossibility—decide between them?
2.  **Reactive Queries:** When a `Product` row is updated via `insertProduct` (INSERT OR REPLACE), how does SQLDelight's `asFlow()` know to re-emit? What mechanism triggers the Flow emission on iOS vs Android?
3.  **Migration Safety:** Your `.sqm` migration adds a `NOT NULL` column without a `DEFAULT`. Contrast a populated production table with an empty test table. Why must the migration plan not assume identical behavior across the SQLite versions used on Android and iOS?
4.  **NSUserDefaults vs SharedPreferences:** An iOS engineer writes Swift code that reads `UserDefaults(suiteName: "group.com.example.shared")` to get the `DARK_MODE` key. Your Kotlin code uses Multiplatform Settings to write to the same suite. Does the iOS engineer see the Kotlin-written value? Why or why not?
5.  **DataStore and iOS extensions:** An iOS widget needs a preference written by shared Preferences DataStore. Why are an App Group path and shared Kotlin insufficient for cross-process consistency, and which coordination or snapshot contracts are safe alternatives?

## Answer Key

1. **Room KMP vs SQLDelight:** Room keeps Kotlin entities and annotated DAOs as the application-facing contract and generates their implementations; SQLDelight keeps SQL schema/query files as the source of truth and generates Kotlin query APIs. Start with migration evidence: existing Room investment, unsupported Room KMP features, asynchronous DAO requirements on non-Android targets, custom SQL complexity, schema tooling, driver/target coverage, and the cost of validating existing migrations. Room's KMP support removes the old Kotlin/Native blocker; it does not make the two approaches operationally identical.
2. **Reactive queries:** `asFlow()` registers a listener on the generated SQLDelight query and re-executes it when SQLDelight reports that one of its observed tables changed. Generated insert/update/delete functions call the query-notification path for affected tables, and a transaction defers notifications until it completes. This is SQLDelight's generated query/listener mechanism on both Android and iOS—not an Android-only observer versus an iOS notification API. A write made outside the relevant SQLDelight driver path must not be assumed to trigger that Flow; test any external-writer or multi-instance design explicitly.
3. **Migration safety:** A populated table must reject the change because existing rows would receive `NULL` for a column that forbids it. Empty-table handling is version-sensitive: older SQLite releases reject the statement up front, while newer releases can accept it after determining that no row violates the constraint. Android may use a bundled or platform SQLite and Apple targets use the selected native driver/runtime, so do not make correctness depend on that exception. Add a valid default when its domain meaning is honest, or use an explicit nullable/add → backfill → rebuild or constrain sequence, and verify migrations from representative populated database snapshots on every shipped driver/version.
4. **UserDefaults interoperability:** Yes, provided both sides use the same `UserDefaults` suite/domain, key, and compatible value type. `NSUserDefaultsSettings` delegates to the supplied `NSUserDefaults`, so Swift reads the same persistent domain that Kotlin writes. Sharing with an extension additionally requires the same App Group identifier and entitlement; falling back to `standardUserDefaults` would instead select the app's own domain.
5. **DataStore and extensions:** An App Group grants both processes access to a location, and shared Kotlin gives them the same API, but neither supplies cross-process locking, cache invalidation, or write serialization. Safe designs require a coordinator documented for multiple processes on the exact target/version, one designated writer publishing an atomically replaced and versioned snapshot for readers, or an intentionally interoperable native store such as an App Group `UserDefaults` suite when its semantics fit. Validate crash recovery and simultaneous access with separate-process tests.

## Further Reading

- [Room for Kotlin Multiplatform](https://developer.android.com/kotlin/multiplatform/room) — Current setup, target support, DAO constraints, and unsupported APIs.
- [Preferences DataStore for KMP](https://developer.android.com/kotlin/multiplatform/datastore) — Current `Storage<Preferences>` construction and Preferences-only KMP support.
- [SQLDelight coroutines](https://sqldelight.github.io/sqldelight/2.3.2/android_sqlite/coroutines/) and [migration verification](https://sqldelight.github.io/sqldelight/2.3.2/android_sqlite/migrations/) — Flow behavior and schema-snapshot checks.
- [SQLite `ALTER TABLE`](https://www.sqlite.org/lang_altertable.html) — Authoritative restrictions for adding `NOT NULL` columns.
- [Apple `UserDefaults.init(suiteName:)`](https://developer.apple.com/documentation/foundation/userdefaults/init%28suitename%3A%29) and [App Groups](https://developer.apple.com/documentation/xcode/configuring-app-groups) — Shared defaults domains, entitlements, and containers.
- [Multiplatform Settings 1.3.0](https://github.com/russhwolf/multiplatform-settings/tree/v1.3.0) — Supported implementations, listeners, and coroutine adapters.
- [`libraries-ecosystem.md`](libraries-ecosystem.md) — How to evaluate target variants, support levels, and behavioral tradeoffs without a stale replacement table.
- [`dependency-injection.md`](dependency-injection.md) — How to inject the platform-specific `SqlDriver` via Koin.
- [`build-system-and-source-sets.md`](../tooling/build-system-and-source-sets.md) — Configuring the SQLDelight Gradle plugin in the KMP module.
- [`adoption-and-migration.md`](../production/adoption-and-migration.md) — How Phase 3 evaluates a Room KMP move versus a SQLDelight rewrite.

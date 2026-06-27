# ADR 004: Room vs DataStore for Persistence

## Context
The application relies heavily on local persistence to achieve its Offline-First architecture. Historically, the project used **SharedPreferences** for simple key-value pairs (like user settings or auth tokens) and **Room (SQLite)** for complex relational data (like lists of posts, user profiles, and sync queues).

Two major issues have forced a re-evaluation of the storage layer:
1.  **SharedPreferences Blocking:** `SharedPreferences` is notorious for ANRs (Application Not Responding). While `apply()` is asynchronous, Android's Activity lifecycle will aggressively wait for pending `apply()` disk writes to finish before pausing or destroying an Activity, leading to UI freezes on older devices.
2.  **Type Safety:** `SharedPreferences` is untyped, leading to frequent `ClassCastException`s when a developer accidentally reads a Boolean as an Integer.
3.  **Abuse of Key-Value Storage:** Developers are currently serializing massive, complex JSON objects (e.g., the entire user profile configuration) and storing them as a single String in `SharedPreferences` to avoid the overhead of creating Room entities, leading to massive memory bloat when the file is parsed.

The engineering team needs to standardize the boundaries between Android's modern persistence libraries: Room, Preferences DataStore, and Proto DataStore.

## Alternatives Considered

### 1. Room for Everything
-   **Pros:** Single source of truth. Robust migrations. Complex relational queries.
-   **Cons:** Overkill for simple boolean flags (e.g., `is_dark_mode_enabled`). Writing SQL queries and DAOs for 10 individual user settings is tedious boilerplate.

### 2. Preferences DataStore
-   **Pros:** Google's official replacement for `SharedPreferences`. Fully asynchronous via Kotlin Flow and Coroutines. Mathematically eliminates the ANR problems associated with `SharedPreferences`.
-   **Cons:** Still lacks strong type safety (relies on defining `Preferences.Key<String>`). Not designed for complex objects, only basic primitives.

### 3. Proto DataStore
-   **Pros:** Uses Protocol Buffers to define the schema. Guarantees strong type safety. Excellent for storing medium-complexity objects (like a user configuration object) without the overhead of relational SQL.
-   **Cons:** Requires learning Protobuf syntax. Generates Java/Kotlin classes which add minor build time overhead.

## Decision
We will enforce a strict, tiered persistence strategy:

1.  **Deprecation of SharedPreferences:** `SharedPreferences` is formally banned in the codebase. All existing usages must be migrated to DataStore using the `SharedPreferencesMigration` utility.
2.  **Proto DataStore for Configuration & State:** All global app configurations, user settings, and medium-complexity monolithic state objects (e.g., `UserPreferences`, `FeatureFlagConfig`) will be stored using **Proto DataStore**. The type safety and ability to store nested objects without JSON serialization make it vastly superior to Preferences DataStore.
3.  **Room for Relational Data & Caching:** All lists, offline queues, and highly structured domain models (e.g., `CachedPosts`, `PendingUploads`) will remain in **Room**. Room must be used when querying, sorting, or filtering data is required.
4.  **No JSON in DataStore:** Serializing complex JSON objects into a String to store in Preferences DataStore is banned. If the object is complex, it must be modeled as a Protobuf schema in Proto DataStore, or normalized into a Room Database.

## Consequences
-   **Positive:** Complete elimination of `SharedPreferences`-induced ANRs on the Main Thread.
-   **Positive:** `ClassCastException`s when reading settings are eliminated via Proto DataStore's strong typing.
-   **Negative:** Developers must learn Protocol Buffer syntax (`.proto` files) for simple settings.
-   **Negative:** Migrating existing complex JSON strings out of `SharedPreferences` into normalized Room tables or Protobufs will require significant one-time engineering effort and complex data migrations.

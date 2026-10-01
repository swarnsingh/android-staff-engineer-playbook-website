# Room vs Proto DataStore: Local Data Strategies

> Pick wrong and you'll either run SQLite to cache one boolean (overkill) or write a 5 MB DataStore file every time the user toggles a switch (battery murder). Staff-level decisions here come down to: *Is the data relational or queryable?* If yes → Room. *Is it a single coherent settings document?* If yes → Proto DataStore. The choice cascades into encryption strategy, migration risk, threading model, and backup behavior.

---

## TL;DR Decision Table

| Data shape | Tool | Why |
|---|---|---|
| Single config / settings document | Proto DataStore | Type-safe schema, atomic writes, suspend API |
| Key-value flags, < 10 keys, no schema needed | Preferences DataStore (or Proto) | Suspend, async, no SP synchronicity issues |
| List of 10+ items with queries / filters | Room | SQL indexes; partial updates; joins |
| Single-source-of-truth cache (offline-first) | Room | Reactive `Flow` from queries; partial updates |
| Encrypted secrets (token, refresh) | Keystore-backed ciphertext envelope | Small payload; versioned migration and key-invalidation handling |
| Binary blobs (photos, audio) | File system + path in Room | Don't put blobs in either; reference by path |
| Logs / analytics events queue | Room with TTL | Append-only, query for unsent, batch upload |

Use this table during code review.

---

## The Lineage and Why DataStore Exists

- **SharedPreferences** (since API 1) — XML file, synchronous reads (`getString` blocks the main thread), no type safety, no schema, `apply()` is async but `commit()` is blocking.
- **Preferences DataStore** (2020) — `SharedPreferences`'s replacement: key-value, **suspending**, transactional.
- **Proto DataStore** (2020) — typed schema via Protobuf, atomic, the only Google-blessed option for "structured settings."
- **Room** (2017) — official ORM on top of SQLite. Reactive via Flow.

Why three (and the fourth remains supported)? Each addresses a different access pattern. Android [recommends DataStore instead of SharedPreferences](https://developer.android.com/training/data-storage/shared-preferences) for new small-data storage, but `SharedPreferences` has not been formally deprecated.

---

## Room — When You Need a Real Database

Use Room when:

- You have **many items** that need querying / sorting / filtering.
- You need **partial updates** (change one column without rewriting the row).
- You want to observe a query reactively (`Flow<List<T>>`).
- You're caching server data with relationships (users → orders → items).

### Skeleton

```kotlin
@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val username: String,
    val isPremium: Boolean,
    @ColumnInfo(name = "last_login") val lastLogin: Long,
)

@Dao
interface UserDao {
    // Reactive query: emits a new list whenever the table changes
    @Query("SELECT * FROM users WHERE isPremium = 1 ORDER BY last_login DESC")
    fun observePremiumUsers(): Flow<List<UserEntity>>

    // Partial update: only touches one column, doesn't reload the row
    @Query("UPDATE users SET last_login = :ts WHERE id = :userId")
    suspend fun setLastLogin(userId: String, ts: Long)

    @Upsert
    suspend fun upsert(users: List<UserEntity>)

    @Delete
    suspend fun delete(user: UserEntity)
}

@Database(entities = [UserEntity::class], version = 3)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
}
```

### Schema Migrations

Each schema change increments `version` and provides a `Migration`:

```kotlin
val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE users ADD COLUMN last_login INTEGER NOT NULL DEFAULT 0")
    }
}

Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
    .addMigrations(MIGRATION_2_3)
    .fallbackToDestructiveMigration(false)    // never silently drop user data
    .build()
```

Schema migrations are tested via the `RoomMigrationTestHelper`:

```kotlin
@Rule @JvmField
val helper = MigrationTestHelper(
    InstrumentationRegistry.getInstrumentation(),
    AppDatabase::class.java,
)

@Test fun migrate2to3() {
    helper.createDatabase("test.db", 2).apply {
        execSQL("INSERT INTO users (id, username, isPremium) VALUES ('1', 'alice', 1)")
        close()
    }
    helper.runMigrationsAndValidate("test.db", 3, true, MIGRATION_2_3)
}
```

Migrations are the most common source of "app crashes on update" bugs. **Always test them.** `fallbackToDestructiveMigration(true)` deletes user data — never enable for a shipping app without explicit consent.

### Room Auto-Migrations (since 2.4)

For simple schema diffs:

```kotlin
@Database(
    entities = [UserEntity::class],
    version = 3,
    autoMigrations = [
        AutoMigration(from = 2, to = 3),
    ],
)
abstract class AppDatabase : RoomDatabase()
```

Codegen handles SQL. Works for adding columns, tables; not for renames (use a `@RenameColumn` spec).

---

## Proto DataStore — When the Whole Thing is One Document

Use Proto DataStore when:

- The data is a **single coherent settings document** (~tens of fields, KB not MB).
- You want **type-safe schema** with controlled evolution.
- You read it **rarely** but the reads must be **suspending** (no main-thread block).
- The whole thing is **read or written atomically** — no partial updates.

### Schema

```protobuf
// app/src/main/proto/user_prefs.proto
syntax = "proto3";

option java_package = "com.example.app.settings";
option java_multiple_files = true;

message UserPrefs {
  string user_id = 1;
  ThemeMode theme = 2;
  bool push_notifications_enabled = 3;
  int64 last_sync_timestamp = 4;
}

enum ThemeMode {
  THEME_MODE_UNSPECIFIED = 0;
  THEME_MODE_LIGHT = 1;
  THEME_MODE_DARK = 2;
  THEME_MODE_SYSTEM = 3;
}
```

### Wiring

```kotlin
object UserPrefsSerializer : Serializer<UserPrefs> {
    override val defaultValue: UserPrefs = UserPrefs.getDefaultInstance()

    override suspend fun readFrom(input: InputStream): UserPrefs =
        try {
            UserPrefs.parseFrom(input)
        } catch (e: InvalidProtocolBufferException) {
            throw CorruptionException("Cannot read UserPrefs", e)
        }

    override suspend fun writeTo(t: UserPrefs, output: OutputStream) = t.writeTo(output)
}

val Context.userPrefsStore: DataStore<UserPrefs> by dataStore(
    fileName = "user_prefs.pb",
    serializer = UserPrefsSerializer,
)

class UserPrefsRepository @Inject constructor(
    @ApplicationContext context: Context,
) {
    private val store = context.userPrefsStore

    val theme: Flow<ThemeMode> = store.data
        .catch { e ->
            if (e is IOException) emit(UserPrefs.getDefaultInstance()) else throw e
        }
        .map { it.theme }

    suspend fun setTheme(mode: ThemeMode) {
        store.updateData { current ->
            current.toBuilder().setTheme(mode).build()
        }
    }
}
```

### Protobuf field evolution

Proto's schema rules (vs Room's SQL migrations):

- **Add a field** — safe; old readers ignore unknown fields, new readers see default.
- **Remove a field** — safe if no one is reading it; mark it `reserved`.
- **Change a field's type** — unsafe; reserve the number, add a new field.
- **Renumber a field** — unsafe; protobuf identifies fields by number, not name.

If you stick to "add new fields, never reuse numbers," you avoid the migration cliffs Room forces you onto.

### Why **Proto** DataStore over **Preferences** DataStore

`PreferencesDataStore` looks like `SharedPreferences` (string keys, dynamic types). It's untyped — `prefs[KEY] = 5` works but `prefs[KEY].toString()` returns whatever you stored. Easy to corrupt.

Proto DataStore enforces a schema. The IDE gives autocomplete; the compiler catches typos; refactoring renames work. At staff level, prefer **Proto** for anything that isn't a one-off boolean.

---

## The Update-Pattern Difference (Why It Matters)

### Room — surgical updates

```kotlin
@Query("UPDATE users SET last_login = :ts WHERE id = :userId")
suspend fun setLastLogin(userId: String, ts: Long)
```

SQL `UPDATE … WHERE id = …` modifies **one row's one column** on disk. Even with 100k rows, the cost is a small index seek + a single B-tree leaf update.

### DataStore — whole-file rewrite

```kotlin
store.updateData { it.toBuilder().setLastLogin(now).build() }
```

DataStore writes are *transactional*: read the entire file, build a new proto in memory, write the whole thing back to a temp file, rename atomically. **The entire document is rewritten on every change.**

For a 5 KB prefs doc, this is fine — ~1ms. For a 5 MB user profile cache, this is murder — every change pumps 5 MB through the disk.

**Rule:** keep your Proto DataStore under ~20 KB. If you find yourself adding a `repeated User` field, you've outgrown DataStore — move to Room.

---

## Reactive Reads — Both Are Flow-First

Both libraries integrate with coroutines + Flow.

```kotlin
// Room
@Query("SELECT * FROM users")
fun observeAll(): Flow<List<UserEntity>>

// DataStore
val prefs: Flow<UserPrefs> = store.data
```

Room's `Flow` emits on any change to tables referenced by the query. DataStore's `Flow` emits on any `updateData` call. Both honor structured concurrency — cancelled scopes detach observers cleanly.

In a Composable:

```kotlin
@Composable
fun ThemeToggle(prefs: UserPrefsRepository) {
    val theme by prefs.theme.collectAsStateWithLifecycle(initialValue = ThemeMode.THEME_MODE_SYSTEM)
    Switch(checked = theme == ThemeMode.THEME_MODE_DARK, onCheckedChange = { /* ... */ })
}
```

---

## Encryption

### Room

No built-in encryption. Two paths:

1. **SQLCipher** (open-source, AES-256 SQLite extension):
   ```kotlin
   val factory = SupportFactory(SQLiteDatabase.getBytes("user-secret".toCharArray()))
   Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
       .openHelperFactory(factory)
       .build()
   ```
   Encrypts the whole DB file. ~10% perf overhead. Suitable for PII / health / financial data.

2. **Field-level encryption** — encrypt sensitive columns yourself via Tink + AndroidKeyStore; store ciphertext.

### DataStore

No built-in encryption either, but easier to layer:

- For **Proto DataStore**, wrap the `Serializer` to encrypt/decrypt the bytes via Tink (`AndroidKeysetManager`).
- For **secrets** (tokens, keys), keep the storage decision separate from key custody. AndroidX Security Crypto deprecated `EncryptedSharedPreferences`; new code should use direct Android Keystore keys and store a versioned ciphertext envelope in an app-private store. See [Secure Storage on Android](../../security/secure-storage-on-android.md). Room vs DataStore does not decide this security boundary.

---

## Single-Source-of-Truth Pattern (Room + Network)

This is the canonical offline-first pattern:

```kotlin
class FeedRepository @Inject constructor(
    private val api: FeedApi,
    private val dao: PostDao,
) {
    // UI observes Room. Always returns the latest cached data + reacts to changes.
    fun observeFeed(): Flow<List<Post>> = dao.observeAll().map { it.toDomain() }

    // Background refresh inserts into Room; the Flow above auto-emits.
    suspend fun refresh() {
        val remote = api.getFeed()                  // network
        dao.upsert(remote.toEntities())             // single source of truth
    }
}
```

The UI never touches the network directly. The repository pulls from the network, writes to Room, and the UI gets the new state via the Flow. Failure modes:

- Network down → UI still works (cache).
- Cache stale → refresh runs in background → Flow updates → UI rerenders.
- Process death → cache survives → UI loads instantly on restart.

See [`../patterns/repository.md`](../../patterns/repository.md) for the broader pattern.

---

## Backup Behavior

Default Android Auto Backup includes both Room DBs and DataStore files under the app's `files/` directory. Whether you want this:

| Data | Backup? | Why |
|---|---|---|
| User settings (theme, locale) | Yes | User expects to keep after reinstall |
| Auth tokens | **No** | Different device = different security context |
| Cache from server | No | Cheap to re-fetch; bloats backup |
| Encrypted DB (SQLCipher) | Sometimes | Useful if user kept the key |
| Onboarding completion flag | Yes | Don't re-onboard the user |

Control via `android:fullBackupContent` in `AndroidManifest.xml` with an XML rules file. Default behavior backs up *everything*; the right move is to exclude caches and tokens.

---

## Testing

### Room — in-memory database

```kotlin
@Test
fun upsert_persists() = runTest {
    val db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
        .allowMainThreadQueries()
        .build()
    val dao = db.userDao()

    dao.upsert(listOf(UserEntity("1", "alice", false, 0)))
    val users = dao.observePremiumUsers().first()
    assertEquals(0, users.size)
}
```

Tests run against a real SQLite engine, just in RAM. Catches SQL syntax errors and constraint bugs.

### DataStore — test directory

```kotlin
@Test
fun setTheme_emits() = runTest {
    val tempFile = tempFolder.newFile("test.pb")
    val store = DataStoreFactory.create(
        serializer = UserPrefsSerializer,
        scope = TestScope(),
        produceFile = { tempFile },
    )
    store.updateData { it.toBuilder().setTheme(ThemeMode.THEME_MODE_DARK).build() }
    val prefs = store.data.first()
    assertEquals(ThemeMode.THEME_MODE_DARK, prefs.theme)
}
```

---

## Migration from SharedPreferences

DataStore exposes a built-in migrator:

```kotlin
val Context.userPrefsStore: DataStore<UserPrefs> by dataStore(
    fileName = "user_prefs.pb",
    serializer = UserPrefsSerializer,
    produceMigrations = { context ->
        listOf(
            SharedPreferencesMigration(context, "legacy_prefs") { sp, proto ->
                proto.toBuilder()
                    .setTheme(ThemeMode.valueOf(sp.getString("theme") ?: "THEME_MODE_SYSTEM"))
                    .setPushNotificationsEnabled(sp.getBoolean("notifications") ?: true)
                    .build()
            },
        )
    },
)
```

On first read, the migrator runs once, copies values from `legacy_prefs.xml` into the proto, marks the migration complete, and deletes the old XML file. Idempotent and one-shot.

For Room: there's no automatic migrator from SharedPreferences. Read the prefs once in `Application.onCreate`, write into Room, then delete the SP file.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| App freezes on launch reading user prefs | `SharedPreferences.getString()` on main thread | Migrate to DataStore (suspend) |
| Battery drain after settings screen | DataStore prefs file is too large; updates rewrite all | Split into multiple DataStore files, or move bulk data to Room |
| App crashes on update with "no such column" | Room migration missing | Add a `Migration` + test with `MigrationTestHelper` |
| Auth token leaks via Auto Backup | Backup not excluded | `android:fullBackupContent="@xml/backup_rules"` + exclude |
| Room queries block UI | Used non-suspend DAO from Main | Mark DAO methods `suspend` or return `Flow` |
| Crash: `CorruptionException` reading DataStore | File partially written (process killed mid-update) | Set `corruptionHandler = ReplaceFileCorruptionHandler { default }` |
| DataStore writes happen in random order | Multiple writers racing | DataStore is single-writer; serialize via single repository |
| Two DataStores defined for the same file | `by dataStore(filename = ...)` declared in two modules | Make one canonical; delete duplicates |
| Room migration test passes, prod crashes | Test DB had different schema | Always start migration tests from the previous shipped version's schema |
| Encrypted DB loses data after Play Store key rotation | Key tied to AndroidKeyStore alias that rotated | Persist the key in a stable way; or use SQLCipher with a derived passphrase |
| `Flow` from Room not emitting | Forgot `@Transaction` for multi-table query, or query has no observable trigger | Use `@Query` with `Flow<T>` return type; ensure trigger tables are correct |
| Proto compile errors mid-release | Renamed a field number | Reserve the old number; add new field with new number |
| Slow first-time Room access | DB constructed on main thread | `Room.databaseBuilder(...).build()` lazily; or use `viewModelScope` |
| Coroutine deadlock writing to DataStore from inside `updateData` | Recursive call | Don't call `updateData` from inside another `updateData` |

---

## Common Pitfalls

- **Treating Preferences DataStore as a typed store.** It isn't. Use Proto.
- **Storing big blobs in either.** Photos, audio, attachments: write to the filesystem with a path stored in Room.
- **Reading SharedPreferences on main thread "because it's already loaded."** First read still does I/O. Move off it.
- **Catching `IOException` in Room and swallowing.** Room throws `SQLiteConstraintException`, `SQLiteFullException`, and friends — handle them specifically; don't shrug.
- **Auto-backup of cached data.** Bloats user backups and re-fetches anyway. Exclude.
- **`allowMainThreadQueries()` in production.** Allowed for tests only.
- **No coroutine scope around DataStore writes.** Writes must be from a coroutine — UI buttons that call `runBlocking { store.updateData(...) }` will block the main thread.
- **Multiple DataStore instances for the same file.** Causes silent races. Make it a singleton via DI.
- **Forgetting `@Index` on foreign-key columns.** Room won't crash but queries become slow on large tables.

---

## Probing Questions

1. Walk through what happens on disk when you call `store.updateData { it.toBuilder().setX(...).build() }`. Why is this the wrong tool for a 5 MB file?
2. A Room migration adds a column. Walk through writing it, testing it with `MigrationTestHelper`, and what goes wrong if you don't test.
3. Why is Proto DataStore preferred over Preferences DataStore at staff level?
4. Compare partial updates: SQL `UPDATE … WHERE` vs DataStore `updateData`. Which is faster, and why?
5. An app encrypts its Room database with SQLCipher. The user reinstalls. The DB file persists in Auto Backup. What's the security implication?
6. Your DataStore has grown to 8 MB because someone added `repeated User users` to the proto. What's the migration story?
7. Walk through the Single Source of Truth pattern: how Room + Flow + a network call combine to make an offline-first feature.
8. Why does Room emit a `Flow<List<T>>` automatically on table changes, and what's the rule for which tables a query "depends on"?
9. SharedPreferences calls block the main thread on first read. Why? Walk through the file I/O.
10. Compare schema evolution: Room migrations vs Protobuf field number rules. Which is safer for SDK consumers?
11. You see crashes from `CorruptionException` on DataStore. Walk through likely causes and fixes.
12. A team wants to store user analytics events locally before upload. Room or DataStore? Why?

## Answer Key

1. **Walk through what happens on disk when you call `store.updateData { it.toBuilder().setX(...).build() }`. Why is this the wrong tool for a 5 MB file?**
   DataStore reads the entire file into memory, creates a new object with the mutation, writes the complete 5 MB object to a temporary file, and performs an atomic rename. This forces 5 MB of disk write for every tiny mutation, causing severe I/O overhead and battery drain.
2. **A Room migration adds a column. Walk through writing it, testing it with `MigrationTestHelper`, and what goes wrong if you don't test.**
   Write an `object : Migration(x, y)` executing `ALTER TABLE ADD COLUMN`. Test it by having `MigrationTestHelper` create the DB at version X, insert data, and then run `runMigrationsAndValidate` for version Y. Failing to test can lead to SQL syntax errors crashing the app on startup, permanently locking users out of their data.
3. **Why is Proto DataStore preferred over Preferences DataStore at staff level?**
   Proto DataStore enforces a strict, type-safe schema with explicit defaults and compile-time checks. Preferences DataStore is string-key based and untyped, risking `ClassCastException`s and typos exactly like `SharedPreferences`.
4. **Compare partial updates: SQL `UPDATE … WHERE` vs DataStore `updateData`. Which is faster, and why?**
   SQL `UPDATE` is drastically faster because SQLite performs a targeted index seek and modifies only the specific leaf nodes of the B-tree on disk. DataStore must rewrite the entire file transactionally.
5. **An app encrypts its Room database with SQLCipher. The user reinstalls. The DB file persists in Auto Backup. What's the security implication?**
   If the SQLCipher key was stored in the Android Keystore (which is wiped on uninstall), the restored DB file is permanently unreadable. If the key was derived from a user password, they can unlock it. If the key was hardcoded or backed up, the encryption is compromised.
6. **Your DataStore has grown to 8 MB because someone added `repeated User users` to the proto. What's the migration story?**
   Create a new Room database for the `User` list. In app initialization, read the 8 MB DataStore, insert all users into Room, then write a new Proto DataStore omitting the repeated field (having marked it `reserved`).
7. **Walk through the Single Source of Truth pattern: how Room + Flow + a network call combine to make an offline-first feature.**
   The UI exclusively observes a `Flow` emitted by a Room `@Query`. To refresh data, the repository makes a network call and saves the result to Room. The database mutation automatically triggers the `Flow` to emit the new data to the UI, guaranteeing the UI always reflects the local cache.
8. **Why does Room emit a `Flow<List<T>>` automatically on table changes, and what's the rule for which tables a query "depends on"?**
   Room registers an `InvalidationTracker` on the SQLite database. During compilation, Room analyzes the `SELECT` query to identify all referenced tables. If any of those specific tables are mutated, the tracker fires and re-evaluates the query for the Flow.
9. **SharedPreferences calls block the main thread on first read. Why? Walk through the file I/O.**
   When `getSharedPreferences()` is first called, the OS spawns a background thread to read and parse the entire XML file into a memory map. If you call `getBoolean()` before that finishes, the calling thread explicitly blocks (waits on a latch) until the file I/O completes.
10. **Compare schema evolution: Room migrations vs Protobuf field number rules. Which is safer for SDK consumers?**
    Protobuf is safer. It ignores unknown fields and gracefully handles missing ones via defaults using stable field numbers. Room requires explicit SQL migrations; if versions mismatch between what the SDK expects and what is on disk, Room throws an exception and fails to open.
11. **You see crashes from `CorruptionException` on DataStore. Walk through likely causes and fixes.**
    It usually happens when the device powers off or the process is brutally killed during a write. Fix it by configuring a `ReplaceFileCorruptionHandler` in the DataStore factory to provide a safe fallback default rather than crashing the app.
12. **A team wants to store user analytics events locally before upload. Room or DataStore? Why?**
    Room. Analytics are append-only lists that require querying for unsent events, batching, and deleting by ID after upload. DataStore rewriting the entire file on every event append would be catastrophic for performance.

---

## Further Reading

- [`room.md`](room.md) — Room canonical (deeper).
- [`datastore.md`](datastore.md) — DataStore canonical (deeper).
- [`paging.md`](paging.md) — Paging 3 over Room for huge lists.
- [`hilt-vs-koin-vs-manual-di.md`](hilt-vs-koin-vs-manual-di.md) — injecting `DataStore` / DAO singletons.
- [`dependency-injection.md`](dependency-injection.md) — repository wiring.
- [`../networking-and-security/security-and-keystore.md`](../networking-and-security/security-and-keystore.md) — encrypted storage primitives.
- [`../../patterns/repository.md`](../../patterns/repository.md) — single source of truth pattern.
- [`../../backend-for-mobile/graphql-vs-rest.md`](../../backend-for-mobile/graphql-vs-rest.md) — syncing local Room with server.
- [`../../kotlin/coroutines-and-flow/coroutines.md`](../../kotlin/coroutines-and-flow/coroutines.md) — suspend Flow integration.
- [Android Developers — Save data with DataStore](https://developer.android.com/topic/libraries/architecture/datastore) — official guide.
- [Android Developers — Room overview](https://developer.android.com/training/data-storage/room) — official guide.
- [SQLCipher for Android](https://www.zetetic.net/sqlcipher/sqlcipher-for-android/) — encryption deep dive.
- [Florina Muntenescu — DataStore patterns](https://medium.com/androiddevelopers/) — Google DevRel deep dives.

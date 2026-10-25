# Android Phase 2: possible errors in the original chapters

Found while writing the teaching layer for Android Phase 2 (data ownership and dependency boundaries: the ten chapters listed in Phase 2 of `android.md`). These are **findings for the owner's review**, not approved corrections. The original Markdown is unchanged and nothing has been added to `content/corrections-*.json`.

On the website, each finding is shown as an **Under review** note before the section that contains it. The teaching layer avoids restating these claims.

**Verification method:** Android framework code was not compiled; it needs the Android SDK and a project. Each finding was checked against official documentation, API references or release notes, cited per row. Checked on 2026-10-25.

| ID | Chapter, section | Original says | Problem | Evidence |
|---|---|---|---|---|
| R1 | Repository Source of Truth, Offline-First Read Pattern | `dao.withTransaction { … }` called on a DAO | Room's `withTransaction` is an extension on `RoomDatabase`; the chapter's own write-path example uses `database.withTransaction` | androidx.room `RoomDatabase.withTransaction` (room-ktx) |
| R2 | Room, Failure Modes (N+1) and Answer Key 7 | `@Relation` runs one query per parent (N+1); multimaps "solve the N+1 problem" | Android documents that a `@Relation` method "requires Room to run two queries": one for parents, one for all related rows | [One-to-many relationships](https://developer.android.com/training/data-storage/room/relationships/one-to-many) |
| R3 | Room, Staff Engineer Thinking point 2 and Answer Key 6 | Projecting fewer columns stops a `Flow` re-emitting when an unselected column changes | Room invalidates observable queries per table, as the chapter's Internal Mechanics section says; projection reduces mapping cost, not invalidation | Room `InvalidationTracker` (table-level observers); same chapter, Internal Mechanics |
| RD1 | Room vs DataStore, Room — When You Need a Real Database | `.fallbackToDestructiveMigration(false)` with the comment "never silently drop user data" | The overload "Allows Room to destructively recreate database tables"; its argument only chooses whether all tables or only Room-managed tables are dropped | [`RoomDatabase.Builder` reference](https://developer.android.com/reference/kotlin/androidx/room/RoomDatabase.Builder) |
| DI1 | Dependency Injection, Failure Modes (over-scoping) and Answer Key 6 | `@Singleton` classes are instantiated "from the moment the app boots" | Dagger creates a scoped binding on first request and then holds it for the component's lifetime | Dagger scoping semantics (`DoubleCheck` lazy provider) |
| C1 | Hilt Components: table "Default for", `ActivityRetainedComponent` drill-down, a Failure Modes row, Answer Key 5 | `@HiltViewModel` ViewModels are scoped to / live in `ActivityRetainedComponent` | Hilt lists `ViewModelComponent` as the injector for `ViewModel`, a child of `ActivityRetainedComponent` (as the chapter's own hierarchy diagram shows) | [Hilt component lifetimes](https://developer.android.com/training/dependency-injection/hilt-android) |
| HK1 | Hilt vs Koin vs Manual DI, Hilt Scope Hierarchy table | `@ActivityRetainedScoped` "Use for: ViewModels via `@HiltViewModel`" | Same as C1 | Same as C1 |
| HK2 | Hilt vs Koin vs Manual DI, The Build-Time Cost and a Failure Modes row | Hilt KSP support is stable "since Hilt 2.48 + Dagger 2.48" | Dagger 2.48 "includes the alpha release of the Dagger and Hilt KSP processors" | [Dagger 2.48 release notes](https://github.com/google/dagger/releases/tag/dagger-2.48) |
| HK3 | Hilt vs Koin vs Manual DI, Common Pitfalls | "Every `@Provides` graph is wired eagerly for `@Singleton`" | Same as DI1: scoped bindings are created lazily on first request | Same as DI1 |

## Smaller notes (not flagged on the pages)

- **Room vs DataStore, Backup Behavior:** says Room databases sit under the app's `files/` directory, but Room databases live in `databases/`; both are included in Auto Backup by default. Android 12 and later use `android:dataExtractionRules`; the chapter mentions only `android:fullBackupContent`.
- **Room vs DataStore, Migration from SharedPreferences:** `sp.getBoolean("notifications") ?: true` may not match the `SharedPreferencesView.getBoolean(key, defValue)` signature. Not verified by compilation.
- **Hilt Components, Pattern 4:** "Workers run in a hidden internal component". `@HiltWorker` workers are created by `HiltWorkerFactory` with dependencies from `SingletonComponent`. Wording only.
- **Hilt vs Koin vs Manual DI, Koin compiler plugin and `module(override = true)`:** current Koin behaviour was not verified for this review. The chapter itself asks readers to verify current capabilities.

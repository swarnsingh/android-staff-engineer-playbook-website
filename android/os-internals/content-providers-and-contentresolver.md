# Content Providers and ContentResolver

## Overview

A `ContentProvider` is Android's structured cross-process data API. It exposes data through `content://` URIs and lets other components query, insert, update, delete, open files, or request typed streams through a `ContentResolver`.

Modern apps rarely need to create public custom providers, but Android itself uses providers everywhere: Contacts, MediaStore, DocumentsProvider, Settings, FileProvider, app startup initializers, and many SDK hooks. Understanding providers explains why URI permissions exist, why `ContentProvider.onCreate()` can run before `Application.onCreate()`, and why file sharing should not use raw filesystem paths.

---

## Why It Matters

1. **Providers are IPC.** Calls cross process boundaries through Binder and can block.
2. **Providers are startup entry points.** The OS can instantiate providers before your app's normal initialization path.
3. **URI permissions are security-critical.** They let you share one file without exposing your whole storage.
4. **Cursors are resources.** Leaking or over-reading them causes memory and file descriptor pressure.
5. **FileProvider is the safe sharing primitive.** `file://` sharing is obsolete and unsafe.

Staff-level Android code treats providers as secure APIs, not as local database helpers.

---

## First Principles

### URI Shape

```text
content://com.example.notes.provider/notes/42
```

Parts:

- `content://`: provider scheme.
- `com.example.notes.provider`: authority, globally unique per app.
- `/notes/42`: provider-defined path.

The authority is declared in the manifest:

```xml
<provider
    android:name=".NotesProvider"
    android:authorities="com.example.notes.provider"
    android:exported="false" />
```

### ContentResolver

Consumers do not call providers directly. They call `ContentResolver`:

```kotlin
val cursor = context.contentResolver.query(
    uri,
    arrayOf("title", "updated_at"),
    null,
    null,
    "updated_at DESC"
)
```

The resolver finds the provider for the URI authority and routes the call through Binder.

---

## Provider Contract

A provider commonly implements:

```kotlin
class NotesProvider : ContentProvider() {
    override fun onCreate(): Boolean {
        // Initialize lightweight dependencies only.
        return true
    }

    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?
    ): Cursor? {
        return null // Return a Cursor for supported URIs.
    }

    override fun getType(uri: Uri): String? = "vnd.android.cursor.item/vnd.example.note"

    override fun insert(uri: Uri, values: ContentValues?): Uri? = null
    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = 0
    override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = 0
}
```

For most app-internal persistence, use Room directly. Create a provider only when another app/process needs a stable content API.

---

## Startup Order Trap

Content providers are created before `Application.onCreate()` when the process starts. Many libraries historically used this for automatic initialization.

```text
Process start
  -> Install content providers
  -> Provider.onCreate()
  -> Application.onCreate()
  -> Activity/Service/Receiver
```

Implications:

- Provider initialization must be minimal.
- Do not assume your DI graph is ready unless you explicitly build for this.
- Third-party SDK providers can hurt cold start before your code appears in traces.

This is why AndroidX App Startup and manifest provider removal matter in startup optimization.

---

## FileProvider

Never expose raw file paths to other apps. Use `FileProvider` and URI grants:

```xml
<provider
    android:name="androidx.core.content.FileProvider"
    android:authorities="${applicationId}.fileprovider"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data
        android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/file_paths" />
</provider>
```

```kotlin
val uri = FileProvider.getUriForFile(
    context,
    "${BuildConfig.APPLICATION_ID}.fileprovider",
    file
)

val share = Intent(Intent.ACTION_SEND).apply {
    type = "image/png"
    putExtra(Intent.EXTRA_STREAM, uri)
    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
}
```

This grants access to one URI, not your whole filesystem.

---

## URI Permissions

Providers can grant temporary access:

- `FLAG_GRANT_READ_URI_PERMISSION`
- `FLAG_GRANT_WRITE_URI_PERMISSION`
- Persistable URI permissions for document-style access.

URI grants are narrower than storage permissions and should be preferred when sharing specific files.

---

## Cursor Discipline

Always close cursors:

```kotlin
context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
    val titleIndex = cursor.getColumnIndexOrThrow("title")
    while (cursor.moveToNext()) {
        val title = cursor.getString(titleIndex)
        // Consume row.
    }
}
```

Do not read huge provider results on the main thread. A provider query can hit disk, block on another process, or return a massive cursor window.

---

## Security

### Exported Providers

If a provider is exported, it is a public data API.

```xml
<provider
    android:name=".PartnerProvider"
    android:authorities="com.example.partner"
    android:exported="true"
    android:readPermission="com.example.permission.READ_PARTNER_DATA"
    android:writePermission="com.example.permission.WRITE_PARTNER_DATA" />
```

Protect with permissions, validate URI paths, enforce row-level access, and avoid SQL injection through untrusted selection strings.

### Path Permissions

Use path permissions when different URI subtrees need different access:

```xml
<path-permission
    android:pathPrefix="/public"
    android:readPermission="com.example.permission.READ_PUBLIC" />
```

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Cold start regression | SDK/provider initializes before app | Remove provider or lazy-init |
| Data leak | Exported provider with weak permissions | Export false or require signature permission |
| File exposure | Sharing `file://` path | Use FileProvider + URI grants |
| Main-thread ANR | Provider query blocks | Query off main; page results |
| Cursor leak | Cursor not closed | Use `.use {}` |
| SQL injection | Trusting selection strings | Use args, validate paths, avoid raw SQL |
| Broken authority | Authority collision or flavor mismatch | Use applicationId-based authorities |

---

## Staff Engineer Thinking

1. **Do we need a provider at all?** Most app-internal data should stay behind repositories/Room.
2. **Treat providers as public APIs.** URI shape, permissions, and compatibility matter.
3. **Audit startup providers.** Manifest-declared providers can silently tax cold start.
4. **Prefer URI grants over broad storage permissions.** Share the exact thing, not the whole shelf.
5. **Design for hostile callers.** Validate URI, projection, sort order, and access rights.

---

## Probing Questions

1. What problem does `ContentResolver` solve?
2. Why can a `ContentProvider` run before `Application.onCreate()`?
3. Why is `FileProvider` safer than `file://`?
4. How do URI permission grants work?
5. What makes an exported provider dangerous?
6. Why should provider queries avoid the main thread?
7. When is a custom provider justified?
8. How can provider startup hurt cold-start performance?

## Answer Key

1. **What problem does `ContentResolver` solve?**
   It acts as a single, centralized API for consuming data from multiple `ContentProvider`s, abstracting away the IPC and routing details required to query data across different app processes.
2. **Why can a `ContentProvider` run before `Application.onCreate()`?**
   The Android OS instantiates and initializes all manifest-declared content providers during process startup, ensuring they are ready to handle IPC requests before the main application code starts running.
3. **Why is `FileProvider` safer than `file://`?**
   `FileProvider` translates internal file paths into `content://` URIs, allowing apps to grant temporary, granular access to specific files without exposing the raw filesystem path or requiring broad storage permissions.
4. **How do URI permission grants work?**
   URI grants provide temporary read or write access (`FLAG_GRANT_READ_URI_PERMISSION`) to a specific `content://` URI, delegating access only for that resource and typically expiring when the recipient's task finishes.
5. **What makes an exported provider dangerous?**
   It acts as a public API accessible by any app on the device. Without strong permission checks and input validation, it can leak sensitive data or become vulnerable to SQL injection.
6. **Why should provider queries avoid the main thread?**
   Provider queries involve synchronous IPC (Binder calls) that may hit disk or block on another process, which can lead to UI jank or Application Not Responding (ANR) crashes.
7. **When is a custom provider justified?**
   A custom provider is justified only when you need to expose a stable, structured data API or share files securely with other applications or the Android OS, rather than for internal app persistence.
8. **How can provider startup hurt cold-start performance?**
   Because all manifest-declared providers are initialized before `Application.onCreate()`, heavyweight operations or complex dependency graphs in `ContentProvider.onCreate()` will block the main thread and delay app startup.

## Further Reading

- [`intent-resolution-and-manifest.md`](intent-resolution-and-manifest.md)
- [`the-binder.md`](the-binder.md)
- [`../performance/startup.md`](../performance/startup.md)
- [`../data-and-di/room.md`](../data-and-di/room.md)
- [Android Developers: Content providers](https://developer.android.com/guide/topics/providers/content-providers)

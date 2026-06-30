# Repository Pattern

> The Repository pattern mediates between the domain and data mapping layers using a collection-like interface for accessing domain objects. In Android, the Repository pattern is arguably the single most important architectural boundary. It dictates that the UI layer (ViewModel) must never know *where* data comes from. A Staff engineer uses the Repository as the **Single Source of Truth (SSOT)**, flawlessly orchestrating the complex dance between a local SQLite database (Room), a remote API (Retrofit), and in-memory caches.

---

## Overview

Without a Repository, ViewModels become massive god-classes. They make Retrofit calls, handle HTTP errors, save to Room, and map database entities to UI models. This violates the Single Responsibility Principle and makes the ViewModel impossible to test without a functioning backend.

The Repository extracts this logic. To the ViewModel, the Repository looks like a simple, always-available collection of data.

---

## 1. The Core Android Implementation: The Single Source of Truth

In a modern, production-grade Android app, data is usually fetched from a network, but it must be displayed immediately the *next* time the user opens the app (Offline-First). 

This requires two data sources:
1. **Remote Data Source** (Retrofit API)
2. **Local Data Source** (Room Database)

**The Golden Rule of the SSOT:** The UI *only* ever observes the Local Data Source. The Remote Data Source *only* ever writes to the Local Data Source. 

### The Network-Bound Resource Strategy

```kotlin
// The Repository Interface (Domain Layer)
interface UserRepository {
    fun getUserStream(userId: String): Flow<User>
    suspend fun refreshUser(userId: String)
}

// The Implementation (Data Layer)
class UserRepositoryImpl(
    private val api: UserApi,           // Remote
    private val userDao: UserDao,       // Local
    private val ioDispatcher: CoroutineDispatcher
) : UserRepository {

    // 1. The UI observes the local database directly
    override fun getUserStream(userId: String): Flow<User> {
        return userDao.observeUser(userId).map { it.toDomainModel() }
    }

    // 2. The Network updates the database, NOT the UI
    override suspend fun refreshUser(userId: String) {
        withContext(ioDispatcher) {
            try {
                // Fetch from network
                val networkUser = api.getUser(userId)
                
                // Write to database. 
                // Because the UI is observing the DB via Room Flow, 
                // the UI will automatically update!
                userDao.insert(networkUser.toEntity())
                
            } catch (e: Exception) {
                // Handle or rethrow network error
                throw NetworkSyncException("Failed to fetch user", e)
            }
        }
    }
}
```

This pattern solves dozens of race conditions. If the user rotates the screen while the network call is happening, the new `Activity` immediately reads the cached data from the Room `Flow`. When the network call finishes, Room emits the new data, and the UI updates seamlessly.

---

## 2. In-Memory Caching (The 3-Tiered Repository)

Sometimes, data changes so fast (or is so ephemeral) that persisting it to SQLite via Room is too slow or unnecessary. In these cases, the Repository manages a 3-tier system: Memory -> Disk -> Network.

```kotlin
class ProductRepository(
    private val api: ProductApi,
    private val dao: ProductDao
) {
    // Tier 1: In-Memory Cache using Mutex for thread safety
    private val memoryCache = mutableMapOf<String, Product>()
    private val cacheMutex = Mutex()

    suspend fun getProduct(id: String): Product {
        // 1. Check Memory (Fastest)
        cacheMutex.withLock {
            memoryCache[id]?.let { return it }
        }

        // 2. Check Disk (Medium)
        val localProduct = dao.getProduct(id)
        if (localProduct != null) {
            val domainProduct = localProduct.toDomainModel()
            cacheMutex.withLock { memoryCache[id] = domainProduct } // Update memory
            return domainProduct
        }

        // 3. Check Network (Slowest)
        val networkProduct = api.getProduct(id)
        val domainProduct = networkProduct.toDomainModel()
        
        // Update both caches
        dao.insert(networkProduct.toEntity())
        cacheMutex.withLock { memoryCache[id] = domainProduct }
        
        return domainProduct
    }
}
```
**Staff Insight:** Hardcoding caching logic into the repository is fine for small apps, but in massive codebases, this logic is often abstracted using the `Store` library by Dropbox, which provides declarative Kotlin flows for multi-tiered caching.

---

## 3. Data Mapping: The Anti-Corruption Layer

The Repository sits on the architectural boundary between the Data layer and the Domain layer. Therefore, it is responsible for **Mapping**.

The JSON structure your backend returns (`NetworkUser`) is rarely identical to the SQLite table structure (`UserEntity`), which is rarely identical to the clean model your UI wants (`User`).

```kotlin
// The UI only ever sees this pure Kotlin class
data class User(val id: String, val fullName: String)

// The Repository handles the dirty translation
override suspend fun refreshUser(id: String) {
    val networkObj: NetworkUser = api.getUser(id)
    
    // Map Network -> DB Entity
    val entity = UserEntity(
        id = networkObj.userId,
        first = networkObj.firstName,
        last = networkObj.lastName
    )
    dao.insert(entity)
}

override fun getUser(id: String): Flow<User> {
    return dao.observeUser(id).map { entity ->
        // Map DB Entity -> Domain Model
        User(
            id = entity.id,
            fullName = "${entity.first} ${entity.last}"
        )
    }
}
```
If the backend changes `firstName` to `given_name` in the JSON API, you only change the `NetworkUser` mapping. The `UserEntity` and Domain `User` models remain untouched. This is the Anti-Corruption Layer in action.

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **Fractured State** | The Repository returns network data directly to the UI, bypassing the database. Later, another screen reads the database and gets stale data. | Strictly enforce the Single Source of Truth rule. The network must write to the database, and the UI must read from the database. |
| **Fat Repositories** | A `UserRepository` that handles login, fetching profiles, uploading avatars, and tracking friends. The class becomes 2,000 lines long. | Split repositories by entity or subdomain (e.g. `AuthRepository`, `ProfileRepository`, `SocialRepository`). |
| **Leaking Data Models** | Returning Retrofit models (`NetworkUser`) or Room entities (`UserEntity`) directly to the ViewModel. | The ViewModel must only receive Domain models. Use mapper extension functions (`.toDomain()`) inside the Repository. |

---

## 5. Common Pitfalls

### Pitfall 1: Repositories creating CoroutineScopes
```kotlin
class BadRepository {
    private val repoScope = CoroutineScope(Dispatchers.IO)
    
    fun fetchData() {
        repoScope.launch { api.getData() } // BAD! Fire and forget.
    }
}
```
If the user leaves the screen, the ViewModel is destroyed, but the Repository's `repoScope` is still running, wasting battery and network.
*Fix:* Repositories should expose `suspend` functions and let the caller (`ViewModelScope`) manage the lifecycle and cancellation.

### Pitfall 2: Bypassing the Repository
A developer needs to fetch a user's avatar. They inject `UserApi` directly into the `ProfileViewModel` because "it's just a quick network call, I don't need a repository."
*Fix:* This breaks the offline-first architecture. When the user opens the app on a plane, the avatar will fail to load because it wasn't routed through the Repository's caching layer. Injecting APIs directly into ViewModels is an architectural strict-fail.

---

## Probing Questions

1.  **Concurrency:** If you have an in-memory cache inside a Singleton Repository, and two different ViewModels call `getProduct("123")` at the exact same millisecond, how do you prevent the Repository from executing two identical network calls simultaneously?
2.  **Flow Consolidation:** The `NetworkBoundResource` pattern returns a `Flow<Resource<T>>` that emits `Loading`, then `Success` or `Error`. How does this pattern differ mechanically from simply exposing a `Flow<T>` from Room and returning a `Result` from a `suspend fun refresh()`? Which is better for Jetpack Compose?
3.  **Pagination:** The Paging 3 library utilizes a `RemoteMediator`. How does `RemoteMediator` enforce the Single Source of Truth principle across a paginated RecyclerView, a Room database, and a Retrofit API?
4.  **Data Deletion:** The user logs out. You need to clear the in-memory caches of 15 different Repositories. How do you architect this without hardcoding `repo.clearCache()` 15 times in your `LogoutUseCase`?
5.  **Multiplatform:** You are moving your Repository to a Kotlin Multiplatform `commonMain` module. Your Android app uses Room, and your iOS app uses CoreData. What interface pattern is required in the shared code to allow platform-specific databases to act as the Single Source of Truth?

## Further Reading

- [`../reference-architectures/offline-first-app.md`](../reference-architectures/offline-first-app.md) — How the entire app architecture orbits around the SSOT Repository.
- [`../android/architecture/viewmodel.md`](../android/architecture/viewmodel.md) — How ViewModels consume Repository flows lifecycle-safely.
- [`../android/data-and-di/room-vs-datastore.md`](../android/data-and-di/room-vs-datastore.md) — Choosing the right persistence layer for the local data source.
- [`adapter.md`](adapter.md) — The mechanical pattern used to map Network models to Domain models.

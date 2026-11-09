# Decorator Pattern

> In modern Android development, you rarely implement the classic "Gang of Four" Decorator pattern by manually wrapping interfaces. Instead, you consume it constantly through idiomatic framework APIs: **OkHttp Interceptors**, **Jetpack Compose Modifiers**, and higher-order function wrappers. Extension functions alone do not wrap or dynamically override an object; they are statically resolved helpers. A Staff engineer must recognize these as decorators, understand how their order of application alters behavior, and know when to build custom decorators to handle cross-cutting concerns like logging, caching, and retry logic without polluting business logic.

---

## Overview

The Decorator pattern allows behavior to be added to an individual object, dynamically or statically, without affecting the behavior of other objects from the same class. It provides a flexible alternative to subclassing for extending functionality.

In Android, inheritance scales poorly. If you have a `BaseActivity` and you need some activities to have Analytics, some to have Authentication, and some to have both, you end up with a tangled hierarchy (`AuthAnalyticsActivity`, etc.). Decorators solve this by wrapping the core component with layers of behavior.

---

## 1. The Classic Implementation vs. Kotlin Idioms

### The "Gang of Four" Object-Oriented Approach
Historically, Decorators were built by implementing a shared interface and passing the wrapped object in the constructor.

```kotlin
// The shared interface
interface ImageLoader {
    fun loadImage(url: String): Bitmap
}

// The core component
class BasicImageLoader : ImageLoader {
    override fun loadImage(url: String): Bitmap {
        return networkClient.download(url)
    }
}

// The abstract decorator
abstract class ImageLoaderDecorator(
    private val wrapped: ImageLoader
) : ImageLoader {
    override fun loadImage(url: String): Bitmap {
        return wrapped.loadImage(url) // Delegate to wrapped
    }
}

// A concrete decorator
class CachingImageLoader(wrapped: ImageLoader) : ImageLoaderDecorator(wrapped) {
    override fun loadImage(url: String): Bitmap {
        return cache.get(url) ?: super.loadImage(url).also { cache.put(url, it) }
    }
}

// Usage
val loader = CachingImageLoader(BasicImageLoader())
```

### The Modern Kotlin Approach (High-Order Functions & Extensions)
Kotlin's language features often make classical decorator classes unnecessary. We can achieve the same behavior using higher-order functions or extension functions.

```kotlin
// A type alias for our function signature
typealias ImageLoader = suspend (String) -> Bitmap

// The core component
val basicLoader: ImageLoader = { url -> networkClient.download(url) }

// A decorator implemented as a higher-order function
fun withCache(
    cache: Cache,
    loader: ImageLoader
): ImageLoader = { url ->
    cache.get(url) ?: loader(url).also { cache.put(url, it) }
}

// Usage
val loader = withCache(memoryCache, basicLoader)
```
This is one functional way to decorate behavior. Alternative snippets define different ImageLoader shapes; app-owned network/cache dependencies and imports are omitted. Blocking implementations need an off-main owner; a suspend signature alone does not move blocking I/O off main.

---

## 2. Core Android Example 1: OkHttp Interceptors

The most critical application of the Decorator pattern in Android is **OkHttp Interceptors**. An interceptor wraps the network request and response, allowing you to rewrite headers, retry failures, or log traffic without modifying your Retrofit APIs.

### The Interceptor Interface (The Decorator)
```java
// Simplified OkHttp Interceptor interface
public interface Interceptor {
  Response intercept(Chain chain) throws IOException;
}
```

The `Chain` object holds the wrapped request and the mechanism to proceed to the next layer.

### Building Concrete Interceptors (Decorators)

**1. Authentication Decorator:**

Use the session-bound `AuthInterceptor`, `SessionTokenStore`, and `TokenAuthenticator` from [Retrofit and OkHttp](../android/networking-and-security/retrofit-and-okhttp.md#production-example). That implementation restricts credentials to one HTTPS origin, shares refresh outcomes, and prevents a late refresh from restoring a logged-out session. A generic decorator should not invent a second token lifecycle.

**2. Retry Decorator (bodyless reads only):**
```kotlin
class RetryInterceptor(private val maxAttempts: Int = 2) : Interceptor {
    init { require(maxAttempts in 1..3) }

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val retrySafe = request.method in setOf("GET", "HEAD") && request.body == null
        var attempt = 1
        while (true) {
            if (chain.call().isCanceled()) throw IOException("Canceled")
            val response = chain.proceed(request)
            if (!retrySafe || response.code !in setOf(502, 503, 504) ||
                response.header("Retry-After") != null || attempt >= maxAttempts) {
                return response
            }
            response.close() // Close only the response being discarded.
            attempt++
        }
    }
}
```

This small application interceptor makes at most one extra attempt by default. It does not retry 401/403, other client errors, writes, requests with bodies, or thrown I/O failures. A `Retry-After` response is returned to the caller for scheduling. Production retry policy also needs backoff, jitter and a total deadline; see [Retry](retry.md). Do not add writes merely because the body can be replayed: the server contract and idempotency protection must make repetition safe.

### The Importance of Application Order

```kotlin
// Fresh store and client for this login only; never put another account in it.
val client = OkHttpClient.Builder()
    .followRedirects(false)
    .followSslRedirects(false)
    .retryOnConnectionFailure(false)
    .callTimeout(30, TimeUnit.SECONDS)
    .addInterceptor(RetryInterceptor(maxAttempts = 2))
    .addInterceptor(AuthInterceptor(sessionStore, apiOrigin))
    .authenticator(TokenAuthenticator(sessionStore, apiOrigin, refreshApi))
    .build()
```

The bodyless-read restriction belongs to the retry decorator, not the whole client: unlike the Ktor auth sample, this `TokenAuthenticator` can replay a write with a replayable body after a 401. Use it for writes only when the API contract makes replay safe, for example with a server-enforced idempotency key.

An outer application interceptor re-enters the inner application decorators when it calls `proceed` again. With retry outside auth, each permitted read attempt rechecks the captured session. With auth outside retry, the inner retry reuses the already-decorated request. Neither ordering refreshes an expired token by itself: the bounded authenticator handles a 401 challenge, independently of this 5xx policy. Its refresh API uses a separate client with no auth interceptor or authenticator. Logout invalidates the old store and cancels old-session calls; already-sent requests cannot be recalled.

`maxAttempts` counts this decorator's `proceed` calls, not every wire exchange: the authenticator and OkHttp may perform their own bounded follow-ups. Configure and test the combined call budget. These are application interceptors; a network interceptor must call `proceed` exactly once.

---

## 3. Core Android Example 2: Jetpack Compose Modifiers

Jetpack Compose replaces Android's deep inheritance tree (`View` -> `TextView` -> `Button`) with composition and the Decorator pattern via **Modifiers**.

### How Modifiers are Decorators
A `Modifier` is an ordered, immutable list of elements that decorate a Compose layout node. 

```kotlin
@Composable
fun ProfileCard() {
    Box(
        modifier = Modifier
            .padding(16.dp)           // Decorator 1
            .background(Color.Blue)   // Decorator 2
            .padding(16.dp)           // Decorator 3
            .clickable { /* ... */ }  // Decorator 4
    ) {
        Text("Staff Engineer")
    }
}
```

### Order of Application (The "Onion" Model)
In Compose, Modifiers wrap the UI node from the outside in.
1. The outermost layer adds 16dp of padding.
2. The next layer fills the remaining bounds with Blue background.
3. The next layer adds *another* 16dp of padding (which will be Blue, because it's inside the background layer).
4. The innermost layer makes the remaining space clickable.

If you swap the order:
```kotlin
Modifier
    .clickable { /* ... */ }
    .padding(16.dp)
```
The click ripple will extend *into* the padding area. If padding is first, the padding area is not clickable. Understanding this onion-layer decorator model is essential for Staff-level UI debugging.

---

## 4. Core Android Example 3: ContextWrapper

Android's `Context` is heavily overloaded. To extend its behavior without subclassing the OS-provided `ContextImpl` directly, Android uses the Decorator pattern via `ContextWrapper`.

```java
// Simplified framework delegation outline; other Context members omitted.
public class ContextWrapper extends Context {
    Context mBase; // The wrapped component

    public ContextWrapper(Context base) {
        mBase = base;
    }

    @Override
    public void startActivity(Intent intent) {
        mBase.startActivity(intent); // Delegate
    }
}
```

### Modern Usage: Locale Injection

`ContextWrapper` illustrates delegated context behavior, but overriding `attachBaseContext` is not the preferred complete per-app language solution. For a user-selected app language, use the supported AppCompat/platform locale APIs and their persistence/recreation contract:

```kotlin
// Called from the app's language-settings action; appcompat dependency required.
AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags("es-ES"))
```

On Android 13+, the platform stores the app-language choice. For Android 12 (API 32) and lower, opt in to AppCompat storage inside the manifest's `<application>` element:

```xml
<service
    android:name="androidx.appcompat.app.AppLocalesMetadataHolderService"
    android:enabled="false"
    android:exported="false">
    <meta-data android:name="autoStoreLocales" android:value="true" />
</service>
```

`autoStoreLocales` performs a blocking main-thread read and can cause StrictMode disk read/write violations. Without this opt-in, implement custom locale storage and supply the stored choice before `onCreate` on older Android versions, following the per-app language guide. `createConfigurationContext` remains useful for scoped resource lookup; it does not by itself implement a persisted user language preference.

## 5. Architectural Role: The "Cross-Cutting Concern" Solver

Staff engineers use the Decorator pattern to keep business logic clean. If you find your Repositories or Use Cases littered with logging, analytics, or transaction management, you are violating the Single Responsibility Principle.

**Bad (Tangled Concerns):**
```kotlin
class ProductRepositoryImpl(private val api: ProductApi) : ProductRepository {
    override suspend fun getProducts(): List<Product> {
        metrics.startTimer("fetch_products")
        try {
            val products = api.getProducts()
            metrics.incrementSuccess("fetch_products")
            return products
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (e: Exception) {
            metrics.incrementFailure("fetch_products")
            crashlytics.recordException(e)
            throw e
        } finally {
            metrics.stopTimer("fetch_products")
        }
    }
}
```

**Good (Clean Core + Decorator):**
```kotlin
// The clean core
class ProductRepositoryImpl(private val api: ProductApi) : ProductRepository {
    override suspend fun getProducts(): List<Product> = api.getProducts()
}

// The Decorator
class MetricsProductRepository(
    private val wrapped: ProductRepository,
    private val metrics: MetricsClient
) : ProductRepository {
    override suspend fun getProducts(): List<Product> {
        metrics.startTimer("fetch_products")
        return try {
            wrapped.getProducts().also { metrics.incrementSuccess("fetch_products") }
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (e: Exception) {
            metrics.incrementFailure("fetch_products")
            throw e
        } finally {
            metrics.stopTimer("fetch_products")
        }
    }
}
```
The metrics fragment assumes non-throwing instrumentation with per-invocation timing. Expected I/O failures in the tangled example should not all become Crashlytics non-fatals; choose telemetry by operational meaning.

**Wiring with DI (Koin):**
```kotlin
module {
    // Provide the core
    single<ProductRepository>(named("core")) { ProductRepositoryImpl(get()) }
    
    // Provide the decorated version as the default
    single<ProductRepository> { MetricsProductRepository(get(named("core")), get()) }
}
```

---

## 6. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The Ordering Bug** | Interceptors or Modifiers are applied in the wrong sequence, causing logical errors (e.g. logging the request *before* Auth headers are added). | Write integration tests that assert on the *final* network payload or UI bounds. Document order requirements clearly. |
| **Object Identity Loss** | Using `is` checks or downcasting on a decorated object fails because the object is the decorator, not the core class. | **Never downcast interfaces.** If you need specific behavior, it must be exposed on the interface itself. |
| **Stack Overflow (Chaining)** | Wrapping the same object too many times, resulting in deep call stacks and performance penalties. | Collapse multiple decorators into a single configuration object where possible. |
| **Leaking the Wrapped Object** | The Decorator accidentally exposes the wrapped object, allowing callers to bypass the decorator's logic. | The wrapped reference (`private val wrapped`) must strictly remain `private`. |

---

## 7. Common Pitfalls

### Pitfall 1: Decorating Data Classes

Kotlin data classes are final, but can implement an interface and be wrapped by a decorator that implements that interface. Wrapping does not corrupt the original generated methods. Decide equality and ownership explicitly: wrapper equality is not automatically interchangeable with its delegate, and generated `copy()` remains shallow. Use a plain data transformation when no behavioral wrapper is needed.

### Pitfall 2: Fat Interfaces
The Decorator pattern requires implementing the entire interface. If your `UserRepository` interface has 45 methods, creating a `MetricsUserRepositoryDecorator` requires writing 45 forwarding methods.
*Fix:* This is a sign you are violating the Interface Segregation Principle. Split the massive interface into smaller, focused interfaces (e.g., `UserReader`, `UserWriter`) before decorating. Kotlin's interface delegation (`class MetricsUserRepo(private val wrapped: UserRepo) : UserRepo by wrapped`) can alleviate the boilerplate, but the underlying architectural flaw remains.

---

## Probing Questions

1.  **OkHttp Internals:** OkHttp distinguishes between `addInterceptor` (Application Interceptors) and `addNetworkInterceptor`. Both use the Decorator pattern. What is the fundamental difference in what they wrap, and when would you use one over the other?
2.  **Compose Modifiers:** You have `Modifier.padding(10.dp).clickable { }.padding(10.dp)`. Draw the exact bounding boxes and hit areas for this component. How does the Compose runtime merge these decorators internally?
3.  **Kotlin Delegation:** Kotlin supports the Decorator pattern natively via the `by` keyword (`class MyDecorator(b: Base) : Base by b`). How does the Kotlin compiler implement this under the hood? What are the limitations regarding overriding behavior?
4.  **Testing Strategy:** You have a `ProductRepository` wrapped by a `CacheDecorator` and a `MetricsDecorator`. How do you structure your unit tests? Do you test the fully composed object, or test each decorator in isolation using mocks for the wrapped interface?
5.  **Performance:** Every layer of decoration adds a method call to the stack frame. In a hot loop (like a RecyclerView binding or Compose recomposition), at what point does this overhead become measurable? How can Kotlin inline functions mitigate this?

## Answer Key

1. **OkHttp Internals:**
   Application Interceptors wrap the entire request before anything happens (great for app-level logic like Auth). Network interceptors wrap actual network exchanges, may run for redirects/follow-ups, and are skipped for responses served entirely from cache. They must call proceed exactly once for the same connection host/port; application interceptors have different replay/follow-up semantics.
2. **Compose Modifiers:**
   The runtime wraps the node from the outside in. The outermost 10dp padding is applied, then the clickable area is established (meaning the outer padding is NOT clickable), then the inner 10dp padding is applied (meaning the clickable area includes this inner padding), and finally the core content is drawn.
3. **Kotlin Delegation:**
   The Kotlin compiler generates forwarding methods for every method in the interface, delegating them to the provided instance. A limitation is that if the base class calls one of its own methods internally, it won't invoke your overridden version in the decorator because the base class doesn't know about the wrapper.
4. **Testing Strategy:**
   Test each decorator in isolation and the composed chain. Isolation checks each contract; composition checks ordering, cache hits/misses, error/cancellation propagation and response ownership that isolated mocks can miss.
5. **Performance:**
   Overhead becomes measurable in deep UI hierarchies or very tight loops. Eligible inline higher-order calls can remove wrapper/lambda-call overhead at their call sites; they do not automatically inline arbitrary interface decorators or stored function objects. Runtime/JIT behavior and code size matter, so measure the actual hot path.

## Further Reading

- [`../backend-for-mobile/api-design-for-mobile.md`](../backend-for-mobile/api-design-for-mobile.md) — How OkHttp interceptors mutate the API payload before it hits Retrofit.
- [`../android/compose/modifiers-and-layout.md`](../android/compose/modifiers-and-layout.md) — Deep dive into the Compose Modifier hierarchy.
- [`../android/data-and-di/dependency-injection.md`](../android/data-and-di/dependency-injection.md) — How to construct heavily decorated objects cleanly using Hilt or Koin.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Advanced OkHttp interceptor chaining.

- [OkHttp interceptor guide (official source)](https://raw.githubusercontent.com/square/okhttp/master/docs/features/interceptors.md) — ordering, application/network constraints and closing discarded responses.
- [OkHttp Authenticator contract (official source)](https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Authenticator.kt) — bounded challenge follow-ups and returning the original response.
- [HTTP Semantics, RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) — automatic retry and idempotency.
- [Kotlin extensions are statically resolved](https://kotlinlang.org/docs/extensions.html#extensions-are-resolved-statically)
- [Kotlin delegation and overriding limits](https://kotlinlang.org/docs/delegation.html)
- [Data-class generated methods and shallow copy](https://kotlinlang.org/docs/data-classes.html)
- [Inline eligibility and stored lambdas](https://kotlinlang.org/docs/inline-functions.html)
- [Android per-app language APIs](https://developer.android.com/guide/topics/resources/app-languages)
- [Coroutine cancellation classification](https://kotlinlang.org/docs/cancellation-and-timeouts.html)

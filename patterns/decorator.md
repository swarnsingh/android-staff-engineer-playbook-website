# Decorator Pattern

> In modern Android development, you rarely implement the classic "Gang of Four" Decorator pattern by manually wrapping interfaces. Instead, you consume it constantly through idiomatic framework APIs: **OkHttp Interceptors**, **Jetpack Compose Modifiers**, and **Kotlin Extension Functions**. A Staff engineer must recognize these as decorators, understand how their order of application alters behavior, and know when to build custom decorators to handle cross-cutting concerns like logging, caching, and retry logic without polluting business logic.

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
This functional approach is exactly how modern Android libraries handle decoration.

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
```kotlin
class AuthInterceptor(private val tokenManager: TokenManager) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        
        // Don't decorate if we already have an Auth header
        if (originalRequest.header("Authorization") != null) {
            return chain.proceed(originalRequest)
        }
        
        val token = tokenManager.getValidToken()
        val decoratedRequest = originalRequest.newBuilder()
            .header("Authorization", "Bearer $token")
            .build()
            
        // Pass the decorated request down the chain
        return chain.proceed(decoratedRequest)
    }
}
```

**2. Retry Decorator:**
```kotlin
class RetryInterceptor(private val maxRetries: Int = 3) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var response = chain.proceed(chain.request())
        var tryCount = 1
        
        while (!response.isSuccessful && tryCount < maxRetries) {
            response.close() // Avoid connection leaks
            tryCount++
            // Proceed again (retry)
            response = chain.proceed(chain.request())
        }
        
        return response
    }
}
```

### The Importance of Application Order
Because decorators wrap each other like an onion, **order matters immensely**.

```kotlin
val client = OkHttpClient.Builder()
    .addInterceptor(RetryInterceptor(maxRetries = 3)) // Wraps AuthInterceptor
    .addInterceptor(AuthInterceptor(tokenManager))    // Wraps the network call
    .build()
```
If `RetryInterceptor` is added first, it wraps the `AuthInterceptor`. If a request fails, the retry loop will execute the `AuthInterceptor` again, fetching a fresh token if the old one expired.
If the order is reversed, the `AuthInterceptor` runs once, grabs a token, and hands off to the `RetryInterceptor`. If the token is expired, the retry loop will just blindly retry 3 times with the same expired token.

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
// From the Android Framework
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
If you need to force a specific language in a specific `Activity` (regardless of the system language), you wrap the base context:

```kotlin
class LocalizedActivity : AppCompatActivity() {
    override fun attachBaseContext(newBase: Context) {
        val locale = Locale("es", "ES")
        val config = Configuration(newBase.resources.configuration)
        config.setLocale(locale)
        
        // Decorate the base context with our new configuration
        val decoratedContext = newBase.createConfigurationContext(config)
        super.attachBaseContext(decoratedContext)
    }
}
```

---

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
        } catch (e: Exception) {
            metrics.incrementFailure("fetch_products")
            throw e
        } finally {
            metrics.stopTimer("fetch_products")
        }
    }
}
```
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
Do not attempt to use the Decorator pattern on Kotlin `data classes`. Data classes are designed to be transparent holders of state, and their generated `equals()`, `hashCode()`, and `copy()` methods will break if you try to wrap them. Use composition or extension functions to derive new state instead.

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

## Further Reading

- [`../backend-for-mobile/api-design-for-mobile.md`](../backend-for-mobile/api-design-for-mobile.md) — How OkHttp interceptors mutate the API payload before it hits Retrofit.
- [`../android/compose/modifiers-and-layout.md`](../android/compose/modifiers-and-layout.md) — Deep dive into the Compose Modifier hierarchy.
- [`../android/data-and-di/dependency-injection.md`](../android/data-and-di/dependency-injection.md) — How to construct heavily decorated objects cleanly using Hilt or Koin.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Advanced OkHttp interceptor chaining.

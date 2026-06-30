# Networking with Ktor in KMP

> Retrofit + OkHttp is the default networking stack for every Android app. But Retrofit relies on Java dynamic proxies (`java.lang.reflect.Proxy`) and OkHttp relies on `java.net.Socket` — both are JVM-only APIs that cannot compile for iOS. Ktor Client is the canonical KMP replacement. A Staff engineer must understand Ktor's architecture (Core vs Engine separation), how to configure platform-specific engines (OkHttp on Android, Darwin/NSURLSession on iOS), and how to migrate complex Retrofit interceptor chains to Ktor's plugin system.

---

## Overview

Ktor Client is architecturally split into two independent halves:

```text
┌────────────────────────────────────────────────────────────┐
│                    commonMain                               │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ktor-client-core                                     │  │
│  │  - HttpClient class                                   │  │
│  │  - Request/Response pipeline                          │  │
│  │  - Plugin system (interceptors)                       │  │
│  │  - ContentNegotiation (JSON serialization)            │  │
│  │  - Logging, Auth, DefaultRequest plugins              │  │
│  │                                                       │  │
│  │  This half does NOT know how to open a TCP socket.    │  │
│  └────────────────────────┬─────────────────────────────┘  │
│                           │ HttpClientEngine interface      │
└───────────────────────────┼─────────────────────────────────┘
                            │
              ┌─────────────┴─────────────────┐
              │                               │
   ┌──────────▼────────────┐    ┌─────────────▼───────────┐
   │ androidMain            │    │ iosMain                  │
   │                        │    │                          │
   │ ktor-client-okhttp     │    │ ktor-client-darwin       │
   │ Uses OkHttp 4.x under  │    │ Uses NSURLSession under  │
   │ the hood for HTTP.     │    │ the hood for HTTP.       │
   │ Full OkHttp interceptor│    │ Full Apple ATS, proxy,   │
   │ compatibility.         │    │ background download      │
   │                        │    │ support.                 │
   └────────────────────────┘    └─────────────────────────┘
```

---

## 1. Setting Up the HttpClient

### The Shared Client Factory (Staff Pattern)

Do not instantiate `HttpClient()` with the no-arg constructor in `commonMain`. This uses Ktor's service-loader mechanism to find an engine — which works but is opaque and untestable. Instead, accept the engine explicitly:

```kotlin
// shared/src/commonMain/kotlin/com/example/network/HttpClientFactory.kt

import io.ktor.client.*
import io.ktor.client.engine.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json

fun createHttpClient(
    engine: HttpClientEngine,
    baseUrl: String,
    authTokenProvider: suspend () -> String?
): HttpClient {
    return HttpClient(engine) {
        
        // 1. JSON serialization (replaces MoshiConverterFactory)
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true       // Don't crash on unknown fields
                isLenient = true               // Accept malformed JSON gracefully
                encodeDefaults = false         // Don't serialize default values
                explicitNulls = false          // Omit null fields from output
                coerceInputValues = true       // Use defaults for missing fields
            })
        }
        
        // 2. Logging (replaces HttpLoggingInterceptor)
        install(Logging) {
            logger = object : Logger {
                override fun log(message: String) {
                    // Route to Kermit or platform logger
                    co.touchlab.kermit.Logger.d { message }
                }
            }
            level = LogLevel.HEADERS  // NONE, INFO, HEADERS, BODY, ALL
            sanitizeHeader { header ->
                header == HttpHeaders.Authorization
            }
        }
        
        // 3. Default request configuration (replaces Retrofit baseUrl)
        defaultRequest {
            url(baseUrl)
            contentType(ContentType.Application.Json)
        }
        
        // 4. Authentication (replaces OkHttp AuthInterceptor)
        install(HttpRequestRetry) {
            retryOnServerErrors(maxRetries = 3)
            exponentialDelay()
        }
        
        // 5. Auth token injection
        install(createClientPlugin("AuthPlugin") {
            onRequest { request, _ ->
                val token = authTokenProvider()
                if (token != null) {
                    request.bearerAuth(token)
                }
            }
        })
        
        // 6. Timeout configuration
        install(HttpTimeout) {
            requestTimeoutMillis = 30_000
            connectTimeoutMillis = 10_000
            socketTimeoutMillis = 30_000
        }
        
        // 7. Response validation (replaces Retrofit's built-in error handling)
        expectSuccess = true  // Throw on non-2xx responses
        HttpResponseValidator {
            handleResponseExceptionWithRequest { exception, request ->
                val clientException = exception as? ClientRequestException
                    ?: return@handleResponseExceptionWithRequest
                val errorBody = clientException.response.bodyAsText()
                throw ApiException(
                    statusCode = clientException.response.status.value,
                    errorBody = errorBody,
                    url = request.url.toString()
                )
            }
        }
    }
}

class ApiException(
    val statusCode: Int,
    val errorBody: String,
    val url: String
) : Exception("API error $statusCode on $url: $errorBody")
```

### Platform Engine Configuration

**Android (`androidMain`):**
```kotlin
// shared/src/androidMain/kotlin/com/example/network/PlatformEngine.kt

import io.ktor.client.engine.okhttp.*
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

fun createPlatformEngine(): OkHttpEngine {
    return OkHttp.create {
        config {
            // Access the raw OkHttpClient.Builder for Android-specific features
            connectTimeout(10, TimeUnit.SECONDS)
            readTimeout(30, TimeUnit.SECONDS)
            
            // Add Chucker for debugging (only in debug builds)
            if (BuildConfig.DEBUG) {
                addInterceptor(ChuckerInterceptor(appContext))
            }
            
            // Add certificate pinning
            certificatePinner(
                CertificatePinner.Builder()
                    .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
                    .build()
            )
        }
    }
}
```

**iOS (`iosMain`):**
```kotlin
// shared/src/iosMain/kotlin/com/example/network/PlatformEngine.kt

import io.ktor.client.engine.darwin.*
import platform.Foundation.*

fun createPlatformEngine(): DarwinClientEngine {
    return Darwin.create {
        configureRequest {
            // Access raw NSMutableURLRequest for iOS-specific features
            setAllowsCellularAccess(true)
            setTimeoutInterval(30.0)
        }
        
        configureSession {
            // Access raw NSURLSessionConfiguration
            // This enables Apple's App Transport Security (ATS)
            // and built-in HTTP/3 support
            setURLCache(
                NSURLCache(
                    memoryCapacity = 10 * 1024 * 1024,   // 10MB memory cache
                    diskCapacity = 50 * 1024 * 1024,      // 50MB disk cache
                    diskPath = "ktor_cache"
                )
            )
        }
    }
}
```

---

## 2. Retrofit → Ktor Migration (Side-by-Side)

### Simple GET with Query Parameters

**Retrofit:**
```kotlin
interface ProductApi {
    @GET("api/v1/products")
    suspend fun getProducts(
        @Query("category") category: String,
        @Query("page") page: Int,
        @Query("limit") limit: Int = 20
    ): ProductListResponse
}
```

**Ktor:**
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
}
```

### POST with JSON Body

**Retrofit:**
```kotlin
@POST("api/v1/orders")
suspend fun submitOrder(@Body request: OrderRequest): OrderResponse
```

**Ktor:**
```kotlin
suspend fun submitOrder(request: OrderRequest): OrderResponse {
    return client.post("api/v1/orders") {
        contentType(ContentType.Application.Json)
        setBody(request)
    }.body()
}
```

### Multipart File Upload

**Retrofit:**
```kotlin
@Multipart
@POST("api/v1/upload")
suspend fun uploadFile(
    @Part file: MultipartBody.Part,
    @Part("description") description: RequestBody
): UploadResponse
```

**Ktor:**
```kotlin
suspend fun uploadFile(
    fileBytes: ByteArray,
    fileName: String,
    description: String
): UploadResponse {
    return client.submitFormWithBinaryData(
        url = "api/v1/upload",
        formData = formData {
            append("file", fileBytes, Headers.build {
                append(HttpHeaders.ContentDisposition, "filename=\"$fileName\"")
            })
            append("description", description)
        }
    ).body()
}
```

### Streaming / SSE

**Retrofit + OkHttp:**
```kotlin
// Complex — requires custom OkHttp EventSource
```

**Ktor:**
```kotlin
suspend fun streamUpdates(onEvent: (ServerEvent) -> Unit) {
    client.prepareGet("api/v1/events/stream").execute { response ->
        val channel: ByteReadChannel = response.body()
        while (!channel.isClosedForRead) {
            val line = channel.readUTF8Line() ?: break
            if (line.startsWith("data:")) {
                val event = Json.decodeFromString<ServerEvent>(line.removePrefix("data:"))
                onEvent(event)
            }
        }
    }
}
```

---

## 3. Error Handling Architecture

In Retrofit, error handling is implicit — a non-2xx response throws `HttpException`. In Ktor, you must design your error handling explicitly.

### The Sealed Result Wrapper (Staff Pattern)

```kotlin
// shared/src/commonMain/kotlin/com/example/network/NetworkResult.kt

sealed interface NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>
    data class Error(
        val code: Int,
        val message: String,
        val errorBody: String? = null
    ) : NetworkResult<Nothing>
    data class NetworkError(val exception: Throwable) : NetworkResult<Nothing>
}

// Extension function to wrap Ktor calls
suspend inline fun <reified T> safeApiCall(
    crossinline block: suspend () -> T
): NetworkResult<T> {
    return try {
        NetworkResult.Success(block())
    } catch (e: ClientRequestException) {
        // 4xx errors
        NetworkResult.Error(
            code = e.response.status.value,
            message = e.response.status.description,
            errorBody = e.response.bodyAsText()
        )
    } catch (e: ServerResponseException) {
        // 5xx errors
        NetworkResult.Error(
            code = e.response.status.value,
            message = "Server error",
            errorBody = e.response.bodyAsText()
        )
    } catch (e: IOException) {
        // Network connectivity errors
        NetworkResult.NetworkError(e)
    } catch (e: SerializationException) {
        // JSON parsing errors
        NetworkResult.Error(code = -1, message = "Failed to parse response: ${e.message}")
    }
}

// Usage in Repository
class ProductRepository(private val api: ProductApi) {
    suspend fun getProducts(category: String): NetworkResult<List<Product>> {
        return safeApiCall { api.getProducts(category, page = 1).products }
    }
}
```

---

## 4. Testing Ktor in `commonTest`

Ktor provides a **MockEngine** that intercepts HTTP requests and returns pre-defined responses. This runs identically on JVM and Native:

```kotlin
// shared/src/commonTest/kotlin/com/example/network/ProductApiTest.kt

class ProductApiTest {
    
    @Test
    fun `getProducts returns parsed products`() = runTest {
        val mockEngine = MockEngine { request ->
            assertEquals("/api/v1/products", request.url.encodedPath)
            assertEquals("electronics", request.url.parameters["category"])
            
            respond(
                content = """
                    {
                        "products": [
                            {"id": "1", "name": "Laptop", "price_cents": 99900},
                            {"id": "2", "name": "Phone", "price_cents": 79900}
                        ],
                        "total": 2
                    }
                """.trimIndent(),
                status = HttpStatusCode.OK,
                headers = headersOf(HttpHeaders.ContentType, "application/json")
            )
        }
        
        val client = createHttpClient(
            engine = mockEngine,
            baseUrl = "https://api.example.com",
            authTokenProvider = { "test-token" }
        )
        val api = ProductApi(client)
        
        val response = api.getProducts("electronics", page = 1)
        
        assertEquals(2, response.products.size)
        assertEquals("Laptop", response.products[0].name)
        assertEquals(99900, response.products[0].priceCents)
    }
    
    @Test
    fun `getProducts handles 401 error`() = runTest {
        val mockEngine = MockEngine {
            respond(
                content = """{"error": "Token expired"}""",
                status = HttpStatusCode.Unauthorized,
                headers = headersOf(HttpHeaders.ContentType, "application/json")
            )
        }
        
        val client = createHttpClient(
            engine = mockEngine,
            baseUrl = "https://api.example.com",
            authTokenProvider = { "expired-token" }
        )
        val api = ProductApi(client)
        val repository = ProductRepository(api)
        
        val result = repository.getProducts("electronics")
        
        assertTrue(result is NetworkResult.Error)
        assertEquals(401, (result as NetworkResult.Error).code)
    }
}
```

---

## 5. Why the Darwin Engine Matters (Not Just "Use NSURLSession")

The `Darwin` engine doesn't just wrap `NSURLSession` — it inherits all of Apple's networking optimizations for free:

| Feature | OkHttp (Android) | Darwin/NSURLSession (iOS) |
|---|---|---|
| HTTP/2 | Supported | Supported |
| HTTP/3 (QUIC) | Not supported (needs Cronet) | **Built-in since iOS 15** |
| Background downloads | Not possible without `DownloadManager` | **Built-in `NSURLSessionDownloadTask`** |
| App Transport Security | N/A | **Enforced by iOS** (blocks plain HTTP) |
| Proxy configuration | Manual | **Automatic (uses system proxy)** |
| DNS-over-HTTPS | Manual | **Built-in since iOS 14** |
| Battery optimization | Manual (must schedule requests) | **iOS automatically batches requests during low-power mode** |
| Certificate pinning | OkHttp `CertificatePinner` | `NSURLSessionDelegate` + `URLAuthenticationChallenge` |

**Staff Insight:** If you force the iOS app to use a custom TCP engine (e.g., via Ktor's CIO engine) instead of Darwin, you lose HTTP/3, background downloads, ATS enforcement, and battery optimizations. **Always use the Darwin engine on iOS.**

---

## Probing Questions

1.  **Engine Architecture:** Why does Ktor separate the `HttpClient` from the `HttpClientEngine`? What problem does this inversion solve for testing and for KMP?
2.  **Interceptor Migration:** You have an OkHttp interceptor that adds `X-Request-ID: UUID` to every request, logs the request/response time, and retries on 503 with exponential backoff. Write the equivalent Ktor plugin configuration.
3.  **Darwin Advantage:** Your iOS app makes 50 API calls per minute. The Android version uses OkHttp and the iOS version uses Darwin. Which version consumes less battery in Low Power Mode, and why?
4.  **Error Handling:** In Retrofit, a 404 response returns a `Response<T>` object with `isSuccessful = false`. In Ktor, what happens by default when you set `expectSuccess = true`? What happens when you set it to `false`?
5.  **MockEngine:** You write a test using `MockEngine` in `commonTest`. This test runs on JVM (fast). You then run `./gradlew iosSimulatorArm64Test`. Does the `MockEngine` test also run on iOS? What runtime differences might cause it to fail?

## Further Reading

- [`libraries-ecosystem.md`](libraries-ecosystem.md) — Why Retrofit can't be used in `commonMain` (the JVM dependency trap).
- [`../../android/networking-and-security/ktor-vs-retrofit.md`](../../android/networking-and-security/ktor-vs-retrofit.md) — The detailed Android-focused decision file comparing Retrofit and Ktor.
- [`dependency-injection.md`](dependency-injection.md) — How to inject the platform-specific `HttpClientEngine` via Koin.
- [`build-system-and-source-sets.md`](build-system-and-source-sets.md) — Where to put `ktor-client-okhttp` (androidMain) vs `ktor-client-darwin` (iosMain) dependencies.

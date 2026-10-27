package dev.playbook.validation.fixtures.ktorclient
import android.net.Uri
import androidx.compose.runtime.*
import androidx.compose.runtime.snapshots.*
import androidx.compose.material3.SnackbarHostState
import androidx.lifecycle.*
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.room.*
import dagger.BindsInstance
import dagger.hilt.*
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.collections.immutable.*
import javax.inject.*

// shared/src/commonMain/kotlin/com/example/network/HttpClientFactory.kt

import io.ktor.client.*
import io.ktor.client.engine.*
import io.ktor.client.plugins.api.createClientPlugin
import io.ktor.client.statement.bodyAsText
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
                coerceInputValues = true // Coerce supported null/unknown-enum values; missing defaults are a separate rule.
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
        
        // 4. Bounded retries for explicitly replay-safe requests
        install(HttpRequestRetry) {
            maxRetries = 3
            retryIf { request, response ->
                request.method in setOf(HttpMethod.Get, HttpMethod.Head) &&
                    response.status.value in 500..599
            }
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



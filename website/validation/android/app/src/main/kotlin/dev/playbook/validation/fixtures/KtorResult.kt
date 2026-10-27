package dev.playbook.validation.fixtures.ktorresult
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
import dev.playbook.validation.fixtures.ktorclient.ApiException
import io.ktor.client.plugins.*
import io.ktor.client.statement.*
import kotlinx.serialization.SerializationException

// shared/src/commonMain/kotlin/com/example/network/NetworkResult.kt
import kotlinx.io.IOException

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
    } catch (e: ApiException) {
        NetworkResult.Error(e.statusCode, e.message ?: "API error", e.errorBody)
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

data class Product(val id:Int)
data class Products(val products:List<Product>)
interface ProductApi { suspend fun getProducts(category:String,page:Int):Products }


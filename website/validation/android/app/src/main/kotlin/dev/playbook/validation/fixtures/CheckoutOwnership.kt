package dev.playbook.validation.fixtures.checkoutownership
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

data class CheckoutUiState(
    val submitted: Boolean = false,
    val userMessage: String? = null,
)

@HiltViewModel
class CheckoutViewModel @Inject constructor(
    private val api: CheckoutApi,
) : ViewModel() {
    private val _uiState = MutableStateFlow(CheckoutUiState())
    val uiState = _uiState.asStateFlow()

    fun submit() = viewModelScope.launch {
        try {
            api.submit(_uiState.value)
            _uiState.update { it.copy(submitted = true) }
        } catch (e: Exception) {
            if (e is CancellationException) throw e
            _uiState.update { it.copy(userMessage = e.message.orEmpty()) }
        }
    }

    fun messageShown() = _uiState.update { it.copy(userMessage = null) }
}

class CheckoutApi @Inject constructor() { suspend fun submit(state:CheckoutUiState) = Unit }


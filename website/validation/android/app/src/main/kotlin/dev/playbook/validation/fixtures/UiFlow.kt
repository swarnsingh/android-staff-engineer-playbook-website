package dev.playbook.validation.fixtures.uiflow
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

@HiltViewModel
class UserViewModel @Inject constructor(
    private val repository: UserRepository
) : ViewModel() {

    // We take the Cold flow, map it to our UI state, and convert it to a Hot StateFlow.
    val uiState: StateFlow<UserUiState> = repository.observeUsers()
        .map<List<User>, UserUiState> { users -> UserUiState.Success(users) }
        .catch { e -> emit(UserUiState.Error(e.message)) }
        // The Pivot: stateIn converts Cold to Hot.
        .stateIn(
            scope = viewModelScope, // Dies when ViewModel dies
            started = SharingStarted.WhileSubscribed(5000), // Pauses when UI is hidden
            initialValue = UserUiState.Loading
        )
}

data class User(val id:Int)
sealed interface UserUiState { data object Loading:UserUiState; data class Success(val users:List<User>):UserUiState; data class Error(val message:String?):UserUiState }
class UserRepository @Inject constructor() { fun observeUsers():Flow<List<User>> = flowOf(emptyList()) }


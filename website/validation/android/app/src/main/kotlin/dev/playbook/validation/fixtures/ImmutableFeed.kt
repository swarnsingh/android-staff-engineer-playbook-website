package dev.playbook.validation.fixtures.immutablefeed
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

sealed interface FeedUiState {
    data object Loading : FeedUiState
    data class Success(val items: ImmutableList<Post>) : FeedUiState
    data class Error(val message: String, val retryable: Boolean) : FeedUiState
}

@HiltViewModel
class FeedViewModel @Inject constructor(repo: FeedRepository) : ViewModel() {
    val uiState: StateFlow<FeedUiState> = repo.observePosts()
        .map { FeedUiState.Success(it.toImmutableList()) as FeedUiState }
        .catch { emit(FeedUiState.Error(it.message.orEmpty(), retryable = true)) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), FeedUiState.Loading)
}

data class Post(val id:Int)
class FeedRepository @Inject constructor() { fun observePosts(): Flow<List<Post>> = flowOf(emptyList()) }


package dev.playbook.validation.fixtures.mainsafetrace
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
import androidx.tracing.trace

// androidx.tracing:tracing:1.3.0 (1.3.0 moved the tracing-ktx code into tracing)
// import androidx.tracing.trace
// Synchronous section stays inside the selected thread's non-suspending block.
suspend fun loadFeed() = withContext(ioDispatcher) {
    trace("Feed/loadBlocking") { blockingApi.fetchFeed() }
}

val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
object blockingApi { fun fetchFeed():String = "feed" }


package dev.playbook.validation.fixtures.analyticsbatch
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
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

class AnalyticsTracker(private val uploadBatch: suspend (List<Event>) -> Unit) {
    private val batchMutex = Mutex()
    private val uploadMutex = Mutex()
    private val batch = mutableListOf<Event>()

    suspend fun trackEvent(event: Event) {
        val ready = batchMutex.withLock { batch.add(event); batch.size >= 50 }
        if (ready) flush()
    }

    suspend fun flush() = uploadMutex.withLock {
        val snapshot = batchMutex.withLock { batch.toList().also { batch.clear() } }
        if (snapshot.isNotEmpty()) {
            try {
                uploadBatch(snapshot)
            } catch (failure: Throwable) {
                withContext(NonCancellable) {
                    batchMutex.withLock { batch.addAll(0, snapshot) }
                }
                throw failure
            }
        }
    }
}

data class Event(val id: Int)

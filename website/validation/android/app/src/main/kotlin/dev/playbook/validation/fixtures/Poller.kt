package dev.playbook.validation.fixtures.poller
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
import kotlin.time.Duration.Companion.seconds

class Poller(private val api: PollApi, private val scope: CoroutineScope) {
    fun start(): Job = scope.launch {
        while (isActive) {
            api.fetch()
            delay(30.seconds)
        }
    }
}
interface PollApi { suspend fun fetch() }



package dev.playbook.validation.fixtures.serviceflow
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

    fun processAudioFile(fileUri: Uri): Flow<Int> = flow {
        for (progress in 1..100) {
            delay(100) // Illustrative processing
            emit(progress)
        }
    }.flowOn(Dispatchers.IO) // import kotlinx.coroutines.flow.flowOn

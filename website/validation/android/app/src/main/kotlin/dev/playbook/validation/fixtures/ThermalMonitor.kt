package dev.playbook.validation.fixtures.thermalmonitor
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
import android.content.Context
import android.os.PowerManager
import androidx.annotation.RequiresApi
import java.util.concurrent.Executor

@RequiresApi(29)
class ThermalMonitor(
    context: Context,
    private val onStatus: (Int) -> Unit
) {
    private val powerManager = context.getSystemService(PowerManager::class.java)
    private val listener = PowerManager.OnThermalStatusChangedListener { status ->
        onStatus(status)
    }

    @RequiresApi(29)
    fun start(executor: Executor) {
        onStatus(powerManager.currentThermalStatus)
        powerManager.addThermalStatusListener(executor, listener)
    }

    @RequiresApi(29)
    fun stop() {
        powerManager.removeThermalStatusListener(listener)
    }
}



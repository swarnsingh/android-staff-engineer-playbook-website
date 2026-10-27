package dev.playbook.validation.fixtures.snapshotcounter
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

private class CounterStateRecord(var value: Int) : StateRecord() {
    override fun assign(value: StateRecord) { this.value = (value as CounterStateRecord).value }
    override fun create(): StateRecord = CounterStateRecord(value)
}

class CounterState(initialValue: Int = 0) : StateObject {
    private var record = CounterStateRecord(initialValue)

    override val firstStateRecord: StateRecord get() = record
    override fun prependStateRecord(value: StateRecord) {
        @Suppress("UNCHECKED_CAST")
        record = value as CounterStateRecord
    }

    var value: Int
        get() = record.readable(this).value
        set(value) {
            record.writable(this) { this.value = value }
        }
}



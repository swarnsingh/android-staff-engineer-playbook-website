package dev.playbook.validation.fixtures.lifecycleeffects
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

@Composable fun CollectEffects(viewModel: EffectsViewModel, snackbarHostState: SnackbarHostState) {
val lifecycleOwner = LocalLifecycleOwner.current // androidx.lifecycle.compose
LaunchedEffect(viewModel, lifecycleOwner, snackbarHostState) {
    lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.effects.collect { effect ->
            when (effect) {
                is UiEffect.ShowToast -> snackbarHostState.showSnackbar(effect.message)
            }
        }
    }
} // imports: androidx.lifecycle.Lifecycle, androidx.lifecycle.repeatOnLifecycle

}
sealed interface UiEffect { data class ShowToast(val message:String): UiEffect }
class EffectsViewModel: ViewModel() { val effects: Flow<UiEffect> = MutableSharedFlow() }


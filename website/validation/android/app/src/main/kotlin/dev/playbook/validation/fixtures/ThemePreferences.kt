package dev.playbook.validation.fixtures.themepreferences
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
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.lifecycle.compose.collectAsStateWithLifecycle

class ThemeRepository(private val prefs: DataStore<Preferences>) {
    fun observe(): Flow<Theme> = prefs.data
        .map { it[KEY]?.let(Theme::valueOf) ?: Theme.SYSTEM } // KEY is a stringPreferencesKey
        .distinctUntilChanged()
}


@Composable fun ThemeReader(themeRepo:ThemeRepository) {
val theme by themeRepo.observe().collectAsStateWithLifecycle(Theme.SYSTEM)

}
enum class Theme { SYSTEM, DARK, LIGHT }
val KEY = stringPreferencesKey("theme")


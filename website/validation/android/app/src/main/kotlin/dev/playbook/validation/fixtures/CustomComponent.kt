package dev.playbook.validation.fixtures.customcomponent
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

@LoggedUserScoped
@DefineComponent(parent = SingletonComponent::class)
interface LoggedUserComponent {
    @DefineComponent.Builder
    interface Builder {
        fun userId(@BindsInstance userId: String): Builder
        fun build(): LoggedUserComponent
    }
}

@Scope @Retention(AnnotationRetention.BINARY)
annotation class LoggedUserScoped

@EntryPoint
@InstallIn(LoggedUserComponent::class)
interface UserEntryPoint {
    fun userPreferences(): UserPreferences
    fun userAnalytics(): UserAnalytics
}

@Singleton
class SessionManager @Inject constructor(
    private val builders: javax.inject.Provider<LoggedUserComponent.Builder>,
) {
    private var component: LoggedUserComponent? = null

    fun login(userId: String) {
        component = builders.get().userId(userId).build()
    }

    fun logout() {
        component = null
    }

    fun prefs(): UserPreferences = component!!
        .let { dagger.hilt.EntryPoints.get(it, UserEntryPoint::class.java) }
        .userPreferences()
}

@LoggedUserScoped class UserPreferences @Inject constructor()
@LoggedUserScoped class UserAnalytics @Inject constructor()

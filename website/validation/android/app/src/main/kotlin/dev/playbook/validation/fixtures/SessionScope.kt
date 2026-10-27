package dev.playbook.validation.fixtures.sessionscope
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

@Scope @Retention(AnnotationRetention.BINARY)
annotation class LoggedUserScoped

@DefineComponent(parent = SingletonComponent::class)
@LoggedUserScoped
interface UserComponent {
    @DefineComponent.Builder
    interface Builder {
        fun userId(@BindsInstance @UserId id: String): Builder
        fun build(): UserComponent
    }
}

@Qualifier @Retention(AnnotationRetention.BINARY)
annotation class UserId

@LoggedUserScoped
class UserSessionState @Inject constructor(@UserId val userId: String) {
    // Tied to the LoggedUser component lifetime.
}

@Singleton
class SessionManager @Inject constructor(
    private val builders: javax.inject.Provider<UserComponent.Builder>,
) {
    private var component: UserComponent? = null
    private var scope: CoroutineScope? = null   // matched coroutine scope

    fun login(userId: String) {
        logout() // End the previous explicitly owned session first.
        component = builders.get().userId(userId).build()
        scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    }

    fun logout() {
        scope?.cancel()
        scope = null
        component = null     // drops all @LoggedUserScoped instances
    }
}



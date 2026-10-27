package dev.playbook.validation
import androidx.activity.ComponentActivity
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import dagger.*
import dagger.hilt.*
import dagger.hilt.components.SingletonComponent
import dagger.hilt.android.AndroidEntryPoint
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import javax.inject.Inject

@AndroidEntryPoint class HiltTestActivity:ComponentActivity()
interface CartRepository { val items:StateFlow<List<String>> }
class FakeCartRepository:CartRepository {
 private val mutable=MutableStateFlow(emptyList<String>())
 override val items:StateFlow<List<String>> = mutable
 fun addItem(item:String) { mutable.value=mutable.value+item }
}
@Module @InstallIn(SingletonComponent::class)
object CartRepositoryModule { @Provides fun provideRepository():CartRepository=FakeCartRepository() }
@HiltViewModel class CartVm @Inject constructor(val repository:CartRepository):ViewModel()
@Composable fun CartScreen() {
 val vm:CartVm=viewModel()
 val items by vm.repository.items.collectAsState()
 Text(if(items.isEmpty()) "Empty" else items.joinToString())
}

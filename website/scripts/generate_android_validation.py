#!/usr/bin/env python3
"""Extract selected corrected Android examples into real API/compiler fixtures.

Only package/import declarations, enclosing function context for statement-only
excerpts, and application-owned domain helpers are supplied. Framework classes
come from the pinned Android/AndroidX/Hilt/Room dependencies.
"""
from pathlib import Path
import hashlib,json,re
import build
ROOT=build.ROOT;OUT=ROOT/'website/validation/android/app/src/main/kotlin/dev/playbook/validation/fixtures';OUT.mkdir(parents=True,exist_ok=True)
records=[]
imports='''import android.net.Uri
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
'''
def blocks(path):
 text,_=build.corrected((ROOT/path).read_text(),path)
 return re.findall(r'```kotlin\n(.*?)```',text,re.S)
def emit(name,path,selector,helpers='',enclose=None,extra_imports=''):
 candidates=[c for c in blocks(path) if selector(c)];assert len(candidates)==1,(name,len(candidates));block=candidates[0]
 body=enclose(block) if enclose else block
 (OUT/(name+'.kt')).write_text('package dev.playbook.validation.fixtures.'+name.lower()+'\n'+imports+extra_imports+'\n'+body+'\n'+helpers+'\n')
 records.append({'fixture':name,'source':path,'sha256':hashlib.sha256(block.encode()).hexdigest(),'enclosingContext':bool(enclose),'applicationHelpers':bool(helpers)})
helpers='''
data class Product(val id: Int, val name: String)
data class ProductDto(val id: Int, val name: String) { fun toRow() = ProductRow(id,name) }
data class ProductsResponse(val items: List<ProductDto>)
interface ProductApi { suspend fun getProducts(): ProductsResponse }
@Entity data class ProductRow(@PrimaryKey val id: Int, val name: String) { fun toDomain() = Product(id,name) }
@Entity data class SyncMetadata(@PrimaryKey val key: String, val time: Long) { companion object { fun now() = SyncMetadata("products",1) } }
@Dao interface ProductDao {
 @Query("SELECT * FROM ProductRow ORDER BY id") fun observeProducts(): Flow<List<ProductRow>>
 @Upsert suspend fun upsertProducts(rows: List<ProductRow>)
 @Upsert suspend fun updateSyncMetadata(row: SyncMetadata)
 @Query("SELECT COUNT(*) FROM SyncMetadata") suspend fun metadataCount(): Int
}
@Database(entities=[ProductRow::class, SyncMetadata::class],version=1) abstract class ProductDatabase: RoomDatabase() { abstract fun products(): ProductDao }
'''
emit('RepositoryTransaction','android/data-and-di/repository-source-of-truth.md',lambda c:'class ProductRepository(' in c,helpers)
emit('SnapshotCounter','android/compose/snapshot-system.md',lambda c:'class CounterState(initialValue' in c)
emit('LifecycleEffects','android/concurrency/shared-flow-and-state-flow.md',lambda c:'val lifecycleOwner = LocalLifecycleOwner.current' in c,'''sealed interface UiEffect { data class ShowToast(val message:String): UiEffect }
class EffectsViewModel: ViewModel() { val effects: Flow<UiEffect> = MutableSharedFlow() }
''',lambda c:'@Composable fun CollectEffects(viewModel: EffectsViewModel, snackbarHostState: SnackbarHostState) {\n'+c+'\n}')
emit('ImmutableFeed','android/architecture/state-management.md',lambda c:'data class Success(val items: ImmutableList<Post>)' in c,'''data class Post(val id:Int)
class FeedRepository @Inject constructor() { fun observePosts(): Flow<List<Post>> = flowOf(emptyList()) }
''')
emit('CheckoutOwnership','android/architecture/state-management.md',lambda c:'data class CheckoutUiState(' in c and 'class CheckoutViewModel' in c,'''class CheckoutApi @Inject constructor() { suspend fun submit(state:CheckoutUiState) = Unit }
''')
emit('SessionScope','android/data-and-di/scopes.md',lambda c:'interface UserComponent {' in c)
# Two source blocks constitute one custom-component example.
path='android/data-and-di/components.md';a=next(c for c in blocks(path) if 'interface LoggedUserComponent {' in c);b=next(c for c in blocks(path) if 'interface UserEntryPoint' in c)
(OUT/'CustomComponent.kt').write_text('package dev.playbook.validation.fixtures.customcomponent\n'+imports+'\n'+a+'\n'+b+'''\n@LoggedUserScoped class UserPreferences @Inject constructor()
@LoggedUserScoped class UserAnalytics @Inject constructor()
''')
records.append({'fixture':'CustomComponent','source':path,'sha256':hashlib.sha256((a+b).encode()).hexdigest(),'applicationHelpers':True})
# The service method is an excerpt of an Android Service; the unchanged method
# body is extracted and checked with the actual Android Uri and coroutine APIs.
path='android/concurrency/services.md';text,_=build.corrected((ROOT/path).read_text(),path);body=re.search(r'    fun processAudioFile\(fileUri: Uri\): Flow<Int> = flow \{.*?\n    }\.flowOn\(Dispatchers.IO\)[^\n]*',text,re.S)[0]
(OUT/'ServiceFlow.kt').write_text('package dev.playbook.validation.fixtures.serviceflow\n'+imports+'\n'+body+'\n');records.append({'fixture':'ServiceFlow','source':path,'sha256':hashlib.sha256(body.encode()).hexdigest()})
(ROOT/'website/validation/android/fixtures.json').write_text(json.dumps(records,indent=2)+'\n');print('Extracted',len(records),'real-API fixtures')
# Additional completion fixtures exercise the corrected public API boundaries.
emit('AnalyticsBatch','android/concurrency/synchronization-and-mutex.md',lambda c:'class AnalyticsTracker(' in c,'data class Event(val id: Int)',extra_imports='import kotlinx.coroutines.sync.Mutex\nimport kotlinx.coroutines.sync.withLock\n')
emit('UiFlow','android/architecture/flow.md',lambda c:'class UserViewModel' in c,'''data class User(val id:Int)
sealed interface UserUiState { data object Loading:UserUiState; data class Success(val users:List<User>):UserUiState; data class Error(val message:String?):UserUiState }
class UserRepository @Inject constructor() { fun observeUsers():Flow<List<User>> = flowOf(emptyList()) }
''')
emit('Poller','android/testing/unit-testing.md',lambda c:'class Poller(' in c,extra_imports='import kotlin.time.Duration.Companion.seconds\n')
emit('ThemePreferences','android/performance/startup.md',lambda c:'class ThemeRepository(' in c,'''enum class Theme { SYSTEM, DARK, LIGHT }
val KEY = stringPreferencesKey("theme")
''',lambda c:c[:c.index('// Compose:')]+'\n@Composable fun ThemeReader(themeRepo:ThemeRepository) {\n'+c[c.index('val theme by'): ]+'\n}',extra_imports='import androidx.datastore.core.DataStore\nimport androidx.datastore.preferences.core.*\nimport androidx.lifecycle.compose.collectAsStateWithLifecycle\n')
emit('MainSafeTrace','android/performance/macrobenchmark-and-perfetto.md',lambda c:'suspend fun loadFeed()' in c,'''val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
object blockingApi { fun fetchFeed():String = "feed" }
''',extra_imports='import androidx.tracing.trace\n')
emit('ThermalMonitor','android/performance/thermal-low-end-device-strategy.md',lambda c:'class ThermalMonitor(' in c,extra_imports='import android.content.Context\nimport android.os.PowerManager\nimport androidx.annotation.RequiresApi\nimport java.util.concurrent.Executor\n')
emit('ParcelableBoundary','kotlin/language-core/extensions.md',lambda c:'Bundle.getParcelableSafe' in c,extra_imports='import android.os.Bundle\nimport android.os.Build\n')
# Compile the exact JvmOverloads behavior at an interspersed required parameter.
(OUT/'OverloadContract.kt').write_text('''package dev.playbook.validation.fixtures.overloads
class OverloadContract {
 @JvmOverloads fun connect(a: Int = 1, required: String, b: Int = 2) = "$a:$required:$b"
}
''')
(ROOT/'website/validation/android/fixtures.json').write_text(json.dumps(records,indent=2)+'\n');print('Completion fixture count',len(records))
emit('KtorClient','android/kotlin-multiplatform/ecosystem/networking-with-ktor.md',lambda c:'fun createHttpClient(' in c)
emit('KtorResult','android/kotlin-multiplatform/ecosystem/networking-with-ktor.md',lambda c:'suspend inline fun <reified T> safeApiCall' in c,'''data class Product(val id:Int)
data class Products(val products:List<Product>)
interface ProductApi { suspend fun getProducts(category:String,page:Int):Products }
''',extra_imports='import dev.playbook.validation.fixtures.ktorclient.ApiException\nimport io.ktor.client.plugins.*\nimport io.ktor.client.statement.*\nimport kotlinx.serialization.SerializationException\n')
(ROOT/'website/validation/android/fixtures.json').write_text(json.dumps(records,indent=2)+'\n');print('Final fixtures',len(records))
TEST=ROOT/'website/validation/android/app/src/androidTest/kotlin/dev/playbook/validation';TEST.mkdir(parents=True,exist_ok=True)
path='android/testing/ui-testing.md'
a=next(c for c in blocks(path) if 'class CartScreenHiltTest' in c)
b=next(c for c in blocks(path) if 'object FakeCartRepositoryModule' in c)
(TEST/'ExtractedHiltTest.kt').write_text('''package dev.playbook.validation
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.*
import androidx.test.ext.junit.runners.AndroidJUnit4
import dagger.Module
import dagger.Provides
import dagger.hilt.android.testing.*
import dagger.hilt.components.SingletonComponent
import dagger.hilt.testing.TestInstallIn
import javax.inject.*
import org.junit.*
import org.junit.runner.RunWith
'''+a+'\n'+b+'\nval item1 = "Item 1"\n')
c=next(c for c in blocks(path) if 'fun enableChecks()' in c)
(TEST/'ExtractedAccessibilityTest.kt').write_text('''package dev.playbook.validation
import androidx.activity.ComponentActivity
import androidx.compose.ui.test.junit4.*
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import org.junit.*
class ExtractedAccessibilityTest {
'''+c+'\n@Test fun accessibilityIsConfigured() { composeRule.setContent { androidx.compose.material3.Text("Example") } }\n}\n')
records.append(dict(fixture='HiltAndAccessibilityTests',source=path,sha256=hashlib.sha256((a+b+c).encode()).hexdigest(),applicationHelpers=True))
(ROOT/'website/validation/android/fixtures.json').write_text(json.dumps(records,indent=2)+'\n')

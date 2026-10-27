package dev.playbook.validation.fixtures.repositorytransaction
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

class ProductRepository(
    private val database: RoomDatabase, // androidx.room.RoomDatabase; owns this DAO
    private val dao: ProductDao,
    private val api: ProductApi
) {
    fun observeProducts(): Flow<List<Product>> =
        dao.observeProducts()
            .map { rows -> rows.map(ProductRow::toDomain) }

    suspend fun refreshProducts() {
        val response = api.getProducts()
        database.withTransaction { // import androidx.room.withTransaction
            dao.upsertProducts(response.items.map(ProductDto::toRow))
            dao.updateSyncMetadata(SyncMetadata.now())
        }
    }
}


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


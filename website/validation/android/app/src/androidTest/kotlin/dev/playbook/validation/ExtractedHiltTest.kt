package dev.playbook.validation
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
@HiltAndroidTest
@RunWith(AndroidJUnit4::class)
class CartScreenHiltTest {

    @get:Rule(order = 0) val hiltRule = HiltAndroidRule(this)
    @get:Rule(order = 1) val composeRule = createAndroidComposeRule<HiltTestActivity>()

    @Inject lateinit var fakeRepository: FakeCartRepository

    @Before
    fun setUp() {
        hiltRule.inject()
    }

    @Test
    fun cartUpdates_whenRepositoryEmits() {
        composeRule.setContent {
            CartScreen()
        }

        composeRule.onNodeWithText("Empty").assertIsDisplayed()
        fakeRepository.addItem(item1)
        composeRule.onNodeWithText("Item 1").assertIsDisplayed()
    }
}

@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [CartRepositoryModule::class],
)
object FakeCartRepositoryModule {
    @Provides @Singleton
    fun provideFake(): FakeCartRepository = FakeCartRepository()

    @Provides
    fun provideRepo(fake: FakeCartRepository): CartRepository = fake
}

val item1 = "Item 1"

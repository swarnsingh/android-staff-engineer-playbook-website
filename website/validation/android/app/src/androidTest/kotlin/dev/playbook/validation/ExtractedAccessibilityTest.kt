package dev.playbook.validation
import androidx.activity.ComponentActivity
import androidx.compose.ui.test.junit4.*
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import org.junit.*
class ExtractedAccessibilityTest {
// androidTestImplementation("androidx.compose.ui:ui-test-junit4-accessibility:<compose-version>")
// import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
@get:Rule val composeRule = createAndroidComposeRule<ComponentActivity>()

@Before
fun enableChecks() { composeRule.enableAccessibilityChecks() }

@Test fun accessibilityIsConfigured() { composeRule.setContent { androidx.compose.material3.Text("Example") } }
}

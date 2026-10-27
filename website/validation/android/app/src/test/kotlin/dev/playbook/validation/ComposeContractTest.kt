package dev.playbook.validation
import android.app.Application
import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.clickable
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.MotionDurationScale
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.testTag
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],application=Application::class)
class ComposeContractTest {
 @get:Rule val composeRule=createComposeRule(effectContext=object:MotionDurationScale { override val scaleFactor=1f })
 @Test fun controlledTextInputUpdatesThroughCallback() {
  composeRule.setContent {
   var value by remember { mutableStateOf("") }
   TextField(value=value,onValueChange={value=it},modifier=Modifier.testTag("name"))
  }
  composeRule.onNodeWithTag("name").performTextInput("Ada")
  composeRule.onNodeWithTag("name").assertTextEquals("Ada")
 }
 @Test fun independentClickBoundarySurvivesDescendantMerge() {
  var clicked=false
  composeRule.setContent {
   Column(Modifier.semantics(mergeDescendants=true){}) {
    Text("Parent text")
    Button(onClick={clicked=true}) { Text("Independent action") }
   }
  }
  composeRule.onNodeWithText("Independent action").performClick()
  assertTrue(clicked)
 }
 @Test fun manualClockObservesIntermediateAnimation() {
  var target by mutableStateOf(0f);var observed=0f
  composeRule.mainClock.autoAdvance=false
  try {
   composeRule.setContent {
    val value by animateFloatAsState(target, tween(durationMillis=1000), label="test")
    val current=value // read in composition so animation updates invalidate this scope
    SideEffect { observed=current }
    Button(onClick={target=1f}) { Text("Animate") }
   }
   composeRule.mainClock.advanceTimeByFrame()
   composeRule.onNodeWithText("Animate").performClick()
   composeRule.mainClock.advanceTimeByFrame()
   composeRule.mainClock.advanceTimeByFrame()
   composeRule.mainClock.advanceTimeBy(400)
   composeRule.runOnIdle { assertTrue("intermediate value=$observed",observed>0f&&observed<1f) }
   composeRule.mainClock.advanceTimeBy(1000)
   composeRule.runOnIdle { assertEquals(1f,observed,0.001f) }
  } finally { composeRule.mainClock.autoAdvance=true }
 }
}

# Resource Sharing in KMP

> Sharing business logic is a solved problem in KMP. Sharing strings, images, fonts, and colors across platforms — the "design system" layer — is where most teams fail. Without a unified resource pipeline, your iOS team manually copies `.svg` files into `.xcassets`, your Android team runs them through the Vector Asset tool, and when the designer changes the brand color, you update it in two completely disjointed ecosystems. Compose Resources (the JetBrains-official solution) eliminates this by compiling all assets into a single shared artifact accessible from both Compose code and native Swift/UIKit.

---

## Overview

### The Resource Sharing Landscape

| Approach | Status | Mechanism | Limitation |
|---|---|---|---|
| **Moko Resources** (IceRock) | ⚠️ Legacy | `expect/actual` wrappers + platform build scripts | Fragile on CI, requires Xcode build phases |
| **Compose Resources** (JetBrains) | ✅ Stable (CMP 1.6+) | Unified `composeResources/` dir → Gradle plugin generates `Res` object | Requires Compose dependency |
| **Lyricist** | ⚠️ Niche | KSP-generated typesafe strings | Less maintained, string-only |
| **Manual `expect`/`actual`** | ✅ Always works | You write all the boilerplate | Extremely tedious at scale |

**Staff Recommendation:** Use **Compose Resources** for all new KMP projects. Even if you're using Paradigm A (shared logic, native UI), Compose Resources can serve as the single source of truth for strings and assets that both platforms consume.

---

## 1. Moko Resources (The Legacy Approach)

**Why you should not use Moko for new projects:**

Moko Resources (by IceRock) was the industry standard from 2020-2023. It generates `expect/actual` wrappers for:
- Android's `R.string.*` → `context.getString(R.string.welcome)`
- iOS's `Localizable.strings` → `NSLocalizedString("welcome", comment: "")`

**The Problem:**
Moko relies on platform-specific build phases:
1. On Android: It hooks into the Android Gradle Plugin's resource merging task.
2. On iOS: It copies `.strings` files into the iOS app bundle via a **Run Script Build Phase** in Xcode.

This Xcode build phase is notoriously fragile:
- It breaks when Xcode updates change the build phase execution order.
- It breaks on CI when the `$PODS_ROOT` path changes.
- It breaks when moving from CocoaPods to SPM distribution.
- Each iOS developer must manually add the build phase to their Xcode project.

**Migration path:** If you have an existing project using Moko, migrate to Compose Resources. The migration is mechanical — move `.strings` to `.xml` format and update imports.

---

## 2. Compose Resources (The Modern Standard)

### Directory Structure

Assets go into a unified `composeResources/` directory inside `commonMain`:

```text
shared/
 └── src/
      └── commonMain/
           └── composeResources/
                ├── drawable/
                │    ├── ic_logo.xml           ← Android Vector Drawable (works on iOS!)
                │    ├── ic_arrow_back.xml
                │    ├── background_gradient.xml
                │    └── hero_banner.png        ← Raster images also work
                │
                ├── font/
                │    ├── inter_regular.ttf
                │    ├── inter_bold.ttf
                │    └── inter_italic.ttf
                │
                ├── values/
                │    └── strings.xml            ← Default (English)
                │
                ├── values-es/
                │    └── strings.xml            ← Spanish
                │
                ├── values-fr/
                │    └── strings.xml            ← French
                │
                ├── values-ja/
                │    └── strings.xml            ← Japanese
                │
                └── values-ar/
                     └── strings.xml            ← Arabic (RTL)
```

### Strings XML Format

```xml
<!-- shared/src/commonMain/composeResources/values/strings.xml -->
<resources>
    <string name="app_name">My KMP App</string>
    <string name="welcome_message">Welcome, %s!</string>
    <string name="item_count">You have %d items in your cart</string>
    <string name="price_format">%s %.2f</string>
    
    <!-- Plurals -->
    <plurals name="items_selected">
        <item quantity="one">%d item selected</item>
        <item quantity="other">%d items selected</item>
    </plurals>
    
    <!-- String arrays -->
    <string-array name="sort_options">
        <item>Price: Low to High</item>
        <item>Price: High to Low</item>
        <item>Newest First</item>
        <item>Best Rating</item>
    </string-array>
</resources>
```

```xml
<!-- shared/src/commonMain/composeResources/values-es/strings.xml -->
<resources>
    <string name="app_name">Mi App KMP</string>
    <string name="welcome_message">¡Bienvenido, %s!</string>
    <string name="item_count">Tienes %d artículos en tu carrito</string>
    <string name="price_format">%s %.2f</string>
    
    <plurals name="items_selected">
        <item quantity="one">%d artículo seleccionado</item>
        <item quantity="other">%d artículos seleccionados</item>
    </plurals>
</resources>
```

### Generated `Res` Object

At compile time, the Gradle plugin generates a typesafe Kotlin object:

```kotlin
// AUTO-GENERATED — do not edit
object Res {
    object string {
        val app_name: StringResource
        val welcome_message: StringResource
        val item_count: StringResource
        val price_format: StringResource
    }
    
    object plurals {
        val items_selected: PluralStringResource
    }
    
    object drawable {
        val ic_logo: DrawableResource
        val ic_arrow_back: DrawableResource
        val background_gradient: DrawableResource
        val hero_banner: DrawableResource
    }
    
    object font {
        val inter_regular: FontResource
        val inter_bold: FontResource
        val inter_italic: FontResource
    }
}
```

### Using Resources in Compose (CMP)

```kotlin
// shared/src/commonMain/kotlin/com/example/ui/HomeScreen.kt

import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource
import org.jetbrains.compose.resources.pluralStringResource
import org.jetbrains.compose.resources.Font
import shared.generated.resources.*

@Composable
fun HomeScreen(userName: String, cartCount: Int) {
    Column(modifier = Modifier.padding(16.dp)) {
        // Image from shared drawable
        Image(
            painter = painterResource(Res.drawable.ic_logo),
            contentDescription = stringResource(Res.string.app_name),
            modifier = Modifier.size(48.dp)
        )
        
        // Formatted string with parameter
        Text(
            text = stringResource(Res.string.welcome_message, userName),
            style = TextStyle(
                fontFamily = FontFamily(Font(Res.font.inter_bold)),
                fontSize = 24.sp
            )
        )
        
        // Plural string
        Text(
            text = pluralStringResource(
                Res.plurals.items_selected,
                quantity = cartCount,
                cartCount
            )
        )
    }
}
```

### The Android Vector Drawable Miracle

The most powerful feature of Compose Resources is its ability to parse **Android Vector Drawables** (`.xml` files with `<vector>` roots) and render them on iOS via Skia.

```xml
<!-- shared/src/commonMain/composeResources/drawable/ic_shopping_cart.xml -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF000000"
        android:pathData="M7,18c-1.1,0 -1.99,0.9 -1.99,2S5.9,22 7,22s2,-0.9 2,-2 -0.9,-2 -2,-2zM1,2v2h2l3.6,7.59 -1.35,2.45c-0.16,0.28 -0.25,0.61 -0.25,0.96 0,1.1 0.9,2 2,2h12v-2H7.42c-0.14,0 -0.25,-0.11 -0.25,-0.25l0.03,-0.12 0.9,-1.63h7.45c0.75,0 1.41,-0.41 1.75,-1.03l3.58,-6.49c0.08,-0.14 0.12,-0.31 0.12,-0.48 0,-0.55 -0.45,-1 -1,-1H5.21l-0.94,-2H1z"/>
</vector>
```

On Android, this is a standard `VectorDrawable`. On iOS, CMP's resource library parses the `<path>` data and draws it directly using Skia's `SkPath` API. The iOS team does NOT need to convert this to PDF or SVG.

---

## 3. Accessing Resources Outside of Compose (Non-Composable Context)

If you're using Paradigm A (shared logic, native UI), you still want iOS to use the shared strings. The problem: `stringResource()` requires a `@Composable` context.

### The `getString()` Suspend Function

Compose Resources provides `getString()` — a `suspend` function that loads the string outside of composition:

```kotlin
// commonMain — utility for ViewModel error messages
class ErrorMapper {
    suspend fun mapError(error: DomainError): String {
        return when (error) {
            is DomainError.NetworkError -> getString(Res.string.error_network)
            is DomainError.AuthError -> getString(Res.string.error_auth)
            is DomainError.ServerError -> getString(Res.string.error_server, error.code)
        }
    }
}
```

### Bridging to Swift (The Wrapper Pattern)

Swift cannot call `suspend fun` directly without the SKIE or manual bridging. Create a synchronous wrapper in `iosMain`:

```kotlin
// shared/src/iosMain/kotlin/resources/SharedResources.kt

import shared.generated.resources.*
import org.jetbrains.compose.resources.getString
import kotlinx.coroutines.runBlocking

/**
 * Synchronous string access for Swift/UIKit code.
 * 
 * Note: runBlocking is acceptable here because string lookups are:
 * 1. Cached in memory after the first load.
 * 2. Reading from a bundled file (no I/O latency).
 * 3. Called on the main thread (which runBlocking on Main thread blocks, but
 *    for <1ms operations, this is imperceptible).
 */
object SharedStrings {
    fun appName(): String = runBlocking { getString(Res.string.app_name) }
    fun welcomeMessage(name: String): String = runBlocking { getString(Res.string.welcome_message, name) }
    fun itemCount(count: Int): String = runBlocking { getString(Res.string.item_count, count) }
    fun errorNetwork(): String = runBlocking { getString(Res.string.error_network) }
}
```

**In Swift:**
```swift
// SwiftUI — using shared strings from Kotlin
struct WelcomeView: View {
    let userName: String
    
    var body: some View {
        VStack {
            Text(SharedStrings.shared.appName())
                .font(.headline)
            Text(SharedStrings.shared.welcomeMessage(name: userName))
                .font(.title)
        }
    }
}
```

---

## 4. Localization Deep Dive

### How Locale Resolution Works

When `stringResource(Res.string.welcome_message)` is called:
1. CMP checks the device's current locale (e.g., `es-MX` for Mexican Spanish).
2. It looks for `values-es-rMX/strings.xml` (exact match).
3. If not found, it falls back to `values-es/strings.xml` (language match).
4. If not found, it falls back to `values/strings.xml` (default English).

### Locale Resolution Differences Between Platforms

| Behavior | Android | iOS |
|---|---|---|
| System locale API | `Locale.getDefault()` | `NSLocale.currentLocale` |
| Fallback chain | `es-MX` → `es` → default | `es-419` → `es` → default |
| Per-app language | ✅ (Android 13+ `LocaleManager`) | ✅ (iOS Settings → Language) |
| RTL auto-detection | ✅ (system handles) | ✅ (system handles) |

**Pitfall:** Android uses `es-rMX` for region variants (dash + lowercase r + uppercase region). Compose Resources follows this Android convention. If you name your folder `values-es-MX` (without the `r`), it won't be found.

### Testing Localization

```kotlin
// commonTest
@Test
fun `spanish strings exist for all keys`() = runTest {
    // Verify that no key is missing from the Spanish translation
    val englishKeys = listOf(
        Res.string.app_name,
        Res.string.welcome_message,
        Res.string.item_count,
        Res.string.error_network
    )
    
    englishKeys.forEach { key ->
        val spanishString = getString(key)  // Would use Spanish if device locale is set
        assertTrue(spanishString.isNotBlank(), "Missing Spanish translation for $key")
    }
}
```

---

## 5. Sharing Colors and Themes

Compose Resources does not yet have a built-in mechanism for sharing color definitions. You must define them in Kotlin:

```kotlin
// shared/src/commonMain/kotlin/com/example/design/AppColors.kt

import androidx.compose.ui.graphics.Color

object AppColors {
    // Brand colors
    val Primary = Color(0xFF6366F1)          // Indigo-500
    val PrimaryDark = Color(0xFF4F46E5)      // Indigo-600
    val Secondary = Color(0xFF06B6D4)        // Cyan-500
    val Accent = Color(0xFFF59E0B)           // Amber-500
    
    // Neutrals
    val Background = Color(0xFFF8FAFC)       // Slate-50
    val Surface = Color(0xFFFFFFFF)
    val OnSurface = Color(0xFF1E293B)        // Slate-800
    val OnSurfaceVariant = Color(0xFF64748B) // Slate-500
    
    // Semantic
    val Error = Color(0xFFEF4444)            // Red-500
    val Success = Color(0xFF22C55E)          // Green-500
    val Warning = Color(0xFFF59E0B)          // Amber-500
}

// For iOS native consumption (without Compose)
object AppColorsHex {
    const val PRIMARY = 0xFF6366F1
    const val PRIMARY_DARK = 0xFF4F46E5
    const val SECONDARY = 0xFF06B6D4
}
```

**In Swift (for native SwiftUI):**
```swift
extension Color {
    static let appPrimary = Color(
        red: Double((AppColorsHex.shared.PRIMARY >> 16) & 0xFF) / 255.0,
        green: Double((AppColorsHex.shared.PRIMARY >> 8) & 0xFF) / 255.0,
        blue: Double(AppColorsHex.shared.PRIMARY & 0xFF) / 255.0
    )
}
```

---

## Common Pitfalls

### 1. The SVG Misconception
Compose Resources does NOT support raw `.svg` files. It supports Android Vector Drawables (`.xml` with `<vector>` root). If you drop an `.svg` into `drawable/`, the build fails. Use Android Studio's "Import Vector Asset" to convert SVGs to Android Vector format.

### 2. The Font Loading Crash
If you reference a font that doesn't exist in `composeResources/font/`, the app crashes at runtime (not compile time) because font loading is asynchronous.

### 3. The `runBlocking` Warning
The `SharedStrings` wrapper uses `runBlocking` to make `suspend` functions synchronous. This is acceptable for small string lookups but dangerous for large resource files (e.g., loading a 5 MB image). For heavy resources, expose the `suspend` function directly and let Swift call it via SKIE's async bridge.

### 4. The Build Performance Impact
The Compose Resources Gradle plugin processes all files in `composeResources/` on every build. If you have 500+ drawables, this can add 5-10 seconds to incremental builds. Consider splitting resources into separate KMP modules (e.g., `:core:core-resources`).

---

## Probing Questions

1.  **Vector Drawable on iOS:** Explain how CMP's resource library parses an Android Vector Drawable (`.xml`) and renders it on iOS. What Skia API does it use? What happens if the vector uses an `<animated-vector>` element?
2.  **Locale Fallback:** Your app has `values/strings.xml` (English), `values-fr/strings.xml` (French), and `values-fr-rCA/strings.xml` (Canadian French). The user's device is set to `fr-BE` (Belgian French). Which strings file is loaded, and why?
3.  **Resource Packaging:** When `./gradlew :shared:assembleXCFramework` runs, where are the `composeResources/` files physically stored inside the `.xcframework`? How does the Kotlin code find them at runtime on iOS?
4.  **Performance:** Your shared `drawable/` folder has 200 Android Vector Drawables. On iOS, each one is parsed from XML to Skia path data on first use. Is this parsing cached? What's the performance impact of rendering 200 unique icons in a `LazyColumn`?
5.  **Design System Sync:** Your design team uses Figma. They export assets as SVGs. Your Android team converts them to Android Vector Drawables. Now the shared module uses Compose Resources. How do you automate the Figma → Android Vector → `composeResources/drawable/` pipeline?

## Further Reading

- [`compose-multiplatform.md`](compose-multiplatform.md) — How the UI layer consumes these resources via Skia.
- [`ios-distribution.md`](../tooling/ios-distribution.md) — How resource bytes are packaged into the `.xcframework`.
- [`build-system-and-source-sets.md`](../tooling/build-system-and-source-sets.md) — Configuring the Compose Resources Gradle plugin.
- [`../../mobile-system-design/localization-and-internationalization.md`](../../../mobile-system-design/localization-and-internationalization.md) — Large-scale localization strategy beyond string files.

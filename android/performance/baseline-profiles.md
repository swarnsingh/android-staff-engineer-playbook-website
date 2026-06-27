# Baseline Profiles

## Overview

A `Baseline Profile` is an incredibly powerful, Google-recommended performance optimization technique. It is a text file bundled with your APK that tells the Android Runtime (ART) exactly which classes and methods are required during app startup and critical user journeys.

A Staff Engineer understands that modern Android apps (especially those built with Jetpack Compose) suffer from massive "Cold Start" delays and initial scroll jank. By utilizing Baseline Profiles, you force the Android OS to pre-compile the heaviest parts of your app into raw Machine Code *before* the user ever opens the app for the first time, resulting in up to 40% faster startup times.

## Why It Matters

When a user downloads your app from the Play Store, the app is distributed as Dalvik Executable (DEX) bytecode. It is not raw machine code. 

When the user taps the app icon for the very first time, the Android Runtime (ART) has to read the bytecode, interpret it, and translate it into machine code on-the-fly (Just-In-Time or JIT compilation). This translation is highly CPU intensive. 

If you are using Jetpack Compose, the framework requires instantiating thousands of classes during the first frame to render the UI. If ART has to JIT compile all of those Compose classes during the first 500ms of startup, your app will hang on a blank screen, and the first few scrolls will drop massive amounts of frames (Jank).

Baseline Profiles eliminate this JIT overhead entirely.

## Historical Context

- **Android 4.4 (Dalvik):** Strictly JIT compilation. Apps were slow to start, but the installation was fast.
- **Android 5.0 (ART / AOT):** Google tried Ahead-Of-Time (AOT) compilation. When you downloaded an app, the OS spent 5 minutes compiling the *entire* APK into machine code. Apps started incredibly fast, but installs took forever, and the compiled app took up 3x the storage space.
- **Android 7.0 (Profile-Guided Optimization):** Google compromised. Apps install fast (bytecode). As the user uses the app, ART watches which methods are called frequently and writes a "Profile" to disk. While the phone charges overnight, ART uses that profile to AOT compile *only* the frequently used methods. The app gets faster over a few days.
- **Modern Era (Baseline Profiles):** Developers realized: "Why wait a few days for the user to generate a profile? I know exactly what methods are called during startup!" Google introduced Baseline Profiles so developers could ship a pre-made profile inside the APK. The OS reads it upon installation and AOT compiles the startup code immediately.

## First Principles

1.  **JIT (Just-In-Time):** Translating bytecode to machine code while the app is running. Slow startup, high CPU usage.
2.  **AOT (Ahead-Of-Time):** Translating bytecode to machine code *before* the app runs. Fast startup, lower CPU usage.
3.  **The Profile:** A list of critical classes and methods (e.g., `Lcom/example/MainActivity;->onCreate()V`).
4.  **Cloud Profiles:** Google Play aggregates the profiles of your actual users. However, this takes weeks of real-world usage to kick in. Baseline Profiles are shipped *with* the APK, guaranteeing performance on Day 1.

## Mental Model

Think of your app's codebase as a **Massive IKEA Furniture Manual (written in Swedish)**.
- **JIT Compilation:** The user opens the manual. They have to translate it from Swedish to English word-by-word as they build the furniture. It is incredibly slow and frustrating.
- **AOT (Android 5.0):** The delivery driver translates the entire 500-page manual in the driveway before handing you the box. Delivery takes hours, and you only actually needed the first 10 pages to build the chair.
- **Baseline Profiles:** You (the developer) know the user is building the chair first. You include an English translation of *only* the first 10 pages inside the box. The user builds the chair instantly. They can translate the rest later if they decide to build the matching table.

## Internal Mechanics

### How to Generate a Baseline Profile

You do not write a Baseline Profile manually. You use the `Macrobenchmark` library to generate it.

1.  Create a separate `benchmark` module in your project.
2.  Write a JUnit test that uses `BaselineProfileRule`.
3.  The test uses `UiAutomator` to launch your app, click a few buttons, and scroll your main feed.
4.  While the test runs, the OS records every single class and method that was executed.
5.  The test outputs a `baseline-prof.txt` file.
6.  You copy this file into your `app/src/main/` directory.

```kotlin
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {
    @get:Rule
    val baselineProfileRule = BaselineProfileRule()

    @Test
    fun generate() = baselineProfileRule.collect(
        packageName = "com.example.myapp",
        profileBlock = {
            // 1. Start the app (This records all startup classes)
            startActivityAndWait()
            
            // 2. Scroll the main list (This records all RecyclerView/Compose classes)
            val list = device.findObject(By.res("main_list"))
            list.setGestureMargin(device.displayWidth / 5)
            list.fling(Direction.DOWN)
        }
    )
}
```

When you build the Release APK, the Android Gradle Plugin bundles this `.txt` file into the binary.

### How the OS Uses It

When the user downloads your app from Google Play:
1. The `dex2oat` daemon wakes up.
2. It looks for the Baseline Profile in the APK.
3. It finds the 5,000 methods listed in the profile.
4. It AOT compiles those 5,000 methods into a `.odex` (Optimized DEX) machine code file.
5. When the user taps the app icon, the OS loads the `.odex` file directly into memory, entirely bypassing JIT interpretation for the startup path.

## Architecture

```mermaid
graph TD
    subgraph Developer Machine
        Test[Macrobenchmark Test] -->|Automates UI| Device[Test Device]
        Device -->|Records Methods| Txt[baseline-prof.txt]
        Txt -->|Bundled into| APK[Release APK]
    end
    
    subgraph User Device (Installation)
        APK --> Play[Google Play Install]
        Play --> OS[Android OS 'dex2oat']
        OS -->|AOT Compiles| ODEX[Optimized Machine Code]
    end
    
    subgraph User Device (App Launch)
        User[Taps App Icon] --> ODEX
        ODEX -->|Bypasses JIT| Fast[Instant Startup]
    end
```

## Production Example

**Jetpack Compose and Baseline Profiles**

Compose is heavily reliant on Baseline Profiles. Because Compose is unbundled from the Android OS (it ships inside your APK, not in the Android framework), the OS doesn't know how to render it natively. 

If you do not use Baseline Profiles in a Compose app, the JIT compiler will thrash the CPU attempting to compile the massive `androidx.compose` libraries during the first frame, resulting in dropped frames on the first scroll.

Google is so aware of this that they now ship default Baseline Profiles *inside* the Compose libraries themselves. However, these only cover the core Compose functions. They do not cover *your* specific `@Composable` UI code. You must generate your own app-specific profile to get the full 40% speed boost.

## Tradeoffs

**Maintenance Burden vs Speed**

- **Tradeoff:** The `baseline-prof.txt` file is highly specific to your source code. If you rename `MainActivity` to `HomeActivity` or radically change the startup UI, the Baseline Profile becomes stale. It will tell the OS to AOT compile methods that no longer exist, and miss the new methods.
- **The Staff Decision:** You cannot manually generate this file every sprint. A Staff Engineer automates this. You set up a GitHub Action or GitLab CI pipeline that runs the `Macrobenchmark` test on an emulator, generates the new `baseline-prof.txt`, and automatically commits it to the repository before every major release.

## Failure Modes

- **Testing on Debug Builds:**
  If you attempt to measure the startup speed of an app, or generate a Baseline Profile using a `Debug` build, the results are completely invalid. Debug builds disable AOT compilation and R8 optimizations. 
  *(Fix: You must strictly use the `benchmark` build type provided by the Macrobenchmark plugin, which perfectly mimics a `Release` build but keeps the profileable flags open).*
- **Over-Profiling:**
  Developers sometimes think: "If AOT compilation is fast, I'll just write a script that clicks every button in my app and profiles the entire codebase!" 
  If your Baseline Profile contains 100,000 methods, the app installation will take 3 minutes, and the resulting `.odex` file will consume hundreds of megabytes of the user's storage. 
  *(Fix: The Baseline Profile must be strictly limited to the "Cold Start" and the top 2-3 most critical "Scroll" journeys).*

## Staff Engineer Thinking

When optimizing Android performance, a Staff engineer looks for the highest ROI (Return on Investment).

1.  **Stop optimizing algorithms:** Junior engineers will spend 3 days rewriting a perfectly fine `for` loop to use `Sequence` to save 2 milliseconds on startup. I tell them to stop. Generating a Baseline Profile takes 2 hours to set up and will instantly shave **300 to 500 milliseconds** off the cold start time with zero code changes.
2.  **Verifying the Profile:** I don't just trust that the profile works. I use the `Macrobenchmark` library to write a `StartupTimingMetric` test. This test launches the app 10 times *without* the profile, then 10 times *with* the profile, and prints a statistical comparison to the console. If the median startup time doesn't drop by at least 15%, our profile is targeting the wrong classes.
3.  **Cloud Profiles Integration:** I ensure we are utilizing Play Developer API to monitor our aggregated cloud profiles. While our Baseline Profile covers Day 1, the Cloud Profile covers Day 30.

## Common Misconceptions

- **"Baseline Profiles replace R8 / ProGuard."** Absolutely false. R8 shrinks your APK by removing dead code. Baseline Profiles speed up your APK by pre-compiling code. They are completely independent and you must use both.
- **"If I update my app, the old Baseline Profile still works."** Not fully. The `dex2oat` compiler matches the exact method signatures. If you change the parameters of a function, the old profile signature is ignored, and that specific function falls back to JIT compilation.

## Probing Questions

1.  What is the fundamental difference between Just-In-Time (JIT) compilation and Ahead-Of-Time (AOT) compilation in the Android Runtime (ART)?
2.  Explain why Jetpack Compose applications are particularly vulnerable to "Cold Start" Jank if Baseline Profiles are not utilized.
3.  How did Google's approach to AOT compilation change between Android 5.0 (Lollipop) and modern Android versions regarding app installation times?
4.  Describe the automated process of generating a Baseline Profile. What library and tools do you use?
5.  Why is it an architectural mistake to try and profile every single screen and button in your application to create a massive Baseline Profile?
6.  If you rename a critical startup class in your application, what happens to the effectiveness of your existing Baseline Profile?
7.  Explain the concept of Cloud Profiles (Profile-Guided Optimization) and how they differ from the Baseline Profiles shipped inside the APK.
8.  Why must performance benchmarks and Baseline Profile generation strictly occur on Release-equivalent builds rather than Debug builds?
9.  What is the `dex2oat` daemon, and what is its specific role during the installation of an app with a Baseline Profile?
10. If a junior engineer wants to spend a week optimizing the sorting logic of a local database to improve app startup speed, how would you coach them regarding Return on Investment (ROI) and Baseline Profiles?

## Further Reading

- [`jank.md`](jank.md) — The visual stuttering that Baseline Profiles aim to eliminate during early app usage.
- [`app-size-and-r8.md`](app-size-and-r8.md) — The static optimization step that must run alongside Baseline Profiles.
- [Android Developers: Baseline Profiles](https://developer.android.com/topic/performance/baselineprofiles/overview)

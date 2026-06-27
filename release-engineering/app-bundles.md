# Release Engineering: App Bundles (.aab) & Dynamic Delivery

## The Prompt

*"Your E-Commerce app has grown to 150MB because it includes a 50MB Augmented Reality (AR) shoe-fitting feature. Users in emerging markets are refusing to download it over expensive cellular connections. Design a release architecture that reduces the initial download size to 20MB, without removing the AR feature from the codebase."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Reduce the initial install size of the application.
- Support downloading heavy features (like AR) only when the user explicitly requests them.
- Support different hardware configurations (CPU architectures, screen densities, languages).

### Non-Functional Requirements (NFRs)
- **App Size:** Must stay under Google Play's 150MB initial limit (though 20MB is the target).
- **Complexity:** The solution must not require building 50 different APKs manually in CI.

## 2. High-Level Architecture (Android App Bundles)

A Junior engineer tries to write a custom Bash script in CI that builds `apk-arm64-english.apk`, `apk-x86-spanish.apk`, etc. This creates dozens of files to manage and inevitably fails.
A Staff engineer uses the **Android App Bundle (.aab)** and **Dynamic Delivery**.

```mermaid
graph TD
    CI[CI Pipeline] -->|Builds .aab (150MB)| PlayConsole[Google Play Console]
    
    subgraph Google Play Server (Dynamic Generation)
        PlayConsole --> SplitEngine[APK Generation Engine]
        SplitEngine -->|Slices by ABI| ABI[arm64, x86]
        SplitEngine -->|Slices by DPI| DPI[hdpi, xxhdpi]
        SplitEngine -->|Slices by Lang| Lang[en, es, fr]
    end
    
    subgraph User A (Pixel 7, English)
        PlayStoreA[Play Store App] -->|Requests App| SplitEngine
        SplitEngine -->|Delivers Base + arm64 + xxhdpi + en| PhoneA[20MB Install]
    end
    
    subgraph User B (Samsung S8, Spanish)
        PlayStoreB[Play Store App] -->|Requests App| SplitEngine
        SplitEngine -->|Delivers Base + arm32 + hdpi + es| PhoneB[18MB Install]
    end
```

## 3. The Core Flows (Deep Dive)

### Flow 1: The Death of the 'Fat APK'
*Interviewer:* "Historically, an APK was 100MB. Why was it so big, and how does the `.aab` format mathematically reduce it?"

**Staff Answer:**
"The old 'Fat APK' contained *everything*. It had the C++ libraries for `arm64`, `arm32`, `x86`. It had image resources for `mdpi`, `hdpi`, `xxhdpi`. It had strings for 50 languages.
An Android App Bundle (`.aab`) is not an installable file. It is a publishing format. 
1. We upload the 150MB `.aab` to Google Play.
2. When a user with a Pixel 7 (English, `xxhdpi`, `arm64`) taps Install, Google Play dynamically generates a specialized set of **Split APKs**.
3. It creates a `Base APK` (the core code), plus a `Language APK` (English only), a `Density APK` (xxhdpi only), and an `ABI APK` (arm64 only).
4. The user's phone downloads these Split APKs. The Android OS installs them together as a single logical app.
The user never downloads the Spanish strings or the x86 binaries, dropping the download size from 150MB to 20MB automatically."

### Flow 2: Dynamic Feature Modules (On-Demand Delivery)
*Interviewer:* "The App Bundle solved the language and screen density problem. But the app is still 70MB because of the massive Augmented Reality (AR) C++ library. The user hasn't even clicked the AR button yet. How do we defer this?"

**Staff Answer:**
"We must refactor the app to use **Dynamic Feature Modules**.
1. We extract the AR feature into a separate Gradle module (`:features:ar`).
2. In the `AndroidManifest.xml` of that module, we declare `<dist:delivery><dist:on-demand/></dist:delivery>`.
3. When we build the `.aab`, Google Play knows this module is optional. It is *not* included in the initial install. The initial install size drops to 20MB.
4. When the user eventually taps 'Try AR Shoe Fitting', our code uses the `SplitInstallManager` SDK:
   `splitInstallManager.startInstall(request)`
5. The Play Store silently downloads the 50MB AR module in the background and injects it directly into the running app's ClassLoader. The user can then launch the AR screen."

### Flow 3: Google Play App Signing Dependency
*Interviewer:* "You try to build an App Bundle, but Google Play rejects it, saying you must enroll in Google Play App Signing first. Why are they linked?"

**Staff Answer:**
"Because Google Play is generating the Split APKs dynamically on their servers.
If we kept the App Signing Private Key on our local CI server, Google Play would have no way to cryptographically sign the dynamic `Language APK` or `ABI APK` it generates for the user.
By giving Google the App Signing Key (Google Play App Signing), they can build, sign, and deliver the Split APKs seamlessly on our behalf. `.aab` requires Play App Signing; they are mathematically codependent."

## 4. Failure Modes & Bottlenecks

### Bottleneck: Sideloading & Enterprise Distribution
*Interviewer:* "Your QA team in China cannot access the Google Play Store. You send them the `.aab` file via email. They cannot install it. The `adb install app.aab` command fails. How do you test it?"

**Staff Answer:**
"An `.aab` cannot be installed on an Android device. The OS does not understand the format.
To test an `.aab` locally or distribute it via an Enterprise MDM, we must use the **Bundletool** CLI.
1. We run `bundletool build-apks --bundle=app.aab --output=app.apks --ks=keystore.jks`.
2. This generates a `.apks` archive (a zip of all possible Split APKs).
3. We connect the test device via USB and run `bundletool install-apks --apks=app.apks`.
4. Bundletool interrogates the connected device, extracts the specific Split APKs it needs, and pushes them via ADB.
If we must email an installable file to QA, we must build a `Universal APK` (a legacy Fat APK) using bundletool, explicitly abandoning the size savings for that specific QA cycle."

### Bottleneck: Dynamic Feature Reflection Crashes
*Interviewer:* "You download the AR Dynamic Feature. You try to launch the `ArActivity`. The app crashes with `ClassNotFoundException`. Why?"

**Staff Answer:**
"When the core app starts, the AR module does not exist on disk.
If the core app tries to reference `ArActivity::class.java` statically, the Kotlin compiler will link it, and the app will crash instantly because the class isn't in the ClassLoader.
**The Fix:** Dynamic Features must be completely decoupled using **Reflection** or a **Dependency Injection Map**.
The core module defines an Interface `interface ArFeature`. The dynamic module implements it. When the dynamic module finishes downloading, we use reflection to instantiate the entry point: `Class.forName("com.app.ar.ArFeatureImpl").newInstance()`. We must never statically link the core module to the dynamic module."

## 5. Staff Engineer Thinking: The Asset Pack (Play Asset Delivery)

A Staff Engineer distinguishes between Code and Assets.
If the 50MB AR feature was mostly C++ code, Dynamic Feature Modules are correct.
If the 50MB feature was actually high-resolution 3D `.obj` models and textures (Assets), we shouldn't put them in the code bundle at all.
We use **Play Asset Delivery (PAD)**.
PAD allows you to package Gigabytes of assets (used heavily in Games, but applicable to AR) into an `.aab`. These assets are delivered seamlessly via the Play Store CDN, bypassing the strict 150MB code limit of the Android ecosystem, and avoiding the complex ClassLoader reflection logic required for Dynamic Code Modules.

## 6. Probing Questions (For Practice)

1.  Explain why an Android App Bundle (`.aab`) cannot be directly installed on an Android phone using standard `adb install`.
2.  Describe the concept of "Split APKs". How does Google Play dissect an `.aab` to create an optimized install for a Spanish-speaking user on a Pixel 7?
3.  Why does the adoption of the `.aab` format mandate that the developer also opts into Google Play App Signing?
4.  Walk through the architecture of a Dynamic Feature Module. How does the app request the module, and how does the OS inject it into a running process?
5.  Explain the `ClassNotFoundException` bottleneck when working with Dynamic Features. Why is Reflection or interface-based DI strictly required?
6.  How does a developer use `bundletool` to test an `.aab` on a physical device connected via USB?
7.  If a QA tester needs an installable file emailed to them (and they don't have bundletool), how do you generate a legacy "Universal APK" from the `.aab`?
8.  Describe the difference between Play Feature Delivery (Code) and Play Asset Delivery (Assets). When would you use one over the other?
9.  If a user has limited storage space, how can an app use the `SplitInstallManager` to explicitly uninstall a Dynamic Feature Module after the user is finished with it?
10. Why did the legacy "Fat APK" architecture severely punish developers who included native C++ libraries (NDK) in their applications?

## Further Reading

- [`code-signing.md`](code-signing.md) — The required architecture of Google Play App Signing.
- [`play-store-internals.md`](play-store-internals.md) — How the `.aab` interacts with the Play Store Tracks and Delta Patching.
- [`app-size-and-r8.md`](../android/performance/app-size-and-r8.md) — How code shrinking complements the `.aab` size reductions.

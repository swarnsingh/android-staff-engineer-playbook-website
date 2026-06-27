# Platform Design: Deep Links & App Links (Universal Links)

## The Prompt

*"Design the Deep Linking architecture for an E-Commerce application. When a user clicks `https://shop.com/shoes/123` in an email, the app must open directly to the Shoe Product Page. If the user does not have the app installed, it must route them to the Play Store, and upon installation, remember that they wanted to see 'Shoe 123' (Deferred Deep Linking)."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Standard Deep Linking (Custom URI Schemes).
- Android App Links (HTTP/HTTPS Universal Links).
- Deferred Deep Linking (Surviving the App Store installation gap).
- Navigation routing (opening the correct screen with the correct back-stack).

### Non-Functional Requirements (NFRs)
- **Security (Priority 0):** Prevent malicious apps from hijacking `shop.com` URLs to steal user credentials (Phishing).
- **UX Consistency:** When the user presses the 'Back' button after opening a deep link, they must not exit the app; they should go to the App's Home Screen.

## 2. High-Level Architecture (The Routing Pipeline)

A Junior engineer handles deep links by writing a massive `switch(intent.data)` statement in `MainActivity.onCreate()`.
A Staff engineer builds a **Centralized Routing Engine** mapped to the Navigation Graph, and utilizes cryptographic Verification (Digital Asset Links).

```mermaid
graph TD
    User[User Clicks Link in Email] --> OS[Android OS Intent System]
    
    subgraph Security Layer
        OS -->|Checks assetlinks.json| Verified[Verified App Link]
        Verified --> App[Mobile App]
    end
    
    subgraph Routing Engine (DeepLinkHandler)
        App --> Router[Central Router]
        Router -->|Extract Params| Graph[Navigation Graph]
        Graph -->|Synthesize Back-Stack| ProductScreen[Product Screen]
    end
    
    subgraph Deferred Flow (Branch / Firebase)
        Uninstalled[User doesn't have app] --> PlayStore[Google Play Store]
        PlayStore --> Install[App Installed]
        Install --> DeferredSDK[Deferred Link SDK]
        DeferredSDK --> Router
    end
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Android App Links vs Custom Schemes (Security)
*Interviewer:* "I register a custom scheme `<data android:scheme="shopapp" />`. Another malicious app on the phone also registers `shopapp://`. When the user clicks the link, the OS shows an 'Open With' dialog, and the user accidentally clicks the malicious app. How do you prevent this?"

**Staff Answer:**
"Custom schemes are insecure. Anyone can claim them. We must migrate to **Android App Links** (the equivalent of iOS Universal Links).
1. We declare support for standard HTTP/HTTPS URLs: `<data android:scheme="https" android:host="shop.com" />` and add `android:autoVerify="true"`.
2. When our app is installed, the Android OS automatically pings `https://shop.com/.well-known/assetlinks.json`.
3. This JSON file contains the SHA-256 fingerprint of our app's signing certificate.
4. The OS mathematically verifies that we own both the App and the Website.
5. Once verified, the OS *never* shows the 'Open With' disambiguation dialog. Clicks on `https://shop.com` are instantly and forcefully routed to our app, mathematically locking out malicious hijackers."

### Flow 2: Synthesizing the Back-Stack (Navigation)
*Interviewer:* "The user opens the deep link and goes straight to the 'Shoe 123' screen. They hit the Android system 'Back' button. The app closes completely and dumps them back into their Email app. This is terrible UX. How do you fix it?"

**Staff Answer:**
"We must synthesize an artificial **Back-Stack**.
If a user organically navigates to the Shoe screen, the stack is `Home -> Search -> Shoe`. 
When they deep link, the stack is just `Shoe`.
Using the Jetpack Navigation Component (or a custom Router), we define the hierarchy. When the deep link is intercepted, the Router does *not* just launch the `ShoeFragment`. It first launches the `HomeFragment`, suppresses the animation, and then pushes the `ShoeFragment` on top.
When the user hits 'Back', they pop the `ShoeFragment` and land gracefully on the `HomeFragment`, keeping them inside our ecosystem."

### Flow 3: Deferred Deep Linking (The App Store Gap)
*Interviewer:* "A user clicks your ad for 'Shoe 123', but they don't have the app. They go to the Play Store and install it. When the app opens, all intent data is gone. They land on the generic Home Screen. How do you preserve the intent across the installation gap?"

**Staff Answer:**
"The Android OS does not natively pass URLs through the Play Store installation process. We must use a **Deferred Deep Linking Provider** (like Branch.io or Firebase Dynamic Links).
1. The user clicks a Branch URL (`https://shop.app.link/shoe123`).
2. Branch's backend records a fingerprint of the user (IP Address, User Agent, Timestamp, Screen Size).
3. The user is redirected to the Play Store and installs the app.
4. On the first launch, the App initializes the Branch SDK.
5. The SDK sends the device fingerprint to the Branch backend.
6. Branch looks at its database, says 'Ah! This fingerprint matches a click from 2 minutes ago for Shoe 123!', and returns the URL to the app.
7. The App's Router parses the URL and opens the Shoe screen.
*(Note: Fingerprinting is increasingly restricted by Privacy laws like iOS ATT, so fallback mechanics to web-to-app banners are also necessary).*

## 4. Failure Modes & Bottlenecks

### Bottleneck: The Massive Switch Statement (Scalability)
A Junior developer puts `if (path == "/shoes") { ... } else if (path == "/cart") { ... }` in `MainActivity`. After 3 years, the file is 5,000 lines long, full of regex errors, and crashes frequently.

**Staff Answer:**
"Routing must be Declarative, not Imperative.
In modern Android (Jetpack Navigation or Compose Navigation), deep links are declared directly on the destination node in the graph:
```kotlin
composable(
    route = "shoe_detail/{shoeId}",
    deepLinks = listOf(navDeepLink { uriPattern = "https://shop.com/shoes/{shoeId}" })
) { backStackEntry ->
    ShoeScreen(id = backStackEntry.arguments?.getString("shoeId"))
}
```
The framework automatically parses the regex, extracts the `{shoeId}` variable, and routes the user. The centralized Router engine handles the delegation, keeping `MainActivity` completely clean."

### Bottleneck: The "Web-Only" Feature Crash
*Interviewer:* "Marketing sends out an email blast with `https://shop.com/new-feature`. The Android app intercepts `https://shop.com/*`. But the Android app hasn't built the 'new-feature' screen yet. The app intercepts the link, fails to parse it, and crashes or shows a blank screen."

**Staff Answer:**
"The app must have a **Web Fallback Mechanism**.
1. The Router intercepts the link.
2. It queries its internal Navigation Graph: 'Do I know how to handle `/new-feature`?'
3. The Graph returns `false`.
4. The Router MUST gracefully degrade. It opens an internal `WebViewActivity` (or Chrome Custom Tab) and passes the URL to it.
5. The user sees the mobile-web version of the 'new-feature' screen inside the app shell. The UX is preserved, and the app doesn't crash."

## 5. Staff Engineer Thinking: Security & Authentication

A Staff Engineer anticipates security exploits related to state changes.

*Exploit:* What if a malicious website embeds an iframe pointing to `https://shop.com/logout` or `https://shop.com/transfer?amount=100`? If the Android app aggressively intercepts these as deep links and executes them without user confirmation, it creates a Cross-Site Request Forgery (CSRF) vulnerability on mobile.

*Fix:* Deep links must **never** execute state-mutating actions (POST/PUT/DELETE equivalents) immediately upon opening. A deep link must only ever *navigate* the user to a UI screen. If the link is `shop.com/transfer`, the app opens the Transfer Screen, pre-fills the amount, but **requires the user to manually tap the 'Confirm' button**. 

## 6. Probing Questions (For Practice)

1.  Explain the security difference between a Custom URI Scheme (`shopapp://`) and an Android App Link (`https://shop.com`), focusing on the disambiguation dialog.
2.  Describe the cryptographic verification process of `assetlinks.json`. How does the Android OS prove that the app developer also owns the website?
3.  Walk through the problem of navigating "Back" after opening a deep link. How does synthesizing a back-stack prevent the app from unexpectedly closing?
4.  What is Deferred Deep Linking? Explain the concept of "Fingerprinting" used by providers like Branch.io to pass data through the Play Store installation gap.
5.  Why is a massive `switch/if-else` statement for URL parsing considered a technical debt bottleneck, and how do declarative Navigation Graphs solve it?
6.  Explain the "Web Fallback Mechanism." What must the Android app do if it intercepts a valid website URL but lacks the native code to render that specific feature?
7.  Describe the security vulnerability of executing state-mutating actions (like transferring money) directly from a parsed deep link. How must the UI handle this?
8.  How does the introduction of strict privacy frameworks (like Apple's ATT and Android's Privacy Sandbox) threaten the reliability of Deferred Deep Linking?
9.  If a user has multiple versions of your app installed (e.g., Production and Beta), how do Android App Links decide which app to open, and how can you configure the `assetlinks.json` to handle this?
10. Why should a mobile app heavily prefer Chrome Custom Tabs over a raw `WebView` when falling back to render web content?

## Further Reading

- [`security-and-privacy.md`](../mobile-system-design/security-and-privacy.md) — How CSRF vulnerabilities manifest on mobile.
- [`navigation.md`](../android/architecture/navigation.md) — The mechanics of Jetpack Navigation and Back-Stack synthesis.
- [`code-signing.md`](../release-engineering/code-signing.md) — Understanding the SHA-256 certificate fingerprints required for `assetlinks.json`.

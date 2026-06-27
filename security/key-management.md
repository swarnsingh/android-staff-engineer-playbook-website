# Security: Key Management & Secrets

## The Theory
Every mobile app requires secrets to function: API Keys for Google Maps, Client Secrets for OAuth, or symmetric keys for local database encryption.
The fundamental rule of mobile security is: **The client is in the hands of the enemy.** Any secret embedded in the APK binary, no matter how heavily obfuscated, can and will be extracted by a motivated attacker using reverse-engineering tools (JADX, Apktool, Frida).

## Staff-Level Application in Mobile

### 1. The Anti-Pattern: Hardcoding in Source
```kotlin
// NEVER DO THIS
const val STRIPE_SECRET_KEY = "sk_live_123456789"
```
Even if you use C++ (NDK) to hide the key in a compiled `.so` library, attackers simply use tools like IDA Pro or Ghidra to extract the strings from the binary. It slows them down by an hour; it does not stop them.

### 2. The Backend Proxy Pattern (The Only True Solution)
If a secret must remain absolutely secure (e.g., a backend database password, a paid API key where you are billed per request), **it cannot exist on the mobile device.**
-   **The Architecture:** The mobile app must never talk directly to the third-party service (e.g., OpenAI API, Stripe). The mobile app talks to *your* backend. Your backend authenticates the user, rate-limits them, and then attaches the Secret API Key to the request before forwarding it to the third party.
-   **Trade-off:** You must maintain a backend proxy server, introducing latency and operational costs.

### 3. Build-Time Secrets (BuildConfig)
For non-critical keys that *must* exist on the client (e.g., Google Maps API Key, Firebase App ID, Analytics tokens), they should not be committed to Git.
-   **The Flow:** Store the keys in a local `local.properties` file or inject them as Environment Variables via the CI/CD pipeline.
-   **Gradle Configuration:**
```groovy
// In build.gradle
buildTypes {
    release {
        buildConfigField "String", "MAPS_API_KEY", "\"${System.getenv("MAPS_KEY")}\""
    }
}
```
This prevents secrets from leaking if your GitHub repository is ever compromised, but remember: the key is still physically present in the final APK and can be extracted.

### 4. Dynamic Key Delivery
For keys that need to be rotated frequently (or keys for decrypting premium video content), the app should fetch them dynamically at runtime.
-   **The Flow:** The user logs in securely. The app requests a temporary encryption key from the backend over a TLS-encrypted connection. The app stores this key temporarily in RAM (or securely in the hardware Keystore) and discards it when the session ends.

## Common Pitfalls
-   **Committing `google-services.json`:** While Firebase explicitly states that the keys in this file are not strict "secrets" (they are identifiers), you must use Firebase Security Rules to lock down your database. A common junior mistake is leaving Firebase Realtime Database rules wide open and assuming the `google-services.json` key provides security.
-   **Secret Rotation Failure:** If you do hardcode an API key in your app, and it is compromised, you must rotate it on the backend. However, if you rotate the key, all older versions of your app currently installed on user devices will instantly break. You must design your system to support multiple active keys simultaneously to allow for graceful migration and forced updates.

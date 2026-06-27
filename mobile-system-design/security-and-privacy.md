# Security & Privacy (System Design NFRs)

## Overview

A Junior Engineer thinks security means adding an "S" to HTTP and hiding the API key in `strings.xml`.

A Staff Engineer assumes the physical device is already compromised. They assume the user is on a malicious Wi-Fi network, the device is rooted, and an attacker has full access to the file system. In Mobile System Design, **Security & Privacy** are not features; they are foundational Non-Functional Requirements (NFRs) that dictate how data rests, how data travels, and how the company avoids devastating GDPR/CCPA fines.

## Why It Matters

If you are asked to design a "Banking App" or a "Medical App", Security is the *only* NFR that truly matters.
- If you save an authentication token to `SharedPreferences` in plain text on a rooted device, another app can read it, steal the session, and drain the user's bank account.
- If you use standard HTTPS but fail to pin the certificate, a malicious Corporate Firewall can perform a Man-In-The-Middle (MITM) attack and intercept passwords.
- If you log the user's GPS coordinates to Firebase Analytics, you might violate the EU's GDPR laws, resulting in a fine of up to 4% of your company's global revenue.

## First Principles

1.  **Data at Rest:** Data physically written to the Android flash storage (SQLite, SharedPreferences, Files). It must be encrypted.
2.  **Data in Transit:** Data moving through the air to the cell tower or Wi-Fi router. It must be encrypted (TLS) and verified.
3.  **PII (Personally Identifiable Information):** Any data that can identify a specific human (Email, Phone, GPS, IP Address). It must be aggressively redacted from logs.
4.  **Hardware-Backed Security:** The Android Keystore (TEE/Secure Element). A physical chip on the phone that holds cryptographic keys. Even the Android OS cannot extract the private key from this chip.
5.  **Root / Jailbreak:** When a user intentionally breaks the OS Sandbox, giving all apps Administrator (`su`) access to the entire file system.

## Mental Model

Think of your app's data as **Cash in a Briefcase**.
- **Data in Transit:** You (the app) walking down the street to the Bank (Server). You don't use a clear plastic bag; you use a locked metal briefcase (HTTPS/TLS).
- **Certificate Pinning:** When you get to the Bank, you don't just hand the briefcase to anyone in a suit. You ask to see their specific Employee ID Badge to prove they actually work there.
- **Data at Rest:** When you get home, you don't leave the briefcase on the kitchen counter (Plaintext SQLite). You put it in a massive steel safe bolted to the floor (Encrypted Local Storage).
- **Android Keystore:** The combination to that safe is locked inside a titanium puzzle box (The Keystore Chip) that even you cannot open; you can only ask the box to lock or unlock things for you.

## Internal Mechanics

### 1. Securing Data at Rest (The Keystore)

Never save sensitive data in plain text.
```kotlin
// DANGEROUS: Anyone with a rooted phone can read this XML file.
sharedPreferences.edit().putString("auth_token", "secret_123").apply()
```

A Staff Engineer uses `EncryptedSharedPreferences` (part of AndroidX Security).
Under the hood, this library:
1. Generates a random AES-256 Symmetric Key.
2. Uses that AES key to encrypt the data.
3. Takes the AES key, and encrypts it using an RSA Asymmetric Master Key that lives inside the physical **Android Keystore** hardware chip.
4. Saves the encrypted AES key and the encrypted data to disk.

Even if an attacker rips the flash storage out of the phone, they cannot decrypt the data because the Master Key is permanently fused into the separate Keystore chip.

*(For massive databases, use `SQLCipher` which operates on the same principles for Room/SQLite).*

### 2. Securing Data in Transit (Certificate Pinning)

HTTPS encrypts the data. But how do you know you are talking to `api.yourbank.com` and not a hacker router pretending to be your bank?

The OS checks the server's TLS Certificate against a list of hundreds of "Trusted Root Certificate Authorities (CAs)" pre-installed on the phone. If a hacker compromises *just one* of those CAs, or if a user installs a malicious profile, the hacker can intercept your HTTPS traffic (Man-In-The-Middle).

**Certificate Pinning** solves this. The app hardcodes the exact cryptographic hash of the server's certificate.

```kotlin
// OkHttp Certificate Pinning
val certificatePinner = CertificatePinner.Builder()
    .add("api.yourbank.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .build()

val client = OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()
```

If the hashes don't match, `OkHttp` instantly severs the connection, protecting the user.

### 3. Biometric Authentication

To prove the human holding the phone is the owner, you use `BiometricPrompt` (Fingerprint / FaceID).

Crucially, a Staff Engineer knows you do *not* just ask the OS "Is this the user?" (a boolean response can be hacked on a rooted device). Instead, you ask the OS to **Unlock a Cryptographic Key**.
When the user successfully authenticates via fingerprint, the hardware Keystore unlocks a specific private key. You use that key to decrypt the authentication token. If the biometric prompt is bypassed by a hacker, they still don't have the decrypted token, so the app remains secure.

## Tradeoffs

**Certificate Pinning vs Operational Agility**

- **Certificate Pinning:**
    - *Pros:* Absolute protection against MITM attacks. Mandatory for banking apps.
    - *Cons:* If the backend DevOps team accidentally rotates the server's TLS certificate without coordinating with the Mobile team, **every single Android app in the world will instantly crash and go offline.** The app is permanently bricked until the user updates from the Play Store.

*Staff Decision:* You never pin to the "Leaf" (the final certificate). You pin to the Intermediate CA or the Root CA. You also mandate the implementation of "Backup Pins" in the code, so if the primary cert expires, the app gracefully falls back to the new one.

## Failure Modes

- **The APM Leak (PII Violation):**
  A developer writes `Timber.d("Login failed for user: ${user.email}")`. This log is uploaded to Firebase Crashlytics or New Relic.
  *(Failure: You have just violated GDPR. You leaked Personally Identifiable Information into a 3rd party database. You must now purge the entire Crashlytics index, and notify your legal department. Fix: Mandate strict Lint rules banning PII logging).*
- **The Clipboard Attack:**
  Users copy their 2FA codes or passwords. Android 12+ shows a toast when an app accesses the clipboard. Malicious background apps constantly poll the clipboard to steal passwords.
  *(Fix: If your app generates sensitive data (like a crypto recovery phrase), you must use the `ClipData.newPlainText()` API and flag it as sensitive so the OS hides it from other apps).*
- **Screen Recording / Screenshot Stealing:**
  Malicious apps can take screenshots of your app while it is in the background, stealing account balances or messages.
  *(Fix: For highly sensitive screens, set `WindowManager.LayoutParams.FLAG_SECURE`. This physically turns the screen black if a screenshot is taken or if the screen is recorded).*

## Staff Engineer Thinking

When reviewing an architecture for Security, a Staff engineer adopts an adversarial mindset (Red Teaming).

1.  **Assume the Device is Hostile:** I do not trust the Android OS. I assume the device is rooted. I assume `SharedPreferences` is a public bulletin board. Therefore, I mandate `EncryptedSharedPreferences` and `SQLCipher` for all session data.
2.  **Stateless Backends:** I advocate for JWTs (JSON Web Tokens) with very short lifespans (e.g., 15 minutes). If a token is stolen from the device, it becomes useless quickly. The app uses a long-lived, securely encrypted Refresh Token to silently fetch new JWTs in the background.
3.  **App Attestation (Play Integrity API):** For high-security endpoints (e.g., transferring money), I integrate the Play Integrity API. Before the backend executes the transfer, the Android app asks Google Play for a cryptographic token proving that: 1. The app is a genuine binary installed from the Play Store (not a modded APK), and 2. The Android OS is pristine (not rooted). The backend verifies this token before moving the money.

## Common Misconceptions

- **"Base64 is encryption."** Terrifyingly false. Base64 is *encoding*. It takes 2 seconds to decode. It provides zero security.
- **"ProGuard / R8 hides my API keys."** False. ProGuard shrinks and obfuscates class names (`UserRepository` becomes `a.b.c`). It does *not* encrypt String literals. Anyone can decompile your APK using `apktool` and extract your API keys via `grep`. Never put secret keys (like an AWS secret or a Stripe secret) in the Android app. The Mobile App only holds public keys; secrets live on your Backend.

## Probing Questions

1.  Explain the architectural difference between saving an API key in `SharedPreferences` versus `EncryptedSharedPreferences` on a rooted Android device.
2.  What is a Man-In-The-Middle (MITM) attack, and how does Certificate Pinning prevent it?
3.  Describe the catastrophic failure mode of Certificate Pinning if the backend team rotates the server's TLS certificate without coordinating with the mobile team.
4.  Why is relying on the boolean result of a `BiometricPrompt` (e.g., `if (success)`) inherently insecure on a compromised device, and what is the cryptographic alternative?
5.  What is Personally Identifiable Information (PII), and how does accidentally logging it to an APM tool violate GDPR/CCPA regulations?
6.  Explain the purpose of `WindowManager.LayoutParams.FLAG_SECURE` in the context of banking or medical applications.
7.  Why is it an architectural failure to bundle a private backend secret key (e.g., an AWS Secret Access Key) directly into the Android APK, even if the code is obfuscated by R8?
8.  Describe how a Staff Engineer utilizes the Google Play Integrity API to prove to a backend server that the Android device has not been rooted or compromised.
9.  How does an attacker utilize the Android Clipboard to steal user data, and how can an application defend against it?
10. Explain the role of the physical Android Keystore (Trusted Execution Environment) in encrypting local SQLite databases via `SQLCipher`.

## Further Reading

- [`security-and-keystore.md`](../android/networking-and-security/security-and-keystore.md) — Deep dive into the physical hardware chip (TEE) that enables this security.
- [`non-functional-requirements.md`](non-functional-requirements.md) — The framework that dictates Security as a core design constraint.
- [`crash-monitoring.md`](../android/observability/crash-monitoring.md) — How APM tools can accidentally leak PII if not tightly controlled.

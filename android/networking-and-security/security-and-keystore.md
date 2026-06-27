# Security and the Android Keystore

## Overview

A Staff Engineer assumes that the client (the Android device) is fundamentally compromised. 

If an attacker has physical access to an unlocked Android phone, or if the phone is rooted, they can extract the app's APK, reverse-engineer the source code, read the SQLite databases, and intercept the network traffic.

Android Security revolves around protecting the user's most sensitive data (Authentication Tokens, PII, Financial data) from these attacks. The primary weapon in our arsenal is the **Android Keystore System** and the `EncryptedSharedPreferences` / `EncryptedFile` wrapper libraries provided by Jetpack Security (Tink).

## Why It Matters

Junior developers often store OAuth Bearer tokens or User Passwords in standard `SharedPreferences` or a `Room` database. 

If a user roots their device, or if a malicious app manages to exploit a privilege escalation bug in the OS, they can navigate to `/data/data/com.your.app/shared_prefs/` and read the Bearer token in plain text. They can then clone that token to their own machine and impersonate the user indefinitely.

If you encrypt the token using a key hardcoded in your Kotlin source code, an attacker will simply decompile the APK using `jadx`, find the hardcoded key, and decrypt the token. 

True security requires Hardware-Backed encryption.

## Historical Context

- **Pre-Android 6.0:** The Android Keystore was software-based. It was better than nothing, but if the OS was compromised, the keys could be extracted from RAM.
- **Android 6.0 (Marshmallow):** Google introduced mandatory **Hardware-Backed Keystore**. The cryptographic keys are generated and stored inside a dedicated hardware chip (the Trusted Execution Environment - TEE, or the Secure Element - SE). The Android OS *never* sees the raw key material.
- **Android 10:** Introduced Jetpack Security (Crypto). A wrapper around the Google Tink library that made it trivially easy to use the Keystore for encrypting files and SharedPreferences without writing 500 lines of complex `Cipher` and `IvParameterSpec` boilerplate.

## First Principles

1.  **The Android Keystore:** A container for cryptographic keys. You ask the Keystore to generate a key (e.g., AES256). The key is generated *inside* the hardware chip. 
2.  **Hardware-Backed Encryption:** If you want to encrypt a token, you send the plaintext token into the hardware chip. The chip encrypts it using the secret key and returns the ciphertext. **The secret key never leaves the chip.** It is physically impossible to extract the key, even on a rooted device.
3.  **EncryptedSharedPreferences:** A wrapper that uses the Keystore. It generates a Master Key in the hardware chip, uses that Master Key to encrypt Data Encryption Keys (DEKs), and uses DEKs to encrypt your SharedPreferences XML file.

## Mental Model

Think of standard encryption as a **Lockbox with a Key on the Table**.
- You put your diary in the lockbox and lock it.
- You hide the key under your mattress (hardcoding the key in the app).
- A thief (hacker) breaks in, flips the mattress, finds the key, and opens the lockbox.

Think of the Android Keystore as a **Bank Vault with a Teller**.
- You cannot enter the vault. You cannot see the keys.
- You hand the Teller your diary. The Teller takes it into the vault, locks it in a box, and hands you the locked box.
- To read it, you hand the locked box back to the Teller. The Teller unlocks it inside the vault and hands you the diary.
- Even if a thief holds the Teller at gunpoint (roots the phone), the vault door (the hardware chip) physically cannot be forced to eject the raw keys.

## Internal Mechanics

### 1. Jetpack Security (The Modern Approach)

```kotlin
// 1. Generate or retrieve the Master Key from the Hardware Keystore
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

// 2. Create the EncryptedSharedPreferences instance
val sharedPreferences = EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey, // Powered by the hardware chip
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

// 3. Use it like normal!
sharedPreferences.edit().putString("auth_token", "super_secret_token").apply()
```
*Note: Under the hood, this XML file on disk now looks like complete gibberish. Even the Keys (like "auth_token") are deterministically encrypted.*

### 2. Biometric Prompt (Tying Keys to the User)

For extreme security (Banking apps), you can tell the Keystore: "Only allow this key to be used if the user proves who they are right now."

```kotlin
val keyGenParameterSpec = KeyGenParameterSpec.Builder(
    "my_bank_key",
    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
)
.setBlockModes(KeyProperties.BLOCK_MODE_GCM)
.setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
// CRITICAL: The chip will refuse to encrypt/decrypt without a fingerprint!
.setUserAuthenticationRequired(true) 
.build()
```
When you try to use this key, the `Cipher` object will throw a `UserNotAuthenticatedException`. You must catch this, launch the `BiometricPrompt` UI, and pass the `Cipher` into a `CryptoObject`. Only upon successful fingerprint read will the OS "unlock" the `Cipher` for one-time use.

## Architecture

```mermaid
graph TD
    subgraph Your App (Compromised OS)
        App[Auth Repository]
        Prefs[EncryptedSharedPreferences]
        Disk[(XML File on Disk)]
    end
    
    subgraph Secure Hardware (TEE / StrongBox)
        Chip[Crypto Chip]
        Key[Master Key AES256]
    end
    
    App -->|Save 'my_token'| Prefs
    Prefs -->|Encrypt 'my_token'| Chip
    Chip -.->|Uses internally| Key
    Chip -->|Returns '0xFA39B...'| Prefs
    Prefs -->|Saves gibberish| Disk
```

## Production Example

**Certificate Pinning (Network Security)**

Encryption on disk is useless if an attacker intercepts the data in transit. Standard HTTPS relies on the OS's list of "Trusted Root Certificates." If an attacker installs a malicious Root Certificate on the user's phone (e.g., using Charles Proxy), they can perform a Man-In-The-Middle (MITM) attack and read your HTTPS traffic in plain text.

To defeat this, we use Certificate Pinning in `OkHttp`. We hardcode the cryptographic hash (Pin) of our specific server's certificate into the app.

```kotlin
// In your DI Network Module
val certificatePinner = CertificatePinner.Builder()
    .add("api.mybank.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .build()

val okHttpClient = OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()
```
If OkHttp connects to `api.mybank.com` and the server's certificate does not perfectly match the hardcoded SHA-256 hash, OkHttp instantly drops the connection. Charles Proxy is defeated.

## Tradeoffs

**EncryptedSharedPreferences vs DataStore**

- **EncryptedSharedPreferences:**
    - *Pros:* Trivially easy to encrypt data. Officially supported by Google via Jetpack Security.
    - *Cons:* Inherits all the performance and ANR flaws of legacy `SharedPreferences`. Blocking I/O.
- **DataStore:**
    - *Pros:* Asynchronous, Coroutine-powered, totally safe from ANRs.
    - *Cons:* Google has not yet released an official "EncryptedDataStore" wrapper.
- **The Staff Compromise:** You must build a custom `Serializer` for Proto DataStore or Preferences DataStore that manually calls the Tink library to encrypt/decrypt the raw byte streams before they hit the disk. Alternatively, use `EncryptedSharedPreferences` strictly for the 2-3 highly sensitive tokens, and standard `DataStore` for the rest of the app's settings.

## Failure Modes

- **The Hardcoded Key Fallacy:**
  Junior developers often try to build their own AES encryption, hardcoding the secret key as a `private const val SECRET = "1234"` or putting it in `gradle.properties` (which just injects it into the `BuildConfig.java`).
  *(Fix: Any string compiled into the app can be extracted in 5 seconds using `jadx` or `strings` command. Never hardcode keys. Use the Keystore).*
- **Certificate Pinning Lockout:**
  If you implement Certificate Pinning and your backend team updates the server's SSL certificate (they usually expire every 1-2 years), your app will instantly refuse to connect to the server. Every single user is locked out until they update the app from the Play Store.
  *(Fix: Always pin the "Backup" certificate alongside the active one. Ensure the DevOps team is heavily coordinated with the Mobile team).*
- **Keystore Invalidation on Lock Screen Change:**
  If you use keys that are tied to device authentication (`setUserAuthenticationRequired(true)`), and the user goes into Android Settings and removes their PIN code or Fingerprint, the hardware chip instantly **permanently deletes** your cryptographic keys for safety.
  *(Fix: Your app must catch the `KeyPermanentlyInvalidatedException`, force the user to log out, clear the local database, and ask them to log in again).*

## Staff Engineer Thinking

When reviewing security PRs, a Staff engineer focuses on attack vectors and blast radius:

1.  **Do we actually need to store this?** The most secure data is data that doesn't exist. If the app stores a Credit Card number locally, I reject the PR. We should only store a Stripe Token.
2.  **Root Detection:** While we can use tools like Google Play Integrity API (formerly SafetyNet) to check if a device is rooted, I remind the team that root detection is a cat-and-mouse game. We must assume the device is rooted and ensure our Keystore implementation relies on Hardware-Backed security, which protects keys even from the root user.
3.  **ProGuard / R8 Obfuscation:** I ensure R8 is enabled in release builds. While it is not true security (it's obscurity), obfuscating class names from `AuthManager` to `a.b.c` slows down script-kiddie attackers significantly.

## Common Misconceptions

- **"HTTPS keeps my API traffic completely safe."** It keeps it safe from hackers on public Wi-Fi. It does *not* keep it safe from the owner of the device if they install a custom Root CA (like Charles Proxy). To protect against the user intercepting their own traffic, you must use Certificate Pinning.
- **"I can hide my API Keys in the NDK (C++ code)."** Putting your Google Maps API key in a `.cpp` file and using JNI to read it is slightly harder to reverse engineer than Java bytecode, but a competent attacker will extract it using Ghidra or IDA Pro in 10 minutes. It is obscurity, not security.

## Probing Questions

1.  What was the critical architectural flaw of storing sensitive tokens in `SharedPreferences` prior to the introduction of Jetpack Security?
2.  Explain the concept of Hardware-Backed Keystore. Why is it impossible for a rooted device to extract the raw cryptographic keys?
3.  If an attacker decompiles your APK using `jadx`, why is it trivial for them to bypass any custom encryption algorithm you wrote if you didn't use the Keystore?
4.  Describe how `EncryptedSharedPreferences` utilizes the "Master Key" pattern to encrypt the underlying XML file.
5.  What is a Man-In-The-Middle (MITM) attack, and how does installing a custom Root CA on an Android device enable it?
6.  How does OkHttp's Certificate Pinning specifically defeat Charles Proxy or other MITM debugging tools?
7.  What catastrophic application failure occurs if you implement Certificate Pinning but fail to coordinate with your DevOps team when the server's SSL certificate is renewed?
8.  Explain what happens to Keystore keys configured with `setUserAuthenticationRequired(true)` if the user removes their PIN code from the Android OS settings.
9.  Why is attempting to hide an API key inside C++ (NDK) code considered "security by obscurity" rather than true security?
10. Describe the architectural tradeoff of using `EncryptedSharedPreferences` versus attempting to manually encrypt a Kotlin `DataStore` implementation.

## Further Reading

- [`retrofit-and-okhttp.md`](retrofit-and-okhttp.md) — The network client where Certificate Pinning is implemented.
- [`datastore.md`](../../mobile-system-design/caching-library.md) — The asynchronous data storage solution that currently lacks a built-in Jetpack Security wrapper.
- [Android Developers: Security Best Practices](https://developer.android.com/topic/security/best-practices)

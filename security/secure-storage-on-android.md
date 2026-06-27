# Security: Secure Storage on Android

## The Theory
Android's file system is isolated by default (Sandboxing). App A cannot read App B's files. However, this software-level protection is completely bypassed if the device is rooted. To protect sensitive data (API Tokens, PII, Cryptographic Keys) from malware with root access, Android relies on Hardware-Backed Security (the Android Keystore system and the Trusted Execution Environment / TEE).

## Staff-Level Application in Mobile

### 1. The Android Keystore (The Vault)
The Keystore is not a database. It is a cryptographic vault. You do not store your JWT string in the Keystore. You store a **Cryptographic Key** in the Keystore, and you use that Key to encrypt your JWT, storing the encrypted ciphertext in normal `SharedPreferences` or Room.
-   **Hardware-Backed:** On modern devices, the Keystore generates and stores keys inside a dedicated security chip (the Secure Element or TEE). The raw key material *never* enters the Android OS memory (RAM).
-   **Execution:** When you ask the Keystore to encrypt a string, the OS sends the plaintext into the hardware chip, the chip performs the math, and the chip returns the ciphertext. A rooted OS can steal the ciphertext, but it cannot steal the Key.

### 2. EncryptedSharedPreferences (Jetpack Security)
Writing raw Keystore cipher logic is incredibly error-prone (managing Initialization Vectors (IVs), padding, and block modes).
Google provides `EncryptedSharedPreferences` via the Jetpack Security library (`androidx.security:security-crypto`).
-   **How it works:** It automatically generates a Master Key in the Android Keystore (AES256-GCM). It uses this Master Key to encrypt both the keys and the values before writing them to the standard XML `SharedPreferences` file on disk.
-   **Usage:** Use this for storing Session Tokens, OAuth Refresh Tokens, and sensitive PII settings. It acts exactly like standard `SharedPreferences` for the developer, abstracting away all cryptographic complexity.

### 3. Key Attestation (Proving the Hardware)
How does your Backend know that the API request came from a genuine Samsung Galaxy S23, and not from a Python script running on a hacker's laptop?
-   **The Flow:** The mobile app generates a keypair (Public/Private) in the Android Keystore and requests an **Attestation Certificate**.
-   This certificate is cryptographically signed by Google's root certificate baked into the hardware at the factory.
-   The mobile app sends the Public Key and the Attestation Certificate to the Backend.
-   The Backend verifies the Google signature. If valid, the Backend *knows* mathematically that the Private Key is securely locked inside genuine Android hardware and that the device's bootloader is locked (not rooted).

## Common Pitfalls
-   **Hardcoding Keys in Source Code:** Storing `const val API_KEY = "12345"` in your Kotlin code is useless. Attackers simply decompile the APK using `jadx`, open the `.smali` files, and copy the string. Use the Keystore to generate keys dynamically on the device.
-   **Failing to handle `KeyPermanentlyInvalidatedException`:** If a Key in the Keystore is configured to require Biometric authentication, and the user adds a new fingerprint to their phone's OS settings, Android will instantly invalidate the Key. Your app must catch this exception, force the user to log in again with their password, and generate a new key.
-   **Performance Overheads:** `EncryptedSharedPreferences` is much slower than standard `SharedPreferences` because it must decrypt the data on every read. Do not use it to store high-frequency, non-sensitive data (like the user's selected theme color).

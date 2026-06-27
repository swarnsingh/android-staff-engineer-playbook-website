# Blueprint: The Banking App (FinTech)

## 1. Architectural Signature
A Banking App (e.g., Chase, Monzo, Revolut) is optimized for **Absolute Security, Regulatory Compliance, and Zero Trust**.
The architecture assumes the device is hostile (rooted, malware-infected, intercepted network). Caching is treated as a liability, not a feature. Offline support is actively disabled for core flows to prevent stale financial data.

**Core Trade-off:** Security & Zero Trust > Offline Capabilities & Caching.

## 2. Component Blueprint

### Presentation Layer (The Secure Enclave)
- **Framework:** Compose or Views, but heavily restricted.
- **Window Flags:** `FLAG_SECURE` is applied to all Activities to prevent screenshots and screen recording by malware or the OS Recent Apps screen.
- **Session Timeout:** A strict, global inactivity timer (e.g., 5 minutes) running at the Application level. If triggered, the UI stack is instantly popped to the Login screen.
- **Biometrics Prompt:** Deeply integrated into the UI flow for step-up authentication before executing sensitive actions (e.g., transferring money).

### Domain Layer (The Cryptographer)
- **Token Manager:** Manages the Two-Token architecture (short-lived stateless JWT, long-lived Refresh Token).
- **Certificate Pinner:** A dedicated security module that validates the backend's SSL certificate hash against a hardcoded list to prevent Man-In-The-Middle (MITM) attacks.
- **Root/Tamper Detection:** Runs on app startup to verify the OS integrity (SafetyNet / Play Integrity API) and check for rooting (Magisk) or hooking frameworks (Xposed/Frida).

### Data Layer (The Ephemeral Network)
- **Local Persistence (Banned for PII):** Room (SQLite) is generally *banned* for storing Personally Identifiable Information (PII) or Account Balances. 
- **Encrypted Storage:** If caching is legally required or absolutely necessary for UX, it must use `EncryptedSharedPreferences` or SQLCipher, with the symmetric key stored in the hardware-backed Android Keystore.
- **Network Strategy:** **Pessimistic & Synchronous**. When transferring money, the app must wait for the HTTP 200 OK. No optimistic UI updates. No background queueing.

## 3. Infrastructure & DevOps
- **Release Cadence:** Governed by compliance. Often requires manual security audits or penetration testing before submission.
- **Obfuscation:** R8 is configured aggressively. Beyond R8, commercial obfuscators (DexGuard, Promon) are used to encrypt strings, hide API endpoints, and mutate the control flow to slow down reverse engineering.
- **Force Updates:** A non-negotiable mechanism to brick older versions of the app instantly if a security vulnerability is discovered in the client.

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The JWT Expiration Race Condition
*Problem:* The 5-minute Access Token expires. The user taps a button that triggers 5 concurrent API requests (e.g., loading Dashboard, Transactions, and Cards). All 5 fail with HTTP 401. The app fires 5 simultaneous requests to the `/refresh` endpoint, causing the backend to invalidate the session due to a replay attack.
*Solution:* **The Authenticator Mutex**. Implement an OkHttp `Authenticator`. When the first 401 arrives, it acquires a Kotlin `Mutex`. The other 4 requests hit the Mutex and suspend. The first request refreshes the token, saves it securely, and releases the Mutex. The 4 suspended requests wake up, attach the *new* token, and retry safely.

### Bottleneck 2: Compromised Device Trust
*Problem:* A user installs malware outside the Play Store. The malware requests Accessibility Services, granting it the ability to read the screen and click buttons on behalf of the user, draining their bank account (Overlay Attack).
*Solution:* **Accessibility Whitelisting & Play Integrity**.
1. The app queries the OS for active Accessibility Services. If a non-system service is active, the app blocks the transfer.
2. The app calls the Google Play Integrity API. Google's servers cryptographically attest if the device is rooted or the app binary was modified. The backend refuses transactions if the attestation fails.

### Bottleneck 3: Biometric Downgrade Attacks
*Problem:* The app supports fingerprint login. A hacker steals the phone, bypasses the lock screen with the user's PIN, disables fingerprint, and the app gracefully falls back to asking for the password (which the hacker also stole).
*Solution:* **Cryptographic Biometrics (KeyStore Binding)**. We do not rely on the boolean result `BiometricPrompt.authenticate() == true`. Instead, we generate a Private Key in the Android Keystore bound to `setUserAuthenticationRequired(true)`. The backend sends a challenge. Only a valid biometric scan can unlock the hardware Keystore to sign the challenge. If the fingerprint is disabled, the Private Key is cryptographically wiped by the OS.

## 5. Summary of Technologies
- **UI:** Compose, `FLAG_SECURE`.
- **Data:** OkHttp (CertificatePinner, Authenticator), EncryptedSharedPreferences, SQLCipher.
- **Security:** Android Keystore, Play Integrity API, BiometricPrompt (CryptoObject).
- **Build:** R8, DexGuard, strict code-signing pipelines.

## Further Reading
- [`authentication.md`](../mobile-system-design/authentication.md) (Deep dive into JWT and Keystore).
- [`security-and-privacy.md`](../mobile-system-design/security-and-privacy.md) (Deep dive into MITM and Certificate Pinning).

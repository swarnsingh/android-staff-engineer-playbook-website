# Security: App & Device Attestation (Play Integrity)

## The Theory
Mobile apps operate in a zero-trust environment. When a backend server receives an API request stating "Transfer $500", it can verify the user's identity (via JWT), but how does it verify the *integrity of the client* making the request?
-   Did the request come from your official app downloaded from the Play Store, or a modified APK downloaded from a piracy site?
-   Is the Android device genuine hardware, or a headless emulator running on a server farm generating fake ad clicks?
-   Is the device rooted, exposing the app's memory to scraping tools?

Attestation is the cryptographic proof of the environment's integrity.

## Staff-Level Application in Mobile

### 1. The Play Integrity API (Formerly SafetyNet)
Google provides the Play Integrity API to answer the questions above. It is a closed-loop cryptographic system.
-   **The Flow:**
    1. The mobile app requests a Nonce (a random, single-use string) from your Backend.
    2. The mobile app passes the Nonce to the Play Integrity SDK (`IntegrityManager`).
    3. The SDK communicates securely with Google Play Services (and the hardware TEE).
    4. Google generates an encrypted **Integrity Token** containing the results of the environment check, bound to the Nonce.
    5. The mobile app sends this Token back to your Backend.
    6. Your Backend decrypts the Token (either locally using a shared secret or by querying Google's servers) and inspects the payload.

### 2. The Attestation Payload Verdicts
The decrypted payload provides three critical verdicts. Your Backend decides whether to accept or reject the API request based on these.
-   **`MEETS_BASIC_INTEGRITY`:** The device passes basic checks (e.g., it's not a known emulator). However, it might be rooted or running a custom ROM.
-   **`MEETS_DEVICE_INTEGRITY`:** The device is powered by genuine Android hardware and passes system integrity checks (CTS). The bootloader is locked.
-   **`MEETS_STRONG_INTEGRITY`:** The strongest guarantee. The device supports hardware-backed keystore attestation and has passed all system integrity checks.

### 3. App Identity Verdict
The payload also verifies the binary itself.
-   **`PLAY_RECOGNIZED`:** The APK's signing certificate exactly matches the one you registered in the Play Console. If a hacker decompiles your app, removes the Ads SDK, recompiles it, and signs it with their own key, this verdict will fail. The Backend should instantly ban the account or drop the request.

## Common Pitfalls
-   **Client-Side Evaluation:** A junior mistake is evaluating the Integrity Token on the mobile device (e.g., `if (token.meetsDeviceIntegrity()) { allowLogin() }`). If the device is rooted, an attacker using Xposed or Frida can simply hook that function and force it to return `true`. **Attestation must always be evaluated on the Backend.**
-   **Latency and Quotas:** Requesting an Integrity Token takes time (network call to Google) and is subject to daily quota limits. You cannot request a token on every single API call. Staff engineers request the token during high-risk chokepoints (Login, Checkout, Password Reset) and cache the trust status in a short-lived backend session.
-   **The Nonce Replay Attack:** If you don't use a cryptographically strong, backend-generated Nonce, an attacker can capture a valid Integrity Token from a real device and replay it alongside malicious requests from a bot farm. The Backend must verify that the Nonce inside the token perfectly matches the one it issued 5 seconds ago, and then burn the Nonce so it can never be used again.

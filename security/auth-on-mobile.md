# Security: Authentication on Mobile (JWTs, OAuth, and Biometrics)

## The Theory
Mobile authentication is fundamentally different from web authentication. A web browser relies on HTTP-only, Secure Cookies, which the browser automatically attaches to requests and protects from JavaScript (XSS). A mobile app has no browser engine; it must manually manage tokens, securely store them, and explicitly attach them to HTTP headers (`Authorization: Bearer <token>`).

## Staff-Level Application in Mobile

### 1. The Two-Token Architecture (Access + Refresh)
Never use a single, never-expiring API token. If a hacker extracts it from a rooted phone, they have permanent access to the user's account.
-   **Access Token (JWT):** Short-lived (e.g., 5 to 15 minutes). It is stateless. The backend validates it using cryptography (verifying the signature), meaning the backend doesn't need to query a database for every API call. The mobile app attaches this to every request.
-   **Refresh Token:** Long-lived (e.g., 30 days). It is stateful (stored in a backend database). The mobile app stores this securely in the Android Keystore.
-   **The Flow:** When the Access Token expires (HTTP 401), the mobile app's network interceptor (e.g., OkHttp `Authenticator`) automatically pauses pending requests, sends the Refresh Token to the `/refresh` endpoint, receives a new Access Token, and retries the paused requests seamlessly. If the backend detects suspicious activity, it revokes the Refresh Token in the database, forcing the user to log in again.

### 2. OAuth 2.0 & PKCE (Proof Key for Code Exchange)
When implementing "Log in with Google" or a custom OAuth flow, the app must bounce the user out to a secure browser (`CustomTabsIntent`).
-   **The Threat (Authorization Code Interception):** Historically, the browser would redirect back to the app via a custom scheme (`myapp://callback?code=123`). A malicious app could register `myapp://` and steal the code.
-   **The Solution (PKCE):** 
    1. The mobile app generates a random secret (`code_verifier`) and hashes it (`code_challenge`).
    2. It sends the `code_challenge` to the Auth server when opening the browser.
    3. The browser redirects back with the `code`.
    4. The mobile app sends the `code` *and* the original plaintext `code_verifier` to the backend.
    5. The backend hashes the verifier. If it matches the challenge from Step 2, it returns the Access Token. The malicious app cannot steal the token because it doesn't know the random `code_verifier` generated in memory.

### 3. Step-Up Authentication (Biometrics)
For highly sensitive actions (e.g., transferring $1,000), holding an Access Token is insufficient. The token proves the *device* is authenticated, but the user might have left their phone unlocked on a table.
-   **The Flow:** The app must prompt the user for Biometrics (Fingerprint/FaceID) immediately before the transaction.
-   **Cryptographic Binding:** (Detailed in `secure-storage-on-android.md`). We do not just check `if (biometricSuccess)`. We use the biometric scan to unlock a hardware-backed Private Key, sign a challenge from the server, and send the cryptographic signature alongside the transfer request.

## Common Pitfalls
-   **Logging Tokens:** Accidentally logging HTTP headers in staging builds (e.g., via `HttpLoggingInterceptor(Level.BODY)`) can leak production Bearer tokens into third-party crash reporting tools if developers reuse the same network client configuration. Always redact the `Authorization` header in logs.
-   **Storing Passwords:** An Android app should *never* store the user's plaintext password. Once the user authenticates, the password must be discarded from RAM immediately. The app relies entirely on the Refresh Token for returning sessions.

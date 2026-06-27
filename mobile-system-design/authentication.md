# Platform Design: Authentication (OAuth 2.0 & OIDC)

## The Prompt

*"Design the Authentication architecture for a mobile Banking application. The user must be able to log in securely, remain logged in across app restarts, and be instantly logged out if their device is stolen or their password is changed on the website. The backend must scale to millions of users without hitting the database for every single API request to verify the user."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Secure User Login (Email/Password or Biometrics).
- Persistent session across cold starts.
- Remote session revocation (Force Logout).

### Non-Functional Requirements (NFRs)
- **Security (Priority 0):** Never store raw passwords on the device. Never log credentials. Mitigate Man-in-the-Middle (MITM) attacks.
- **Backend Scalability:** The backend cannot execute a `SELECT * FROM sessions WHERE token = X` against a SQL database for every single incoming API request. The authorization check must be `O(1)` and stateless.

## 2. High-Level Architecture (JWT & Refresh Tokens)

A Junior engineer uses Stateful Sessions (sending a `Session_ID`, backend checks SQL).
A Staff engineer uses **Stateless JWTs (JSON Web Tokens) with a Two-Token Architecture** (Access Token + Refresh Token).

```mermaid
graph TD
    App[Mobile App] -->|1. Login (Credentials)| AuthServer[Auth Server / Keycloak]
    AuthServer -->|2. Return Tokens| App
    
    subgraph Secure Enclave
        App -->|Save Refresh Token| Keystore[(Android Keystore)]
    end
    
    subgraph API Calls
        App -->|3. Bearer AccessToken| API[API Gateway]
        API -->|4. Cryptographic Verify (No DB)| API
    end
    
    subgraph Token Rotation
        App -->|Access Token Expired| AuthServer
        AuthServer -->|Validate Refresh Token in DB| AuthServer
        AuthServer -->|Return New Access Token| App
    end
```

## 3. The Core Flows (Deep Dive)

### Flow 1: The Two-Token Architecture (Why do we need two?)
*Interviewer:* "Why not just issue a single token that lasts forever?"

**Staff Answer:**
"A token that lasts forever is functionally a password. If a hacker intercepts it, they have infinite access. We must use two tokens:
1.  **The Access Token (JWT):** Very short lifespan (e.g., 15 minutes). It is fully **Stateless**. The backend API Gateway mathematically verifies the JWT's cryptographic signature without talking to a database. This allows infinite backend scalability.
2.  **The Refresh Token:** Long lifespan (e.g., 30 days). It is **Stateful**. It is stored securely in the backend database. 
If the 15-minute Access Token is stolen, the hacker only has 15 minutes. To get a new one, they need the Refresh Token, which is securely locked in the Android Keystore."

### Flow 2: Remote Revocation (The Stolen Phone)
*Interviewer:* "The user's phone is stolen. They log into your website and click 'Log out of all devices'. But you just said the Access Token is stateless and the backend doesn't check the DB! How do you stop the thief from using the app?"

**Staff Answer:**
"This is the fundamental tradeoff of Stateless JWTs. You *cannot* easily revoke a stateless token.
1. **The Maximum Window of Vulnerability:** Because the Access Token expires in 15 minutes, the absolute worst-case scenario is the thief has 15 minutes of access.
2. **The Revocation:** When the user clicks 'Log out of all devices', the backend marks the **Refresh Token** as `Revoked` in the SQL database.
3. **The Cut-off:** After 15 minutes, the thief's Access Token expires. The mobile app automatically sends the Refresh Token to the Auth Server to get a new one. The Auth Server checks the DB, sees it is revoked, and returns HTTP `401 Unauthorized`. The app forcefully logs the thief out.
If 15 minutes is too long for a Bank, we reduce the Access Token lifespan to 5 minutes."

### Flow 3: Secure Storage (The Android Keystore)
*Interviewer:* "Where exactly do you store the Refresh Token on the device? A rooted Android phone can read the `SharedPreferences.xml` file in plaintext."

**Staff Answer:**
"I must use the **Android Keystore System (Hardware-Backed Security)**.
1. I generate a symmetric encryption key (AES-256) inside the Android Keystore. The physical hardware (the Trusted Execution Environment / Secure Enclave) generates this key. The key *cannot* be extracted from the hardware, even on a rooted device.
2. When the backend sends the Refresh Token, I pass it to the Keystore API to encrypt it.
3. I save the *encrypted* byte array in `SharedPreferences` (or EncryptedSharedPreferences).
4. When I need the Refresh Token, I pass the encrypted bytes back to the Keystore, and the hardware decrypts it. 
Even if a hacker copies the entire file system of the phone, they only get encrypted gibberish. They cannot decrypt it without the physical CPU chip of that specific phone."

## 4. Failure Modes & Bottlenecks

### Bottleneck: The Token Expiration Race Condition
*Interviewer:* "The Access Token expires. The user taps 5 different buttons simultaneously on the screen. The app fires 5 API requests. All 5 return `401 Unauthorized`. Your app fires 5 identical 'Refresh Token' requests to the Auth Server. Fix it."

**Staff Answer:**
"This requires an **OkHttp Authenticator** with a Mutex lock.
1. `OkHttp` intercepts the first `401` response.
2. It acquires a Coroutine `Mutex` lock (or `synchronized` block).
3. The other 4 requests also get `401`s, but they hit the Mutex and are suspended (they wait).
4. The first request calls the Auth Server, gets the new tokens, saves them, and unlocks the Mutex.
5. The 4 suspended requests wake up, see that a new token exists, attach the *new* token to their original HTTP requests, and retry the API call. The user never sees an error, and the Auth Server only receives 1 refresh request."

### Bottleneck: Man-in-the-Middle (MITM) Attacks
*Interviewer:* "The user connects to a malicious public Wi-Fi network at a coffee shop. The hacker intercepts the HTTPS traffic using a rogue Root Certificate installed on the user's phone. They steal the Access Token."

**Staff Answer:**
"HTTPS is not enough if the device trusts a malicious certificate. We must implement **Certificate Pinning**.
Inside our OkHttp configuration, we hardcode the SHA-256 hash of our backend's Public Key (or intermediate certificate).
```kotlin
val pinner = CertificatePinner.Builder()
    .add("api.mybank.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .build()
```
Even if the OS trusts the hacker's fake certificate, OkHttp will violently reject the connection because the public key hashes do not match. The app will refuse to transmit the tokens."

## 5. Staff Engineer Thinking: Biometrics & Zero Trust

A Junior engineer implements Fingerprint login by saving the user's password in `SharedPreferences`, and when `BiometricPrompt` returns `true`, they secretly send the password to the server. This is a catastrophic security failure.

A Staff Engineer implements **Cryptographic Biometrics**.
We create a Private Key in the Android Keystore and configure it with `setUserAuthenticationRequired(true)`.
When the user logs in the first time, we send the *Public Key* to the backend.
On subsequent logins, the backend sends a random `challenge` string. The Android app asks the user for their fingerprint. Only if the fingerprint matches will the Keystore hardware unlock the Private Key, sign the challenge, and send the signature back to the server. The server verifies the signature mathematically. The password is never stored, and the fingerprint data never leaves the device.

## 6. Probing Questions (For Practice)

1.  Explain why a stateless JWT Access Token allows a backend to scale infinitely compared to a stateful Session ID stored in a SQL database.
2.  Walk through the "Two-Token Architecture." Why is it necessary to have both a short-lived Access Token and a long-lived Refresh Token?
3.  Describe the exact sequence of events when a user clicks "Log out of all devices" on a website. How does this affect their stolen mobile phone?
4.  Why is storing a Refresh Token in plaintext `SharedPreferences` a massive security vulnerability on Android, and how does the hardware-backed Keystore solve this?
5.  Explain the Token Expiration Race Condition. How does an OkHttp `Authenticator` combined with a Mutex prevent 5 simultaneous refresh requests?
6.  What is a Man-in-the-Middle (MITM) attack, and how does Certificate Pinning specifically defeat it even if the device trusts the malicious certificate?
7.  Why is storing the user's password on the device to facilitate "Biometric Login" an architectural failure?
8.  Describe how Cryptographic Biometrics work using Public/Private key pairs and a backend challenge, ensuring the fingerprint never leaves the device.
9.  If the Access Token is completely stateless, how does the backend identify who the user is when they make an API request? (Hint: The payload payload).
10. What happens if the Refresh Token is compromised? How does the concept of "Refresh Token Rotation" mitigate this?

## Further Reading

- [`security-and-keystore.md`](../android/networking-and-security/security-and-keystore.md) — The deep dive into the Hardware-Backed Keystore and Biometrics.
- [`retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — How to implement the `Authenticator` and Certificate Pinning in code.
- [`caching-library.md`](caching-library.md) — How to use Mutexes to prevent Thundering Herds (similar to the Token Race Condition).

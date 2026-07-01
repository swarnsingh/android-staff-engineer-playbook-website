# Security: Authentication on Mobile (OAuth, PKCE, Tokens, Biometric Step-Up)

> The pragmatic flow for adding auth to an Android app: OAuth 2.0 Authorization Code + PKCE, JWT access + rotating refresh, OkHttp `Authenticator` for silent refresh, biometric step-up for sensitive actions.

---

## 1. Why Mobile Auth Is Its Own Problem

Browsers carry HTTP-only Secure cookies, automatically attached, hidden from JavaScript. Phones have none of that. Every request is a raw HTTP call; you decide what to attach. The browser also doesn't have a `Keystore`. So mobile auth is: "issue tokens, store them safely, attach them to every request, refresh them silently, gate them with biometric when stakes rise."

Three building blocks:
1. **OAuth Authorization Code + PKCE** to get tokens from your IdP.
2. **Two-token model** (short-lived access, longer-lived rotating refresh) for ongoing API calls.
3. **Biometric-bound Keystore key** for step-up when amount/risk demands it.

### Staff threat model

Mobile auth assumes the attacker can own the client. Design policy around server-side risk, not client-side trust.

| Threat | Mitigation | Limit |
|---|---|---|
| Stolen access token | Short TTL, audience/scope binding, revoke on anomaly | Token works until expiry |
| Stolen refresh token | Rotation with reuse detection | Requires backend token family tracking |
| Deep-link interception | Claimed HTTPS app links, PKCE, state validation | Custom schemes are weaker |
| Rooted/tampered device | Step-up, attestation, risk scoring | Cannot make a compromised client trustworthy |
| Replay of sensitive action | Server nonce, idempotency, device signing key | Needs server-side enforcement |
| Socially engineered session | Biometric step-up for high-risk actions | Biometrics prove local user presence, not intent |

The Staff-level rule: authentication proves account access; it does not prove device integrity, app integrity, or user intent. High-risk actions need additional signals.

---

## 2. OAuth 2.0 Authorization Code + PKCE (the Login)

```
Client                  AuthBrowser (Chrome Custom Tab)            IdP
  │
  │ generate verifier (random 64-char) + challenge=SHA256(verifier)
  │
  │ open URL: /authorize?response_type=code
  │            &client_id=...
  │            &redirect_uri=myapp://auth/callback
  │            &code_challenge=...&code_challenge_method=S256
  │            &state=...&scope=openid offline_access
  │
  │ ───────────────────────────────►  user signs in  ──────────────►
  │                                                                  │
  │ ◄───────── redirect ── myapp://auth/callback?code=xyz&state=...  │
  │
  │ POST /token { grant_type=authorization_code, code, code_verifier, client_id, redirect_uri }
  │ ─────────────────────────────────────────────────────────────────►
  │ ◄───── { access_token, refresh_token, id_token, expires_in } ────
  │
  │ persist to KeystoreTokenVault
```

```kotlin
class AuthBrowserClient @Inject constructor(
    private val activityProvider: () -> ComponentActivity,
    private val verifierStore: VerifierStore,
    private val idp: IdpConfig,
) {
    suspend fun login(): AuthResult = suspendCancellableCoroutine { cont ->
        val verifier = generatePkceVerifier()
        val challenge = sha256Base64Url(verifier)
        val state = ByteArray(16).also { SecureRandom().nextBytes(it) }.base64UrlNoPad()
        verifierStore.put(state, verifier)

        val authUri = Uri.parse(idp.authorizeEndpoint).buildUpon()
            .appendQueryParameter("response_type", "code")
            .appendQueryParameter("client_id", idp.clientId)
            .appendQueryParameter("redirect_uri", REDIRECT_URI)
            .appendQueryParameter("code_challenge", challenge)
            .appendQueryParameter("code_challenge_method", "S256")
            .appendQueryParameter("scope", "openid profile offline_access")
            .appendQueryParameter("state", state)
            .build()

        CustomTabsIntent.Builder()
            .setShowTitle(true)
            .build()
            .launchUrl(activityProvider(), authUri)

        // Continuation completed by AuthCallbackActivity when myapp://auth/callback fires.
        pendingContinuations[state] = cont
    }

    suspend fun completeWithCode(state: String, code: String): Tokens {
        val verifier = verifierStore.takeAndRemove(state) ?: error("invalid state")
        val resp = idpApi.exchange(
            TokenRequest(
                grantType = "authorization_code",
                code = code, codeVerifier = verifier,
                clientId = idp.clientId, redirectUri = REDIRECT_URI,
            )
        )
        return Tokens(
            access = resp.accessToken,
            refresh = resp.refreshToken,
            accessExpiresAtMs = clock.now() + resp.expiresInSec * 1000,
            obtainedAtMs = clock.now()
        )
    }
}

private fun generatePkceVerifier(): String {
    val bytes = ByteArray(64)
    SecureRandom().nextBytes(bytes)
    return Base64.encodeToString(
        bytes, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP
    )
}

private fun sha256Base64Url(input: String): String {
    val digest = MessageDigest.getInstance("SHA-256")
        .digest(input.toByteArray(Charsets.US_ASCII))
    return Base64.encodeToString(
        digest, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP
    )
}
```

```kotlin
class AuthCallbackActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val uri = intent.data ?: run { finish(); return }
        val state = uri.getQueryParameter("state")
        val code = uri.getQueryParameter("code")
        val error = uri.getQueryParameter("error")

        if (error != null) {
            authResultBus.publish(AuthResult.Error(error))
            finish(); return
        }
        if (state == null || code == null) { finish(); return }

        lifecycleScope.launch {
            runCatching { authBrowserClient.completeWithCode(state, code) }
                .onSuccess { tokens ->
                    tokenVault.save(tokens)
                    authResultBus.publish(AuthResult.Success)
                }
                .onFailure { authResultBus.publish(AuthResult.Error(it.message)) }
            finish()
        }
    }
}
```

```xml
<!-- AndroidManifest.xml -->
<activity android:name=".auth.AuthCallbackActivity"
          android:exported="true"
          android:launchMode="singleTask">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp" android:host="auth" android:path="/callback" />
    </intent-filter>
</activity>
```

> **Why Chrome Custom Tabs, not WebView.** Custom Tabs share cookies with the user's Chrome session (so they're already signed in to Google), expose the URL bar to defeat phishing, and never give your app access to the password. WebView gives you all those things — and the security audit team will reject it.

---

## 3. Two-Token Storage

```kotlin
data class Tokens(
    val access: String,
    val refresh: String,
    val accessExpiresAtMs: Long,
    val obtainedAtMs: Long,
)

interface TokenVault {
    suspend fun save(tokens: Tokens)
    suspend fun load(): Tokens?
    suspend fun clear()
}
```

Implementation lives in `secure-storage-on-android.md`. The vault wraps `EncryptedSharedPreferences` (or DataStore+Tink). Access tokens survive process death; refresh tokens survive reboots.

---

## 4. OkHttp `Authenticator` (Silent Refresh)

When the access token is expired (or rejected), the `Authenticator` runs **synchronously** on the dispatcher thread, refreshes, and retries the request. Single-flight discipline prevents N concurrent requests from all triggering N concurrent refreshes (which most IdPs will reject).

```kotlin
class JwtAuthenticator @Inject constructor(
    private val refresher: TokenRefresher,
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        if (response.priorRequest("Authorization") != null && response.priorRetries() >= 1) {
            return null    // already retried; give up
        }
        val refreshed = runBlocking { refresher.refreshNow() } ?: return null
        return response.request.newBuilder()
            .header("Authorization", "Bearer ${refreshed.access}")
            .build()
    }
}

class JwtRequestInterceptor @Inject constructor(
    private val refresher: TokenRefresher,
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        if (request.header("X-No-Auth") != null) return chain.proceed(request)

        val token = runBlocking { refresher.freshAccessToken() }
            ?: return chain.proceed(request)    // unauthenticated request

        return chain.proceed(
            request.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        )
    }
}
```

```kotlin
@Singleton
class TokenRefresher @Inject constructor(
    private val vault: TokenVault,
    private val idpApi: IdpApi,
    private val clock: Clock,
) {
    private val refreshMutex = Mutex()
    private var inFlight: Deferred<Tokens?>? = null

    suspend fun freshAccessToken(): String? {
        val current = vault.load() ?: return null
        return if (current.accessExpiresAtMs - clock.now() > REFRESH_AHEAD_MS) {
            current.access
        } else {
            refreshNow()?.access
        }
    }

    suspend fun refreshNow(): Tokens? = refreshMutex.withLock {
        inFlight?.let { return it.await() }
        val deferred = scope.async {
            val current = vault.load() ?: return@async null
            try {
                val resp = idpApi.refresh(current.refresh)
                Tokens(
                    access = resp.accessToken,
                    refresh = resp.refreshToken,        // rotating: new refresh on every call
                    accessExpiresAtMs = clock.now() + resp.expiresInSec * 1000,
                    obtainedAtMs = clock.now(),
                ).also { vault.save(it) }
            } catch (e: HttpException) {
                if (e.code() == 400 || e.code() == 401) {
                    vault.clear()
                    sessionEvents.publish(SessionEvent.ForceSignOut(reason = "refresh_rejected"))
                }
                null
            }
        }
        inFlight = deferred
        try { deferred.await() } finally { inFlight = null }
    }

    companion object { private const val REFRESH_AHEAD_MS = 60_000L }
}
```

**Refresh token rotation.** Modern IdPs (Auth0, Okta, Cognito, Keycloak with rotation enabled) issue a new refresh token on every refresh and invalidate the previous. Your code must accept and persist the new one *atomically*. If your refresh succeeds but you crash before persisting, the user is locked out (server rotated; client still has old).

```kotlin
suspend fun atomicSwap(new: Tokens) {
    vault.save(new)        // EncryptedSharedPreferences.commit() = atomic
}
```

---

## 5. Logout

```kotlin
suspend fun signOut(reason: SignOutReason) {
    val tokens = vault.load()
    runCatching {
        if (tokens != null) idpApi.revoke(tokens.refresh)
    }.onFailure { /* best effort; clear local regardless */ }

    vault.clear()
    cacheDir.deleteRecursively()
    workManager.cancelAllWorkByTag("user-scoped")
    db.clearAllTables()
    notifications.cancelAll()

    Analytics.reset()
    sessionEvents.publish(SessionEvent.SignedOut(reason))
}
```

Sign-out clears local state, cancels user-scoped workers, drops cached data, and (best-effort) tells the IdP to invalidate the refresh token. Local clear must succeed even if the server call fails.

---

## 6. Biometric Step-Up

The session token says "I am signed in." For a $1,000 transfer, you want the user to prove "I'm still here." Biometric step-up uses a Keystore-resident key that requires biometric auth on each use.

```kotlin
class StepUpGate @Inject constructor(
    private val biometricKey: BiometricKeystoreKey,
    private val recencyStore: RecencyStore,
    private val clock: Clock,
) {
    suspend fun require(activity: FragmentActivity, action: SensitiveAction): Boolean {
        val recentAuth = recencyStore.lastSuccessfulMs(action)
        if (clock.now() - recentAuth < action.recencyWindowMs) return true

        val nonce = serverNonceFor(action)         // server-issued challenge
        val signature = biometricKey.signWithBiometric(activity, nonce) ?: return false

        val ok = backend.verifySignature(action, signature)
        if (ok) recencyStore.markSuccessful(action, clock.now())
        return ok
    }
}

enum class SensitiveAction(val recencyWindowMs: Long) {
    TRANSFER(recencyWindowMs = 5 * 60 * 1000),       // 5 minutes
    CHANGE_PASSWORD(recencyWindowMs = 60 * 1000),   // 60 seconds (always fresh)
    ADD_PAYEE(recencyWindowMs = 5 * 60 * 1000),
}
```

The signed nonce proves the user successfully authenticated on the device's biometric sensor AND the device holds the registered private key. The backend verifies both, then permits the action.

See `secure-storage-on-android.md` for the `BiometricKeystoreKey.signWithBiometric` implementation.

---

## 7. Sign-In With Google / OneTap (Without Going Through Your IdP)

Google's Credential Manager API handles the OAuth dance natively:

```kotlin
class GoogleSignInClient @Inject constructor(
    private val credentialManager: CredentialManager,
) {
    suspend fun signIn(activity: ComponentActivity): String? {
        val request = GetCredentialRequest.Builder()
            .addCredentialOption(
                GetGoogleIdOption.Builder()
                    .setServerClientId(BuildConfig.GOOGLE_SERVER_CLIENT_ID)
                    .setFilterByAuthorizedAccounts(true)
                    .build()
            )
            .build()

        val resp = credentialManager.getCredential(activity, request)
        val credential = resp.credential
        return when (credential) {
            is GoogleIdTokenCredential -> credential.idToken
            else -> null
        }
    }
}
```

The `idToken` is a JWT signed by Google. Send it to your backend, which verifies the signature against Google's public keys and issues your app's session tokens.

---

## 8. Common Pitfalls

- **`HttpLoggingInterceptor.Level.HEADERS` or `BODY` in production builds.** Leaks `Authorization` headers to logs/crash reports. Use a redacting interceptor that strips `Authorization`, `Cookie`, `Set-Cookie`.
- **Concurrent refresh storms.** Without single-flight, 8 concurrent requests = 8 refresh calls; IdP rejects 7 with "refresh token reused" if rotation is on. Use `Mutex` + `Deferred`.
- **Storing the user's password.** Don't. After login, the password is discarded; refresh token is the long-lived identity.
- **Plain `Bearer` over plain HTTP.** Network Security Config + `usesCleartextTraffic="false"`.
- **PKCE optional.** Spec says public clients (mobile, SPAs) MUST use PKCE. Some legacy IdPs let you skip. Don't.
- **Using `myapp://` for redirect without App Link verification.** Anyone can register that scheme. Use a verified HTTPS App Link (`https://example.com/auth/callback`) or accept the slightly weaker custom scheme only with PKCE in place.
- **Trusting `id_token` for authorization.** ID tokens are *authentication* artifacts; backends should reissue their own session tokens for *authorization*.
- **Not handling clock skew.** `accessExpiresAtMs` derived from device clock can be off by minutes. Treat it as advisory; let the server's 401 be the trigger.
- **No "force sign-out" path.** Compromised account = need to invalidate everywhere. Server should be able to revoke a refresh token; client should respect the resulting 400 and sign out cleanly.
- **Biometric without `setInvalidatedByBiometricEnrollment`.** A thief enrolls their finger and the old key still works. With invalidation on, the key dies and forces re-auth.

---

## 9. Testing

```kotlin
@Test
fun authenticator_singleFlight_onlyOneRefresh() = runTest {
    val refresher = FakeTokenRefresher(refreshLatencyMs = 200)
    val auth = JwtAuthenticator(refresher)

    repeat(8) {
        launch { auth.authenticate(null, fakeResponseWith401()) }
    }
    advanceUntilIdle()

    assertEquals(1, refresher.refreshCallCount)
}

@Test
fun signOut_clearsAllUserState() = runTest {
    vault.save(testTokens())
    db.userDao().insert(testUser())

    authRepository.signOut(SignOutReason.USER_INITIATED)

    assertNull(vault.load())
    assertNull(db.userDao().get())
    assertEquals(emptyList<Notification>(), notificationManager.active())
}
```

Integration: run against a real IdP sandbox; assert refresh rotation behavior; assert `revoke` succeeds.

---

## 10. Further Reading

- [RFC 8252 — OAuth 2.0 for Native Apps](https://www.rfc-editor.org/rfc/rfc8252) — canonical guidance.
- [RFC 7636 — PKCE](https://www.rfc-editor.org/rfc/rfc7636) — the spec.
- [AppAuth for Android](https://github.com/openid/AppAuth-Android) — reference OAuth library with PKCE.
- [Credential Manager](https://developer.android.com/training/sign-in/passkeys) — Google's unified sign-in API.
- [Android Developers — Biometric authentication](https://developer.android.com/training/sign-in/biometric-auth) — Class 3 prompts.

---

> **In short:** Authorization Code + PKCE through Chrome Custom Tabs; two-token model with rotating refresh; single-flight refresh in OkHttp; Keystore-resident biometric-bound key for step-up. Never log the token. Always clear on sign-out.

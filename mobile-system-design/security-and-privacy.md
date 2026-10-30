# Security & Privacy (Android Mobile)

> A 45-60 minute mobile system-design walkthrough for the security & privacy posture of an Android app: TLS + pinning, Keystore, biometric, screen capture, root/repackaging detection, PII handling, GDPR. A horizontal concern referenced across every other file.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Walk me through the security and privacy decisions for a mobile app."
> **Candidate:** "Security breaks down into transport, storage, app integrity, and runtime. Privacy is about minimisation, consent, and compliance. I'll cover both and deep-dive Keystore-wrapped credential storage."

### Functional Requirements
- **TLS 1.2+** for all network traffic (prefer TLS 1.3).
- **Certificate pinning** only where the threat model justifies it, with backup pins and a recovery plan.
- **Token storage** in Keystore-wrapped storage.
- **Biometric** for high-stakes actions.
- **PII redaction** in logs and analytics.
- **GDPR / CCPA** compliance: consent + delete-my-data.

### Non-Functional Requirements
- **Defense in depth** — multiple layers; no single point of failure.
- **No surprises** — security choices documented in code.
- **Compatible** with security review processes.
- **Tested**: pen-tested annually; regression caught in CI.
- **Failures don't crash** — graceful degradation.

### Out of Scope
- Server-side security (separate domain)
- Anti-fraud ML (server)
- App Store distribution security (Play handles signing, downloads)
- Hardware-level attestation deep dive (touched lightly)
- Compliance audits (legal team)

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Domain (banking, social, retail)? | Threat model intensity |
| Tokens (JWT, session)? | Storage strategy |
| Biometric tier (Class 3 required)? | Keystore binding |
| Markets (GDPR, CCPA, COPPA)? | Consent flow |
| OS floor? | Keystore features, biometric APIs |
| Anti-tamper requirements? | Root detection, Play Integrity |
| Network certificate rotation cadence? | Pinning UX |

> **Candidate:** "Retail with payments; JWT access + rotating refresh; Class-3 biometric on transactions > €30; GDPR + CCPA + COPPA; Android 9+; Play Integrity for high-risk actions; pinning rotation every 6 months with overlap."

---

## 3. The Security Stack on Android

```mermaid
flowchart TD
    Threats["Threat model and data classification"]
    Transport["Transport<br/>TLS + cleartext policy + justified pinning"]
    Storage["Storage<br/>Android Keystore + versioned encryption envelope"]
    Integrity["App integrity<br/>Play App Signing + Play Integrity signals"]
    Runtime["Runtime controls<br/>biometric gates + secure UI + validated links"]
    Code["Build controls<br/>R8 + dependency and native-code hardening"]
    Backend["Server enforcement<br/>short-lived credentials + revocation + risk policy"]

    Threats --> Transport
    Threats --> Storage
    Threats --> Integrity
    Threats --> Runtime
    Threats --> Code
    Transport --> Backend
    Storage --> Backend
    Integrity --> Backend
    Runtime --> Backend
```

No layer proves trust alone. Device-side controls reduce exposure and produce signals, while the backend still enforces credential lifetime, authorization, revocation, and risk decisions.

Validated against: [Android security best practices](https://developer.android.com/privacy-and-security/security-best-practices) and [Play Integrity overview](https://developer.android.com/google/play/integrity/overview).

---

## 4. Transport (TLS + Pinning)

### Strict TLS

```kotlin
val okHttp = OkHttpClient.Builder()
    .connectionSpecs(listOf(
        ConnectionSpec.Builder(ConnectionSpec.MODERN_TLS)
            .tlsVersions(TlsVersion.TLS_1_3, TlsVersion.TLS_1_2)
            .cipherSuites(*MODERN_CIPHERS)
            .build()
    ))
    .build()
```

Disallow plaintext in stacks that honor the app's `network_security_config.xml` policy:

```xml
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    <domain-config>
        <domain includeSubdomains="true">api.example.com</domain>
        <!-- No expiry here: an expired pin set stops enforcing pinning. -->
        <pin-set>
            <pin digest="SHA-256">primaryPinBase64==</pin>
            <pin digest="SHA-256">backupPinBase64==</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```

### Pinning ops

- **Always have a backup pin** — primary pin compromise without backup = bricked app.
- **Rotate with overlap** — add new pin before retiring old.
- **Review pins and rotation on a schedule** — an optional XML expiration disables pinning on that date; it does not rotate keys. Track any chosen expiration per shipped version.
- **Pin only your domains** — don't pin third-party APIs.
- **Have a kill switch** — flag to disable pinning in case of emergency (review carefully).

### Cleartext policy

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="false">
```

The Network Security Config above denies cleartext for cooperating network stacks on Android 7.0 (API 24) and higher. The manifest flag provides a fallback on Android 6.0 (API 23) devices, where Network Security Config is unavailable; on API 24 and higher, the flag is ignored when a Network Security Config is present. Neither setting guarantees that raw sockets or every third-party SDK will reject `http://`. Test the app's actual network paths. See [Android's application manifest reference](https://developer.android.com/guide/topics/manifest/application-element.html#usesCleartextTraffic) and the [canonical pinning chapter](../security/certificate-pinning.md).

---

## 5. Storage (Keystore, Private Storage, SQLCipher)

### Token storage

Keep access tokens in memory when possible. When persistence is required, generate a direct `AndroidKeyStore` key, encrypt into a versioned `IV + ciphertext` envelope, and store that envelope in private storage. AndroidX Security Crypto deprecated `EncryptedSharedPreferences`; existing installations need a migration rather than being copied into new designs. See [Secure Storage on Android](../security/secure-storage-on-android.md).

Non-exportable does not mean unusable by a compromised process. Token TTL, rotation, revocation, audience restriction, and server-side anomaly controls remain mandatory.

### Room with SQLCipher

```kotlin
// net.zetetic:sqlcipher-android (the older android-database-sqlcipher is deprecated)
System.loadLibrary("sqlcipher")
val passphrase: ByteArray = keystoreUnwrap(storedPassphraseEnvelope)
val factory = SupportOpenHelperFactory(passphrase)
val db = Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
    .openHelperFactory(factory)
    .build()
```

The passphrase is generated once and wrapped by a direct Keystore AES key. Store only the versioned passphrase ciphertext in app-private storage, and unwrap it with the Keystore key before opening the database.

### Keystore-bound biometric key

```kotlin
val keyGen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
keyGen.init(
    KeyGenParameterSpec.Builder("biometric_key",
        KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
        .setUserAuthenticationRequired(true)
        .apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
            } else {
                @Suppress("DEPRECATION")
                setUserAuthenticationValidityDurationSeconds(-1) // auth for every use
            }
        }
        .build()
)
```

Using this key requires fresh biometric authentication. Decrypting a stored token = biometric prompt. `setUserAuthenticationParameters` exists from API 30; this design's Android 9 floor needs the older call below that.

---

## 6. App Integrity (Play Integrity)

```kotlin
val integrityManager = IntegrityManagerFactory.create(context)
val request = IntegrityTokenRequest.builder()
    .setNonce(serverProvidedNonce)
    .build()
integrityManager.requestIntegrityToken(request)
    .addOnSuccessListener { response ->
        // Send response.token() to your server for verification
    }
```

Your server decrypts the verdict and checks the signals: `appRecognitionVerdict` is `PLAY_RECOGNIZED`, `appLicensingVerdict` is `LICENSED`, and the device-integrity labels (such as `MEETS_DEVICE_INTEGRITY`). Treat them as risk signals to combine with your own, not as proof.

This snippet is a classic request, which suits rare checks on the highest-value actions (transfers, account changes). Use standard requests for frequent, on-demand checks. Not for ordinary reads.

---

## 7. Runtime Protections

### Screen capture / overlays

```kotlin
class PaymentActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
    }
}
```

- Blocks screenshots of this activity.
- Hides from screen recording.
- Blacks out content in app switcher.

Use on: payment screens, security setup, sensitive content (medical, legal).

### Deep-link validation

```kotlin
fun handleDeepLink(uri: Uri): Boolean {
    if (uri.scheme != "https" || uri.host != "example.com") return false
    val path = uri.pathSegments
    // ... parse safely; never `eval` URI fragments
}
```

App Links + Digital Asset Links verification (see `deep-links-and-universal-links.md`).

### Tap-jacking

```xml
<!-- Views: on the sensitive View in the layout -->
<Button
    android:filterTouchesWhenObscured="true" />
```

```kotlin
// Compose: set it on the View hosting the sensitive screen
val view = LocalView.current
DisposableEffect(view) {
    view.filterTouchesWhenObscured = true
    onDispose { view.filterTouchesWhenObscured = false }
}

// Android 12 (API 31) and higher: hide non-system overlay windows
// (requires <uses-permission android:name="android.permission.HIDE_OVERLAY_WINDOWS" />)
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
    window.setHideOverlayWindows(true)
}
```

`filterTouchesWhenObscured` drops touches delivered while another window fully covers the view. Partial overlays need a check for `MotionEvent.FLAG_WINDOW_IS_PARTIALLY_OBSCURED`. See [Tapjacking](https://developer.android.com/privacy-and-security/risks/tapjacking).

---

## 8. Code Obfuscation & Shrinking

```kotlin
// build.gradle.kts
buildTypes {
    release {
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(
            getDefaultProguardFile("proguard-android-optimize.txt"),
            "proguard-rules.pro"
        )
    }
}
```

R8 obfuscates class/method names — raises the bar for reverse engineering. Doesn't stop a determined attacker but stops casual decompilation.

For sensitive constants:
- Anything shipped in the APK, including `BuildConfig` fields and resources, can be extracted. Keep real secrets server-side; restrict any client key (API restrictions, app-signature checks) and treat it as an identifier, not a secret.
- Crypto secrets: never embed; derive from user input or server, or keep keys in the Android Keystore.

---

## 9. Deep Dive: Token Storage with a Keystore Envelope (~15 min)

> *I'd pick this as the deep dive because token storage is the most-attacked surface — long-lived refresh tokens unlock everything else.*

### Why Keystore?

A token stored in ordinary private storage is protected by the UID sandbox but is plaintext if that file is extracted. A Keystore-backed envelope adds a non-exportable encryption key and optional authentication requirements. A compromised app process may still invoke an authorized key, so this is one layer rather than a complete root defense.

### The layering

```
User token (string)
    ↓ encrypted with
AES-GCM using a non-exportable key handle
    ↓ ciphertext + IV stored in
Private file / DataStore / SharedPreferences / database
    ↓ key material held by
Android Keystore (TEE or StrongBox only when verified)
```

### Key and envelope ownership

Use the direct `KeyGenerator` + `KeyGenParameterSpec` pattern in the canonical secure-storage page. If StrongBox is requested, handle `StrongBoxUnavailableException`; the platform does not promise a silent fallback. Record the envelope schema version, IV, ciphertext, key generation, and associated-data contract.

### Writing and reading the token

```kotlin
// Write
val encrypted = keystoreAead.encrypt(
    plaintext = json.encodeToString(tokens).encodeToByteArray(),
    associatedData = accountId.encodeToByteArray(),
)
privateStore.write(encrypted)

// Read
val stored = privateStore.read() ?: return null
val tokens = json.decodeFromString<Tokens>(
    keystoreAead.decrypt(stored, associatedData = accountId.encodeToByteArray()).decodeToString()
)
```

### Biometric-bound variant

For apps where credentials must be biometric-gated on each use (e.g., banking):

```kotlin
suspend fun loadTokenWithBiometric(activity: FragmentActivity): String? {
    val envelope = privateStore.read() ?: return null
    // AES-GCM decryption needs the stored IV at init time, before authentication.
    val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
        init(Cipher.DECRYPT_MODE, keystoreKey("biometric_key"), GCMParameterSpec(128, envelope.iv))
    }
    // authenticateWithCrypto: a suspending wrapper around BiometricPrompt.authenticate(promptInfo, cryptoObject)
    val authorized = authenticateWithCrypto(activity, BiometricPrompt.CryptoObject(cipher)) ?: return null
    return authorized.cipher!!.doFinal(envelope.ciphertext).decodeToString()
}
```

The cipher is initialised with the envelope's IV before it is wrapped in a `CryptoObject`; after successful authentication, `doFinal` runs on that same authorised cipher. Re-initialising the cipher after the prompt would discard the authorisation. Without successful biometric authentication, the configured key cannot perform the operation.

### Backup exclusion

```xml
<application android:fullBackupContent="@xml/backup_rules"
             android:dataExtractionRules="@xml/data_extraction_rules">
```

```xml
<!-- backup_rules.xml: devices running Android 11 and lower -->
<full-backup-content>
    <exclude domain="file" path="token-vault.bin" />
</full-backup-content>
```

```xml
<!-- data_extraction_rules.xml: Android 12+ for apps targeting API 31+ -->
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="file" path="token-vault.bin" />
    </cloud-backup>
    <device-transfer>
        <exclude domain="file" path="token-vault.bin" />
    </device-transfer>
</data-extraction-rules>
```

Don't let cloud backup or device-to-device transfer carry tokens to other devices. See [Back up user data with Auto Backup](https://developer.android.com/identity/data/autobackup).

### Revoke on suspicion

If you detect a security event (failed biometric attempts, suspicious geo, server alert), revoke the session and force re-authentication:

```kotlin
suspend fun revokeOnSuspicion() {
    vault.load()?.let { tokens -> runCatching { api.revoke(tokens.refreshToken) } } // RFC 7009, best effort
    vault.clear()
    navigator.replaceWithLogin(reason = ReAuthReason.SECURITY_EVENT)
}
```

---

## 10. Privacy & Compliance

### Minimisation

- Don't collect what you don't need.
- Aggregate locations to H3 cell, not raw lat/lng.
- Redact PII in logs and crash reports.

```kotlin
class PiiRedactor {
    // Best-effort scrubbing for free text; prefer structured fields redacted by key.
    private val patterns = listOf(
        Regex("[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}") to "[REDACTED_EMAIL]",
        Regex("\\b\\d(?:[ -]?\\d){12,18}\\b") to "[REDACTED_CARD]",
        Regex("\\+?\\d[\\d ()-]{7,}\\d") to "[REDACTED_PHONE]",
    )
    fun redact(message: String): String = patterns.fold(message) { msg, (regex, replacement) ->
        msg.replace(regex, replacement)
    }
}
```

Regex scrubbing misses formats it does not know. Prefer typed log and analytics fields that are redacted by key (see the analytics SDK's `PiiRedactionInterceptor`).

### Consent

```kotlin
data class Consent(val analytics: Boolean, val marketing: Boolean, val crashReporting: Boolean)
```

Gate every category through `Consent`. Default `false` for non-essential.

### Delete-my-data

```kotlin
suspend fun handleDeleteRequest() {
    api.deleteAccount()                    // server cascade
    db.clearAllTables()                    // local Room
    tokenVault.clear()                    // local secrets and dependent ciphertext
    notifierClear.cancelAll()              // active notifications
    workManager.cancelAllWork()            // pending workers
    auth.signOut()                          // session
}
```

Document this flow. Audit annually. Reach for the same code path as the GDPR delete endpoint.

### Lock-screen visibility

```kotlin
NotificationCompat.Builder(ctx, CHANNEL_SENSITIVE)
    .setVisibility(NotificationCompat.VISIBILITY_SECRET)    // hide content on lock screen
    ...
```

---

## 11. Common Misses

| Miss | Fix |
|---|---|
| Token in plain storage without a threat-model decision | Direct Keystore-backed vault when encryption is required; otherwise short-lived private storage with server controls |
| Pinning without backup pins or a rotation plan | Add backup pins and overlapping rotation, or remove pinning |
| `usesCleartextTraffic=true` | Set to false |
| `allowBackup=true` carrying tokens | Exclude in backup rules |
| Logging tokens in OkHttp interceptor | Redact `Authorization` header |
| Screenshots possible on payment screen | `FLAG_SECURE` |
| Secrets shipped in the app (code, `BuildConfig`, resources) | Keep secrets server-side; restrict client keys |
| Wide-open deep link parser | Validate scheme + host |
| `runBlocking` on main exposing IO | Move to dispatcher |
| Storing biometric template (you can't) | Use Keystore-bound key + BiometricPrompt instead |

---

## 12. Testing & Audits

- **Static**: `Detekt`, `Lint`, OWASP Mobile checks in CI.
- **Dynamic**: MobSF (Mobile Security Framework), Frida-based runtime tests.
- **Pen-test**: annual by an external firm; high-stakes products quarterly.
- **Dependency scan**: `OWASP Dependency-Check`, `Snyk`, `Dependabot`.

---

## 13. Further Reading

- [Android Developers — Security best practices](https://developer.android.com/privacy-and-security/security-best-practices) — official baseline.
- [Android Developers — Security with network protocols](https://developer.android.com/privacy-and-security/security-ssl) — why certificate pinning is not recommended by default.
- [Android Keystore system](https://developer.android.com/training/articles/keystore) — key storage internals.
- [Network Security Configuration](https://developer.android.com/training/articles/security-config) — pinning + TLS.
- [Play Integrity API](https://developer.android.com/google/play/integrity) — integrity verification.
- [OWASP Mobile Top 10](https://owasp.org/www-project-mobile-top-10/) — vulnerability checklist.

---

> **In short:** security is defense in depth — TLS + pinning, Keystore-wrapped storage, biometric for sensitive actions, FLAG_SECURE on payment, R8 obfuscation, Play Integrity for high-stakes flows, consent gates everywhere. Privacy is minimisation + redaction + a delete path. Test annually; gate in CI; never log credentials.

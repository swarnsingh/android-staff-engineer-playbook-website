# Security: Secure Storage on Android

> How to store secrets on Android so that a rooted device, an `adb backup`, or a compromised TLS proxy can't lift them. Keystore is the foundation; everything else is a wrapper around it.

---

## 1. The Threat Model

Android isolates apps by UID — App A can't read App B's files. That promise dies when:

- The device is **rooted** (user or malware has UID 0).
- The user installs an **MDM profile** or **debugging proxy** that bypasses sandbox.
- An attacker pulls the data partition via **fastboot** or **physical extraction**.
- **`adb backup`** dumps app data (off by default since Android 6+, but still possible).
- A bug in the OS lets one app **MAP another app's files** (rare but real).

The goal of secure storage: even if the file on disk is stolen, the secret inside is useless without a key that the attacker can't extract. That key lives in the **Android Keystore**.

---

## 2. The Storage Tiers

| Tier | Use for | Backed by |
|---|---|---|
| **In-memory only** | Short-lived secrets that re-fetch | RAM (lost on process death) |
| **`SharedPreferences` / `DataStore` plain** | Non-sensitive (theme, locale, last screen) | Plain XML / Protobuf on disk |
| **`EncryptedSharedPreferences`** | Tokens, PII, app secrets | Keystore-wrapped AES-GCM |
| **`DataStore` + Tink** | Tokens (modern alternative to EncryptedSharedPreferences) | Keystore-wrapped AEAD |
| **Room + SQLCipher** | Queryable encrypted data (messages, notes) | Keystore-wrapped passphrase |
| **Keystore direct** | Cryptographic keys themselves | Hardware TEE / StrongBox |

> **Rule of thumb:** don't roll your own Keystore + Cipher code. The Jetpack Security and Tink libraries get IV management, padding, and authentication-tag handling correct. Direct Keystore API is for cases where the higher-level libraries don't fit.

### Storage decision matrix

Pick storage by consequence of compromise, not by convenience.

| Data | Storage | Additional control |
|---|---|---|
| Theme, locale, onboarding flags | Plain DataStore | None |
| Access token | Encrypted DataStore or EncryptedSharedPreferences | Short TTL |
| Refresh token | Encrypted storage + rotation | Reuse detection server-side |
| Drafts / offline user content | Room, optionally SQLCipher | Backup/delete policy |
| Payment or wallet material | Biometric-bound Keystore key or server custody | Step-up and attestation |
| Analytics/user identifiers | Minimized plain or encrypted store | Consent and reset path |

No storage tier protects against a malicious app process that already has the token in memory. Do not log decrypted values, expose them through crash breadcrumbs, or keep them in singleton fields longer than needed.

---

## 3. EncryptedSharedPreferences (the default for tokens)

```kotlin
// build.gradle.kts
dependencies {
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
}
```

```kotlin
class KeystoreTokenVault @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val masterKey: MasterKey by lazy {
        MasterKey.Builder(context, "app_master_key")
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .setRequestStrongBoxBacked(true)        // dedicated security chip if available
            .build()
    }

    private val prefs: SharedPreferences by lazy {
        EncryptedSharedPreferences.create(
            context,
            "secure_tokens",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    suspend fun saveAccessToken(token: String) = withContext(Dispatchers.IO) {
        prefs.edit().putString(KEY_ACCESS, token).commit()
    }

    suspend fun loadAccessToken(): String? = withContext(Dispatchers.IO) {
        prefs.getString(KEY_ACCESS, null)
    }

    suspend fun clear() = withContext(Dispatchers.IO) {
        prefs.edit().clear().commit()
    }

    companion object {
        private const val KEY_ACCESS = "access_token"
    }
}
```

### What's happening underneath

1. `MasterKey.Builder` requests a Keystore-resident AES-256-GCM key. On StrongBox-capable devices (Pixel 3+, Samsung S20+, etc.), the key lives in a dedicated tamper-resistant chip.
2. `EncryptedSharedPreferences.create` derives sub-keys from the master key for *keys* (deterministic AES-SIV so the same logical key always hashes the same way) and *values* (randomized AES-GCM so the same value encrypts differently each time).
3. Files on disk look like: `secure_tokens.xml` containing base64 ciphertext. Useless without the Keystore master key.

### What it does NOT protect against

- A user-confirmed biometric prompt unlocks the device → the master key is available → the cipher works. Lock screen is your last line of defense against physical theft.
- Memory dumps while the app is running (the decrypted plaintext is in heap briefly).
- Logic bugs (logging the token after decrypting).

---

## 4. DataStore + Tink (modern alternative)

`EncryptedSharedPreferences` is in maintenance mode. For new code, prefer DataStore with a Tink-wrapped serializer:

```kotlin
// build.gradle.kts
implementation("androidx.datastore:datastore:1.1.1")
implementation("com.google.crypto.tink:tink-android:1.13.0")
```

```kotlin
object TokensSerializer : Serializer<Tokens> {
    override val defaultValue: Tokens = Tokens.getDefaultInstance()

    override suspend fun readFrom(input: InputStream): Tokens {
        val bytes = input.readBytes()
        val plaintext = aead.decrypt(bytes, /* associatedData = */ null)
        return Tokens.parseFrom(plaintext)
    }

    override suspend fun writeTo(t: Tokens, output: OutputStream) {
        val plaintext = t.toByteArray()
        val ciphertext = aead.encrypt(plaintext, null)
        output.write(ciphertext)
    }

    private val aead: Aead by lazy {
        AeadConfig.register()
        AndroidKeysetManager.Builder()
            .withSharedPref(context, "tokens_keyset", "tokens_prefs")
            .withKeyTemplate(KeyTemplates.get("AES256_GCM"))
            .withMasterKeyUri("android-keystore://app_master_key")
            .build()
            .keysetHandle
            .getPrimitive(Aead::class.java)
    }
}

val Context.tokensStore: DataStore<Tokens> by dataStore(
    fileName = "tokens.pb",
    serializer = TokensSerializer,
)
```

Pros: typed (Proto), coroutine-native, no `SharedPreferences` legacy footguns.
Cons: more setup; Tink dependency.

---

## 5. Room + SQLCipher (encrypted database)

For queryable encrypted data (e.g., chat messages, notes):

```kotlin
// build.gradle.kts
implementation("net.zetetic:android-database-sqlcipher:4.5.4")
implementation("androidx.sqlite:sqlite-ktx:2.4.0")
```

```kotlin
class EncryptedRoomBuilder @Inject constructor(
    @ApplicationContext private val context: Context,
    private val passphraseVault: PassphraseVault,
) {
    fun build(): AppDatabase {
        val passphrase: ByteArray = passphraseVault.getOrCreate()
        val factory = SupportFactory(passphrase, /* hook = */ null, /* clearPassphrase = */ true)
        return Room.databaseBuilder(context, AppDatabase::class.java, "encrypted.db")
            .openHelperFactory(factory)
            .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
            .fallbackToDestructiveMigrationOnDowngrade()
            .build()
    }
}

class PassphraseVault @Inject constructor(@ApplicationContext ctx: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        ctx, "db_passphrase",
        MasterKey.Builder(ctx).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun getOrCreate(): ByteArray {
        prefs.getString(KEY_PASSPHRASE, null)?.let {
            return Base64.decode(it, Base64.NO_WRAP)
        }
        val bytes = ByteArray(32).also { SecureRandom().nextBytes(it) }
        prefs.edit().putString(KEY_PASSPHRASE, Base64.encodeToString(bytes, Base64.NO_WRAP)).commit()
        return bytes
    }

    companion object { private const val KEY_PASSPHRASE = "passphrase" }
}
```

The passphrase is 32 random bytes, generated once on install, wrapped by the Keystore master key (via `EncryptedSharedPreferences`), used to open SQLCipher. The on-disk `.db` file is AES-256-CBC encrypted; queries work normally.

---

## 6. Biometric-Bound Keys (the strongest tier)

For high-stakes secrets (banking auth, wallet seeds), the Keystore key itself should require biometric auth to use:

```kotlin
class BiometricKeystoreKey @Inject constructor() {

    fun createKey() {
        val keyGen = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
        )
        keyGen.init(
            KeyGenParameterSpec.Builder(
                "biometric_key",
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setUserAuthenticationRequired(true)
                .setUserAuthenticationParameters(
                    /* timeoutSeconds = */ 0,
                    KeyProperties.AUTH_BIOMETRIC_STRONG
                )
                .setInvalidatedByBiometricEnrollment(true)
                .setIsStrongBoxBacked(true)        // request StrongBox; falls back silently
                .build()
        )
        keyGen.generateKey()
    }

    suspend fun encrypt(activity: FragmentActivity, plaintext: ByteArray): ByteArray? {
        val key = (KeyStore.getInstance("AndroidKeyStore")
            .apply { load(null) })
            .getKey("biometric_key", null) as SecretKey

        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.ENCRYPT_MODE, key)
        }

        val result = authenticate(activity, cipher) ?: return null

        return result.cipher!!.doFinal(plaintext).let { ct ->
            // Prepend IV for later decryption
            cipher.iv + ct
        }
    }

    private suspend fun authenticate(
        activity: FragmentActivity,
        cipher: Cipher,
    ): BiometricPrompt.AuthenticationResult? = suspendCancellableCoroutine { cont ->
        val prompt = BiometricPrompt(
            activity, ContextCompat.getMainExecutor(activity),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    cont.resume(result) {}
                }
                override fun onAuthenticationError(code: Int, msg: CharSequence) {
                    cont.resume(null) {}
                }
            }
        )
        prompt.authenticate(
            BiometricPrompt.PromptInfo.Builder()
                .setTitle("Authenticate to access")
                .setNegativeButtonText("Cancel")
                .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
                .build(),
            BiometricPrompt.CryptoObject(cipher)
        )
    }
}
```

Key properties to call out:
- `setUserAuthenticationRequired(true)`: every use of the key requires biometric.
- `setUserAuthenticationParameters(0, AUTH_BIOMETRIC_STRONG)`: 0 timeout = per-use auth; Class 3 (strong).
- `setInvalidatedByBiometricEnrollment(true)`: adding a new fingerprint **destroys** the key — handle `KeyPermanentlyInvalidatedException`.

---

## 7. Key Invalidation Recovery

```kotlin
suspend fun safeDecrypt(activity: FragmentActivity, ciphertext: ByteArray): ByteArray? {
    return try {
        biometricKey.decrypt(activity, ciphertext)
    } catch (e: KeyPermanentlyInvalidatedException) {
        // User added/removed a fingerprint, or removed lockscreen — the key is dead.
        // Wipe ciphertext that depended on it, re-create the key, force re-enroll.
        tokenVault.clear()
        biometricKey.deleteKey()
        biometricKey.createKey()
        navigator.replaceWithReAuth(reason = ReAuthReason.BIOMETRIC_ENROLLMENT)
        null
    } catch (e: UserNotAuthenticatedException) {
        // Lockscreen-bound key, user hasn't unlocked recently. Prompt then retry.
        biometricKey.decrypt(activity, ciphertext)
    }
}
```

If you don't handle `KeyPermanentlyInvalidatedException`, the user crashes the app every time they pull down notifications after enrolling a new face.

---

## 8. Backup Exclusion

Auto Backup propagates `SharedPreferences` to Google Drive by default. Tokens stored there land on every other device the user signs into.

```xml
<!-- AndroidManifest.xml -->
<application
    android:allowBackup="true"
    android:fullBackupContent="@xml/backup_rules"
    android:dataExtractionRules="@xml/data_extraction_rules"
    ...>
```

```xml
<!-- res/xml/backup_rules.xml (Android 11 and below) -->
<full-backup-content>
    <exclude domain="sharedpref" path="secure_tokens.xml" />
    <exclude domain="sharedpref" path="db_passphrase.xml" />
    <exclude domain="file" path="encrypted.db" />
    <exclude domain="file" path="encrypted.db-journal" />
</full-backup-content>
```

```xml
<!-- res/xml/data_extraction_rules.xml (Android 12+) -->
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="sharedpref" path="secure_tokens.xml" />
        <exclude domain="sharedpref" path="db_passphrase.xml" />
        <exclude domain="file" path="encrypted.db" />
    </cloud-backup>
    <device-transfer>
        <!-- Same exclusions; device transfer also copies user data. -->
        <exclude domain="sharedpref" path="secure_tokens.xml" />
        <exclude domain="sharedpref" path="db_passphrase.xml" />
        <exclude domain="file" path="encrypted.db" />
    </device-transfer>
</data-extraction-rules>
```

Test by triggering backup: `adb shell bmgr backupnow <your-package>`.

---

## 9. StrongBox vs TEE vs Software

| Backing | Where | Pixel | Samsung | Mid-range |
|---|---|---|---|---|
| **StrongBox** | Dedicated secure chip (Titan M on Pixel, Knox on Samsung) | 3+ | S20+ | varies |
| **TEE** | ARM TrustZone inside the SoC | All | All | Most modern |
| **Software** | JVM heap (basically plaintext) | Pre-7.0 | Pre-7.0 | Some emulators |

Code defensively: `setRequestStrongBoxBacked(true)` requests StrongBox but silently falls back. You can detect what backing you got via `KeyInfo.isInsideSecureHardware`.

```kotlin
fun keyBacking(alias: String): KeyBacking {
    val key = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        .getKey(alias, null) as SecretKey
    val factory = SecretKeyFactory.getInstance(key.algorithm, "AndroidKeyStore")
    val info = factory.getKeySpec(key, KeyInfo::class.java) as KeyInfo
    return when {
        info.securityLevel == KeyProperties.SECURITY_LEVEL_STRONGBOX -> KeyBacking.STRONGBOX
        info.isInsideSecureHardware -> KeyBacking.TEE
        else -> KeyBacking.SOFTWARE
    }
}
```

Surface this in telemetry — fleets with high software-backing rates need policy decisions (block? warn? accept?).

---

## 10. Common Pitfalls

- **Hardcoding secrets in source.** `const val API_KEY = "..."` survives R8 obfuscation but not `jadx`. Never embed long-lived secrets; generate per-device via Keystore or fetch from server post-auth.
- **Storing the encryption key alongside ciphertext.** `EncryptedSharedPreferences` does this correctly (key in Keystore). DIY implementations often store the key in plain `SharedPreferences` next to the ciphertext — useless.
- **Not handling `KeyPermanentlyInvalidatedException`.** Users add fingerprints. Your app must recover.
- **Forgetting `clearPassphrase = true`** on SQLCipher's `SupportFactory`. Without it, the passphrase ByteArray stays in heap.
- **Using `EncryptedSharedPreferences` for high-frequency reads.** Each `getString` decrypts. Cache the result in memory for the session.
- **Not excluding secure files from backup.** Tokens replicate to every device on the user's Google account.
- **Logging tokens in OkHttp interceptors.** `HttpLoggingInterceptor.Level.HEADERS` includes `Authorization`. Use a redacting interceptor in production.
- **Trusting `BuildConfig.DEBUG` for security gating.** R8 strips `if (BuildConfig.DEBUG)` blocks but only if `isMinifyEnabled = true`. Verify.
- **Assuming root detection is a security boundary.** It's a deterrent at best. Defend at the data layer (Keystore), not at the process layer.

---

## 11. Testing

```kotlin
@RunWith(AndroidJUnit4::class)
class KeystoreTokenVaultTest {
    @Test
    fun roundTrip_preservesToken() = runBlocking {
        val vault = KeystoreTokenVault(InstrumentationRegistry.getInstrumentation().targetContext)
        vault.saveAccessToken("eyJhbGc...")
        assertEquals("eyJhbGc...", vault.loadAccessToken())
        vault.clear()
        assertNull(vault.loadAccessToken())
    }
}
```

Run on a real device (emulators have weaker Keystore guarantees; some emulators are software-only).

For pen-test simulation:
- Pull `secure_tokens.xml` via `adb` from a rooted emulator.
- Try to decrypt without the Keystore — should be infeasible.
- Try `KeyPermanentlyInvalidatedException` flow by enrolling a new fingerprint mid-session.

---

## 12. Further Reading

- [Android Developers — Encrypt and authenticate stored data](https://developer.android.com/topic/security/data) — official guide for AndroidX Security.
- [Android Developers — Android Keystore system](https://developer.android.com/training/articles/keystore) — Keystore concepts.
- [SQLCipher for Android](https://www.zetetic.net/sqlcipher/sqlcipher-for-android/) — encrypted SQLite.
- [Google Tink](https://developers.google.com/tink) — modern crypto wrapper used in DataStore patterns.
- [OWASP Mobile Top 10 — M9 Insecure Data Storage](https://owasp.org/www-project-mobile-top-10/) — checklist of common storage failures.

---

> **In short:** Keystore-resident keys + library-managed encryption (`EncryptedSharedPreferences`, DataStore+Tink, SQLCipher). Never roll your own cipher. Always exclude from backup. Always handle key invalidation. Always log telemetry on key backing so you know what your fleet runs on.

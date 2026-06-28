# Security: Key Management & Secrets on Android

> How to handle secrets on a device you don't control. The hard rule: any secret embedded in the APK is extractable. Plan accordingly.

---

## 1. The Threat Model

The client runs on hardware the attacker owns. Any constant in your `.dex`, `.so`, or resources can be lifted with `jadx`, Ghidra, or `apktool` in minutes. Obfuscation slows extraction by hours, not days. So the design question is not "how do I hide this key" but "what classes of key am I willing to expose."

| Secret class | Strategy |
|---|---|
| Per-user, per-session secrets | Issue server-side post-auth; cache in Keystore-wrapped storage |
| Per-device long-lived secrets | Generate on-device in Keystore; key material never leaves the chip |
| Third-party API keys with billing implications | Never embed; proxy via your backend |
| Build-time identifiers (Maps, Firebase) | Embed; restrict by package + SHA-1 in the vendor console |
| App-signing private key | Play App Signing (Google holds it); upload key stored in HSM you control |

> **Mantra:** the only secret safe on a phone is a secret derived from the user (PIN, biometric-bound key, or session token tied to their account).

---

## 2. Build-Time Constants vs Runtime Secrets

```kotlin
// build.gradle.kts
android {
    defaultConfig {
        buildConfigField("String", "MAPS_API_KEY", "\"${localProperty("MAPS_API_KEY")}\"")
        manifestPlaceholders["mapsApiKey"] = localProperty("MAPS_API_KEY")
    }
    buildFeatures { buildConfig = true }
}

fun localProperty(key: String): String {
    val props = Properties()
    val file = rootProject.file("local.properties")
    if (file.exists()) props.load(file.inputStream())
    return props.getProperty(key) ?: System.getenv(key) ?: ""
}
```

```kotlin
// local.properties (NEVER committed — listed in .gitignore)
MAPS_API_KEY=AIzaSy...REDACTED
```

```kotlin
// CI provides via environment variables
// .github/workflows/release.yml
//   env:
//     MAPS_API_KEY: ${{ secrets.MAPS_API_KEY }}
```

This pattern keeps the key out of git but **does not** keep it out of the APK. Restrict the Maps key in Google Cloud Console by app package + signing-cert SHA-1. Restrict Firebase via Security Rules + App Check. The key on disk is a junk identifier without the restrictions.

---

## 3. Per-Device Key Generation (the Keystore)

For symmetric encryption keys used to wrap on-device data:

```kotlin
class DeviceSymmetricKey @Inject constructor() {

    private val keystore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    fun getOrCreate(alias: String): SecretKey {
        keystore.getKey(alias, null)?.let { return it as SecretKey }
        return generate(alias)
    }

    private fun generate(alias: String): SecretKey {
        val keyGen = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
        )
        keyGen.init(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .setIsStrongBoxBacked(true)             // dedicated chip if available
                .setRandomizedEncryptionRequired(true)  // forces unique IV per encryption
                .build()
        )
        return keyGen.generateKey()
    }

    fun delete(alias: String) {
        keystore.deleteEntry(alias)
    }
}
```

The key material is generated **inside** the secure element. Your code receives a `SecretKey` handle — a Java reference, not the bytes. Use it via `Cipher`:

```kotlin
class GcmCipher @Inject constructor(private val keys: DeviceSymmetricKey) {
    private val keyAlias = "wallet_data_v1"

    fun encrypt(plaintext: ByteArray): EncryptedBlob {
        val key = keys.getOrCreate(keyAlias)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.ENCRYPT_MODE, key)
        }
        return EncryptedBlob(iv = cipher.iv, ciphertext = cipher.doFinal(plaintext))
    }

    fun decrypt(blob: EncryptedBlob): ByteArray {
        val key = keys.getOrCreate(keyAlias)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, blob.iv))
        }
        return cipher.doFinal(blob.ciphertext)
    }
}

data class EncryptedBlob(val iv: ByteArray, val ciphertext: ByteArray)
```

> **Why GCM, not CBC.** GCM is authenticated encryption: tamper with the ciphertext and `doFinal` throws. CBC requires a separate HMAC; easy to get wrong. Always GCM for new code.

---

## 4. Asymmetric Keys (For Signing)

When the backend needs to verify "this request really came from this device":

```kotlin
class DeviceSigningKey @Inject constructor() {

    fun create(alias: String): KeyPair {
        val gen = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore"
        )
        gen.initialize(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
            )
                .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
                .setDigests(KeyProperties.DIGEST_SHA256)
                .setIsStrongBoxBacked(true)
                .setAttestationChallenge(challengeFromServer())  // for Key Attestation
                .build()
        )
        return gen.generateKeyPair()
    }

    fun sign(alias: String, payload: ByteArray): ByteArray {
        val key = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            .getKey(alias, null) as PrivateKey
        return Signature.getInstance("SHA256withECDSA").run {
            initSign(key)
            update(payload)
            sign()
        }
    }

    fun publicKey(alias: String): PublicKey =
        KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            .getCertificate(alias).publicKey

    fun attestationCertChain(alias: String): List<Certificate> =
        KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            .getCertificateChain(alias).toList()
}
```

Server flow:
1. Backend issues a `challenge` (nonce).
2. Client creates an EC key pair in Keystore, includes `setAttestationChallenge(challenge)`.
3. Client uploads the resulting cert chain to the backend.
4. Backend walks the chain to Google's hardware root, extracts the **attestation extension**, verifies the challenge matches and that the key lives in a TEE/StrongBox.
5. From now on, the client signs requests with this key; backend verifies with the registered public key.

See `attestation.md` for the chain verification details.

---

## 5. Biometric-Bound Keys

When the key should only be usable after the *user* authenticates (per-use), not just because the app is running:

```kotlin
.setUserAuthenticationRequired(true)
.setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
.setInvalidatedByBiometricEnrollment(true)
```

The cipher is unusable until `BiometricPrompt` succeeds with the `CryptoObject`. See `secure-storage-on-android.md` for the full prompt code.

`setInvalidatedByBiometricEnrollment(true)` is a hard tradeoff: every fingerprint enroll wipes the key. If you can't tolerate that, drop it — but then a thief who can add a fingerprint can decrypt.

---

## 6. The Backend Proxy Pattern (For Third-Party API Keys)

You bought a paid API. The vendor charges per call. The key is in your APK. A motivated attacker extracts it and runs up your bill.

**Don't ship vendor secrets to the client.** Stand up a proxy in your backend:

```
Mobile  ──── Bearer (your auth) ────►  Your BFF  ──── Vendor API key ────►  Vendor
        ◄──────── proxied response ─────────────────────────────────────
```

The BFF:
- Authenticates the user against your system.
- Rate-limits per user.
- Adds the vendor API key.
- Forwards the request and proxies the response back.

You pay the latency cost (one extra hop). You gain billing safety, central rate-limiting, and the ability to swap vendors without an app release.

The only secrets you put in the APK are vendor identifiers that are *meant* to be public (Firebase config, Maps API key with package restriction, etc.).

---

## 7. Secret Rotation

A leaked symmetric key needs rotation. Pattern:

```kotlin
class RotatableKey @Inject constructor(...) {
    suspend fun encryptForNewKey(plaintext: ByteArray): EncryptedBlob {
        val currentAlias = config.currentEncryptionKeyAlias()  // from feature flag
        return cipher.encrypt(plaintext, alias = currentAlias)
    }

    suspend fun decrypt(blob: VersionedEncryptedBlob): ByteArray {
        // Old payloads carry a version; pick the right key by version.
        val alias = config.keyAliasForVersion(blob.version)
        return cipher.decrypt(blob, alias = alias)
    }
}
```

Each new version of the encryption key gets a new alias (`wallet_data_v1`, `wallet_data_v2`). On read, look up the right key by version. On write, always use the current.

For server-side secrets (API keys you embed for vendor restrictions), rotate via a release with both keys hot, then retire the old after telemetry confirms the new is in use everywhere.

---

## 8. App Signing Keys (The One Key You Cannot Lose)

Your app-signing private key is what proves "this APK is from your team." Lose it → you cannot ship updates that current users can install. Leak it → attackers can publish malicious updates that current users install seamlessly.

**Use Play App Signing.**

1. You generate the *upload* key (`keytool`, stored in your CI HSM).
2. Google generates the *app-signing* key (held in their HSM, never exported).
3. You sign uploads with the upload key. Google strips, re-signs with the app-signing key, and distributes.

Benefits:
- Lost upload key → request a reset from Google (proof of identity required).
- Compromised upload key → request a key rotation; Google issues a new signing identity that supersedes the old; you publish releases signed with the new key going forward.
- Hardware HSM (Cloud KMS or AWS CloudHSM) for the upload key in CI; never in a developer laptop.

---

## 9. Common Pitfalls

- **`google-services.json` committed and confused for "a secret".** It's an identifier, not a secret. The actual security comes from Firebase Security Rules + App Check. But `firebase_credentials.json` (the *server* private key) IS a secret — don't confuse them.
- **Single shared API key for all users.** A leak means rotation breaks every install. Issue per-user, per-session tokens instead.
- **Storing the *unwrapped* key alongside the ciphertext.** EncryptedSharedPreferences gets this right; DIY usually doesn't.
- **No `setRandomizedEncryptionRequired(true)`.** Identical plaintexts encrypt to identical ciphertexts — an attacker observes "ah, that's another `4242 4242` card number."
- **AES-CBC without HMAC.** Authenticate or use GCM. CBC alone is a footgun.
- **Embedding the upload key in the repo.** Even password-protected. Use Play App Signing + HSM-backed CI secrets.
- **Trusting "obfuscation" to hide secrets.** R8 renames classes; it doesn't remove `String` constants from the constant pool.
- **Long-lived signing keys in dev laptops.** If a dev is phished and their laptop drive is exfiltrated, the upload key goes with it. CI-only access; rotation policy.
- **Not labeling key versions.** Rotating requires reading old ciphertext. If you don't version, you can't migrate gracefully.

---

## 10. Inventory: What Secrets Exist?

Before any of this is useful, audit:

```
APK secrets:
  - MAPS_API_KEY              build-time, package-restricted
  - FIREBASE_APP_ID           public identifier
  - SENTRY_DSN                public ingest endpoint (rate-limited)
  - (No third-party API secrets)

Server-issued runtime:
  - OAuth access token        15 min
  - OAuth refresh token       30 days
  - FCM device token          rotates server-side

On-device generated:
  - Keystore: wallet_data_v1  AES-256-GCM, StrongBox where avail
  - Keystore: device_signing  EC P-256, attested

CI / build:
  - Upload key                in Cloud KMS, accessed only by release workflow
  - Play store API key        in secret manager, scoped to release pipeline
```

Track ownership, rotation cadence, and where each lives. A spreadsheet beats nothing.

---

## 11. Testing

```kotlin
@Test
fun keystore_keyMaterial_doesNotEnterJvmHeap() {
    val keys = DeviceSymmetricKey()
    val key = keys.getOrCreate("test_alias")
    // SecretKey.getEncoded() returns null for Keystore keys — by design.
    assertNull(key.encoded)
}

@Test
fun encrypt_decrypt_roundTrip() {
    val cipher = GcmCipher(DeviceSymmetricKey())
    val plaintext = "hello world".toByteArray()
    val blob = cipher.encrypt(plaintext)
    assertContentEquals(plaintext, cipher.decrypt(blob))
}

@Test
fun gcm_authenticationFailureThrows() {
    val cipher = GcmCipher(DeviceSymmetricKey())
    val blob = cipher.encrypt("hello".toByteArray())
    val tampered = blob.copy(ciphertext = blob.ciphertext.copyOf().also { it[0] = it[0].inc() })
    assertFailsWith<AEADBadTagException> { cipher.decrypt(tampered) }
}
```

For build-time keys: a release-build smoke test that asserts the APK does NOT contain known test/staging keys (string-scan the final APK as part of release pipeline).

---

## 12. Further Reading

- [Android Developers — Android Keystore system](https://developer.android.com/training/articles/keystore) — Keystore concepts.
- [Android Developers — Hardware-backed Keystore](https://source.android.com/docs/security/features/keystore) — StrongBox & TEE.
- [Play App Signing](https://support.google.com/googleplay/android-developer/answer/9842756) — how Google holds the signing key.
- [OWASP — Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) — algorithm choices.
- [Google Cloud KMS](https://cloud.google.com/kms) / [AWS KMS](https://aws.amazon.com/kms/) — for CI-side secret storage.

---

> **In short:** generate keys in the Keystore, never in your code. Use AES-GCM for confidentiality+authentication. Use EC for signatures. Issue session-scoped tokens server-side. Proxy third-party APIs. Use Play App Signing. Inventory and rotate.

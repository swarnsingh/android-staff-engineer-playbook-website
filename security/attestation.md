# Security: App + Device Attestation (Play Integrity, Key Attestation)

> How a server tells a real install of your app on a real device apart from an attacker's Python script. Play Integrity + Keystore Key Attestation are the two tools; both need server-side verification to mean anything.

---

## 1. The Threat Model

A backend receives a request claiming "send $500 to alice." Auth alone proves a valid token. It doesn't prove:

- The request came from your real APK (not a tampered copy with the rate limiter removed).
- The request came from a real Android device (not an emulator farm).
- The device's bootloader is locked and the OS isn't rooted.
- The user actually performed the action (vs. a script running in the background).

Attestation answers some of these — but only when the server holds the verdict, not the client.

### What attestation is not

Attestation is a risk signal, not a magic "safe device" stamp.

| Misuse | Problem |
|---|---|
| Client checks its own verdict | A modified client can skip the check |
| Attesting every request | Quota, latency, battery, and poor UX |
| Blocking all non-strong devices | Excludes legitimate users on older/low-end devices |
| Treating attestation as fraud detection | It says something about app/device integrity, not user intent |
| Ignoring nonce binding | Captured verdicts become replayable |

Use attestation to raise or lower risk: allow, step-up, limit, delay, or reject. For many consumer apps, `DEVICE` integrity plus behavioral/risk signals is better than requiring `STRONG` everywhere.

---

## 2. The Two Attestation Surfaces

| Tool | What it proves | Where you call it |
|---|---|---|
| **Play Integrity API** | App is unmodified, signed by you, installed via Play, on Android with a verdict tier (basic/device/strong) | At sensitive checkpoints (login, transfer, account change) |
| **Keystore Key Attestation** | A specific key was generated in hardware (TEE / StrongBox) of a specific genuine device | Once at device enrollment; thereafter you trust the signed nonce |

Play Integrity gives a global "is this device + app legit" check per call. Key Attestation cryptographically binds a *key* you registered to the device — for ongoing signed requests.

---

## 3. Play Integrity API

```kotlin
// build.gradle.kts
implementation("com.google.android.play:integrity:1.4.0")
```

```kotlin
class PlayIntegrityClient @Inject constructor(
    @ApplicationContext private val context: Context,
    private val api: BackendApi,
) {

    suspend fun obtainTokenAndSubmit(action: SensitiveAction): IntegrityResult {
        val nonce = api.requestNonce(action)            // server-issued, single-use, 5-min TTL
        val manager = IntegrityManagerFactory.create(context)
        val request = IntegrityTokenRequest.builder()
            .setNonce(nonce.value)
            .setCloudProjectNumber(BuildConfig.GCP_PROJECT_NUMBER)
            .build()

        val response = manager.requestIntegrityToken(request).await()
        return api.submitIntegrityToken(
            action = action,
            nonce = nonce.value,
            integrityToken = response.token(),
        )
    }
}

private suspend fun <T> Task<T>.await(): T = suspendCancellableCoroutine { cont ->
    addOnSuccessListener { cont.resume(it) }
    addOnFailureListener { cont.resumeWithException(it) }
}
```

The client never reads the token contents. It hands it back to your server.

---

## 4. Server-Side Verification (The Critical Half)

The integrity token is an encrypted JWE. The server decrypts (via Google's API) and inspects the payload:

```json
{
  "requestDetails": {
    "requestPackageName": "com.example.app",
    "timestampMillis": "1750000000123",
    "nonce": "abc123..."
  },
  "appIntegrity": {
    "appRecognitionVerdict": "PLAY_RECOGNIZED",
    "packageName": "com.example.app",
    "certificateSha256Digest": ["..."],
    "versionCode": "1234"
  },
  "deviceIntegrity": {
    "deviceRecognitionVerdict": ["MEETS_DEVICE_INTEGRITY", "MEETS_STRONG_INTEGRITY"]
  },
  "accountDetails": {
    "appLicensingVerdict": "LICENSED"
  }
}
```

Server-side enforcement (pseudocode):

```kotlin
fun verifyIntegrity(token: String, expectedNonce: String, action: SensitiveAction): VerdictDecision {
    val payload = playApi.decodeIntegrityToken(token)

    // 1. Nonce binding
    if (payload.requestDetails.nonce != expectedNonce) {
        return VerdictDecision.Reject("nonce mismatch")
    }
    if (now() - payload.requestDetails.timestampMillis > MAX_AGE_MS) {
        return VerdictDecision.Reject("token too old")
    }

    // 2. Package binding
    if (payload.appIntegrity.packageName != "com.example.app") {
        return VerdictDecision.Reject("wrong package")
    }

    // 3. App identity
    if (payload.appIntegrity.appRecognitionVerdict != "PLAY_RECOGNIZED") {
        return VerdictDecision.Reject("modified APK")
    }
    if (payload.appIntegrity.certificateSha256Digest.none { it in trustedSigningCerts }) {
        return VerdictDecision.Reject("wrong signing cert")
    }

    // 4. Device integrity (policy varies by action)
    val verdicts = payload.deviceIntegrity.deviceRecognitionVerdict.toSet()
    when (action.requiredTier) {
        Tier.STRONG -> if ("MEETS_STRONG_INTEGRITY" !in verdicts) return VerdictDecision.Reject("requires StrongBox")
        Tier.DEVICE -> if ("MEETS_DEVICE_INTEGRITY" !in verdicts) return VerdictDecision.Reject("device not trusted")
        Tier.BASIC -> if ("MEETS_BASIC_INTEGRITY" !in verdicts) return VerdictDecision.Reject("basic integrity failed")
    }

    // 5. Burn the nonce so it can't be replayed
    nonceStore.consume(expectedNonce)

    return VerdictDecision.Accept
}
```

The verdict tiers ratchet:
- **`MEETS_BASIC_INTEGRITY`**: device passes minimal checks; might be rooted/emulator-like.
- **`MEETS_DEVICE_INTEGRITY`**: genuine Android device, bootloader locked, recent system update.
- **`MEETS_STRONG_INTEGRITY`**: above + hardware-backed Keystore + recent attestation.

Match the tier to the action. Reading a feed: `BASIC` is fine. Transferring money: require `DEVICE` or `STRONG`.

---

## 5. Nonce Discipline

Without a server-issued nonce, an attacker can:
1. Capture an integrity token from a legitimate device.
2. Replay it from a Python script forever.

The pattern:

```kotlin
// Server
fun requestNonce(userId: String, action: SensitiveAction): Nonce {
    val value = secureRandom.base64UrlNoPad(32)
    val nonce = Nonce(value = value, userId = userId, action = action,
                      issuedAt = now(), consumed = false, ttlMs = 5 * 60 * 1000)
    nonceStore.put(nonce)
    return nonce
}

fun consumeNonce(value: String): Boolean {
    val nonce = nonceStore.get(value) ?: return false
    if (nonce.consumed) return false
    if (now() - nonce.issuedAt > nonce.ttlMs) return false
    nonceStore.markConsumed(value)
    return true
}
```

Single-use, short-lived, bound to (user, action). One captured token cannot service two requests.

---

## 6. Quota & Latency

Standard integrity requests have a 10K/day per-app quota. Premium (paid) is needed for high-volume. Plan accordingly:

- **Don't request on every API call.** Cache the verdict in a short-lived (e.g., 5 min) backend session.
- **Use Standard at low-stakes checkpoints**, Classic (legacy) for one-off, or Premium for high-volume real-time.
- **Latency is 200-1000 ms.** Don't block UI on it for low-friction flows; do block for transfers.

```kotlin
class IntegrityCache @Inject constructor() {
    suspend fun verdictFor(action: SensitiveAction, session: SessionId): VerdictDecision {
        val cached = sessionStore.get(session)?.recentIntegrity
        if (cached != null && now() - cached.timestamp < CACHE_MS) {
            return cached.verdict
        }
        val verdict = playIntegrityClient.obtainTokenAndSubmit(action)
        sessionStore.update(session) { it.copy(recentIntegrity = CachedVerdict(verdict, now())) }
        return verdict
    }
}
```

---

## 7. Keystore Key Attestation (Cryptographically Bound)

When you want a long-lived cryptographic identity for a device — sign requests with a key whose origin you've verified once — use Key Attestation.

### Client: create an attested key

```kotlin
fun createAttestedKey(alias: String, challenge: ByteArray): KeyPair {
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
            .setAttestationChallenge(challenge)       // ← key step
            .setIsStrongBoxBacked(true)
            .build()
    )
    return gen.generateKeyPair()
}

fun certificateChain(alias: String): List<X509Certificate> =
    (KeyStore.getInstance("AndroidKeyStore").apply { load(null) })
        .getCertificateChain(alias)
        .map { it as X509Certificate }
```

The challenge is a nonce your server issues. The Keystore generates a key pair AND produces an attestation certificate signed by Google's hardware root, embedding the challenge.

### Client: upload the chain

```kotlin
suspend fun registerDevice(alias: String) {
    val challenge = backend.requestAttestationChallenge()
    deviceSigningKey.createAttestedKey(alias, challenge.value)
    val chain = deviceSigningKey.certificateChain(alias).map { it.encoded.base64() }
    backend.registerDevice(
        userId = currentUser.id,
        keyAlias = alias,
        certificateChain = chain,
    )
}
```

### Server: verify the chain

The chain ends at a known Google root certificate. The server:

1. Verifies each cert in the chain signs the previous.
2. Walks to a hardware root known to be Google's.
3. Reads the **attestation extension** OID `1.3.6.1.4.1.11129.2.1.17`.
4. Confirms the embedded challenge matches the one it issued.
5. Confirms `securityLevel` is `TRUSTED_ENVIRONMENT` or `STRONG_BOX`.
6. Confirms `verifiedBootState` is `VERIFIED` (bootloader locked).
7. Confirms `packageName` matches your app.
8. Persists the leaf public key as the device's registered identity.

```kotlin
fun verifyAttestation(chain: List<X509Certificate>, expectedChallenge: ByteArray): VerifiedAttestation? {
    // 1. Chain trust
    val anchor = googleHardwareRoots.firstOrNull { it.matches(chain.last()) }
        ?: return null
    chain.zipWithNext().forEach { (child, parent) ->
        child.verify(parent.publicKey)
    }
    // 2. Read attestation extension
    val extn = chain.first().getExtensionValue("1.3.6.1.4.1.11129.2.1.17")
        ?: return null
    val parsed = ParsedAttestation(extn)
    // 3. Bindings
    if (!parsed.challenge.contentEquals(expectedChallenge)) return null
    if (parsed.attestationSecurityLevel !in listOf(SecurityLevel.TEE, SecurityLevel.STRONG_BOX)) return null
    if (parsed.softwareEnforced.attestationApplicationId.packageName != "com.example.app") return null
    if (parsed.teeEnforced.rootOfTrust.verifiedBootState != VerifiedBootState.VERIFIED) return null
    return VerifiedAttestation(
        leafPublicKey = chain.first().publicKey,
        securityLevel = parsed.attestationSecurityLevel,
    )
}
```

Open-source libraries like Google's `android-key-attestation` parse the extension; do not write the ASN.1 parser yourself.

### After registration

Server stores `(userId, deviceId, leafPublicKey)`. Subsequent sensitive requests:

```
Client:  POST /v1/transfer
         Body: { amount, recipient, nonce, signature = sign(privKey, hash(body+nonce)) }

Server:  Look up (userId, deviceId) → public key.
         Verify signature(public key, hash(body+nonce)).
         Consume nonce.
         Accept.
```

Now the server has cryptographic proof that the request came from a device whose hardware Keystore it has attested.

---

## 8. Combining the Two

| Action | Play Integrity | Key Attestation |
|---|---|---|
| Login | Optional (anti-bot) | Register a key after login |
| Read feed | No | No |
| Make a payment | Yes (`STRONG`) | Sign request with attested key |
| Account change | Yes (`DEVICE`) | Sign request with attested key |
| Background analytics | No | No |

Play Integrity is per-call snapshot; Key Attestation is durable identity. Use both for the highest-stakes flows.

---

## 9. Common Pitfalls

- **Client-side verdict check.** `if (token.meetsDeviceIntegrity()) { ... }` on the client is bypassed with Frida in 5 minutes. Always server-side.
- **No nonce.** Replays defeat the whole system. Server-issued, single-use, short TTL.
- **No `setAttestationChallenge`.** Without it, the cert chain doesn't bind the challenge; an attacker can present a chain from any device.
- **Trusting the leaf without walking to a hardware root.** Anyone can produce a self-signed cert. Walk the chain.
- **Not pinning the Google root cert list.** Google rotates these — stay current. Out-of-band updates.
- **Quota burnout.** Calling Play Integrity on every request burns through Standard quota. Cache the verdict per session.
- **Ignoring "soft" verdicts.** `BASIC` users on customs ROMs are real customers. Decide policy: block? warn? feature-restrict? Don't surprise them.
- **Forgetting attestation works on TEE only.** Pre-Android 8 has weaker attestation; older devices may fail `STRONG_INTEGRITY` even when "genuine."
- **Key Attestation is one-time.** Re-attestation only on key rotation. Don't repeat at every request.
- **Latency in critical paths.** Don't put a 1s Play Integrity call between "user taps Pay" and the bank API. Issue ahead of time or accept the friction.

---

## 10. Testing

```kotlin
@Test
fun signature_overNonce_isVerifiableByServer() {
    val keys = DeviceSigningKey()
    keys.createAttestedKey("test_alias", challenge = ByteArray(32) { it.toByte() })

    val nonce = "abc".toByteArray()
    val signature = keys.sign("test_alias", nonce)
    val publicKey = keys.publicKey("test_alias")

    val verifier = Signature.getInstance("SHA256withECDSA")
    verifier.initVerify(publicKey)
    verifier.update(nonce)
    assertTrue(verifier.verify(signature))
}
```

Server-side: fixtures of real attestation chains from various device classes. Unit-test the verification logic against each.

For Play Integrity, use the official sample app + a test backend that decrypts the token.

---

## 11. Further Reading

- [Play Integrity API](https://developer.android.com/google/play/integrity) — official.
- [Key Attestation](https://developer.android.com/privacy-and-security/security-key-attestation) — Android docs.
- [google/android-key-attestation](https://github.com/google/android-key-attestation) — server-side reference verifier.
- [Verified Boot](https://source.android.com/docs/security/features/verifiedboot) — what `verifiedBootState` means.
- [Play Integrity verdict tiers](https://developer.android.com/google/play/integrity/verdicts) — basic vs device vs strong.

---

> **In short:** Play Integrity for per-call "is this real" with a server-issued nonce, evaluated server-side; Key Attestation for "I cryptographically registered this device once." Pair them at the highest-stakes endpoints. Never trust the client's verdict.

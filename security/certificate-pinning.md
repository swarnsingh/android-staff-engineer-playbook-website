# Security: Certificate Pinning (Defeating Active MITM)

> How to make sure your app only talks to *your* servers, even when a hostile network or compromised CA issues a valid-looking certificate. Network Security Config + OkHttp `CertificatePinner` + a rotation discipline.

---

## 1. The Threat Model

TLS authenticates a server by checking the certificate chain against the OS root trust store. That store contains hundreds of CAs. Compromise any one of them, install a corporate MITM proxy, or trick the user into adding a rogue CA, and the OS-blessed `https://` connection lands on the attacker's server with a "valid" certificate.

Pinning collapses the trust set from "any CA Android trusts" to "the specific certificate(s) we provisioned." Even with a perfectly forged cert, the connection fails.

---

## 2. What Exactly You Pin

You don't pin the *certificate* (it rotates yearly). You pin the **SHA-256 hash of the SubjectPublicKeyInfo (SPKI)**. SPKI is the public-key portion of the cert; it can survive cert reissues if you re-use the same key pair (a "re-key").

```bash
# Extract SPKI hash from a live host
openssl s_client -servername api.example.com -connect api.example.com:443 < /dev/null \
  | openssl x509 -pubkey -noout \
  | openssl pkey -pubin -outform der \
  | openssl dgst -sha256 -binary \
  | openssl enc -base64

# Output:
# 7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y=
```

Pin this hash; not the cert's serial number, not the cert's full hash, not the issuer's CA. SPKI gives you the right balance: survives reissue-with-same-key, breaks if a new key pair is generated.

---

## 3. Network Security Config (Declarative, Manifest-Driven)

The simplest path, available since Android 7.0 (API 24). Pins live in XML; the platform enforces them on every HTTP stack.

```xml
<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>

    <!-- Hard fail any cleartext anywhere. -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Production pins -->
    <domain-config>
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2026-12-31">
            <pin digest="SHA-256">7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y=</pin>
            <!-- Backup pin: provisioned but not yet rotated to. -->
            <pin digest="SHA-256">fwza0LRMXouZHRC8Ei+4PyuldPDcf3UKgO/04cDM1oE=</pin>
        </pin-set>
    </domain-config>

    <!-- Debug-only: allow user-installed certs (for Charles/Proxyman) -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
            <certificates src="system" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

```xml
<!-- AndroidManifest.xml -->
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="false"
    ...>
```

### What Network Security Config gets you

- Enforced at the platform `URLConnection`/`HttpsURLConnection` layer — works for OkHttp, Ktor, Retrofit, WebView, native code using the OS networking stack.
- `cleartextTrafficPermitted="false"` hard-fails any `http://` request anywhere in the app — including third-party SDKs you didn't write.
- `debug-overrides` only applies in `debuggable` builds, so Charles/Proxyman work in dev but never in production.
- `expiration` causes the platform to log a warning when expiry approaches; on Android 12+ the OS surfaces a developer-visible warning.

### What it does NOT do

- No runtime rotation. Pins are baked into the APK; changing them requires an app release.
- No conditional pinning by host header or path — only by domain.
- WebView `loadUrl` is not pinned for content loaded inside the WebView itself; you need WebView client overrides for that.

---

## 4. Programmatic Pinning with OkHttp (For Custom Stacks)

When you need runtime control (different pins per build flavor, kill switch, custom error handling), use OkHttp's `CertificatePinner`:

```kotlin
class PinnedOkHttpClientFactory @Inject constructor(
    private val pinConfig: PinConfig,    // injected; could come from remote config
    private val analytics: AnalyticsClient,
) {
    fun build(): OkHttpClient {
        val pinner = CertificatePinner.Builder().apply {
            for ((host, pins) in pinConfig.pins) {
                for (pin in pins) {
                    add(host, "sha256/$pin")
                }
            }
        }.build()

        return OkHttpClient.Builder()
            .certificatePinner(pinner)
            .addInterceptor(PinFailureInterceptor(analytics))
            .connectionSpecs(modernTlsOnly())
            .build()
    }

    private fun modernTlsOnly() = listOf(
        ConnectionSpec.Builder(ConnectionSpec.MODERN_TLS)
            .tlsVersions(TlsVersion.TLS_1_3, TlsVersion.TLS_1_2)
            .build()
    )
}

class PinFailureInterceptor(private val analytics: AnalyticsClient) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        return try {
            chain.proceed(chain.request())
        } catch (e: SSLPeerUnverifiedException) {
            // Pin failure! Telemetry MUST capture before re-throw.
            analytics.log("tls_pin_failure", mapOf(
                "host" to chain.request().url.host,
                "exception" to e.message.orEmpty().take(200),
            ))
            throw e
        }
    }
}
```

`CertificatePinner` augments — does not replace — the OS trust check. The cert must be valid AND match one of the pinned hashes.

---

## 5. Pin Rotation: The Two-Pin Rule

```mermaid
flowchart LR
    V1["Release N<br/>old pin + backup new pin"] --> Rotate["Server certificate rotates"] --> Overlap["Both installed cohorts connect"] --> V2["Later release<br/>new pin + next backup"]
    Failure["No overlapping backup"] --> Outage["Installed clients cannot recover remotely"]
```

Pin rotation must overlap across installed app cohorts; a missing backup pin can turn routine certificate rotation into a persistent outage.

Certs expire. If your only pin is today's cert and ops rotates tomorrow, every install in the field breaks instantly — and they can't even download an update because the update-check endpoint also fails.

**Always pin at least two:**
- **Active pin** — what the server actually serves today.
- **Backup pin** — the *next* key pair, generated and kept offline by ops. When ops rotates, the app already trusts it.

```
Day -90:   Generate next year's key pair offline. Compute SPKI hash. Add as a *backup* pin in next release.
Day 0:     Release ships with [activePin, backupPin].
Day 365:   Ops rotates server to backupPin. Old activePin retires. Apps in the field accept seamlessly.
Day 366:   New release ships with [newActive=backupPin, newBackup=offlinePin].
```

If you ship only one pin, you've built a bricking mechanism. Treat the second pin as table stakes.

---

## 6. The Kill Switch (Pragmatic, Controversial)

Some teams maintain a server-side flag that disables pinning if an incident makes recovery impossible. Pattern:

```kotlin
val client = OkHttpClient.Builder().apply {
    if (flags.tlsPinningEnabled()) {
        certificatePinner(pinner)
    }
    // ... rest of config
}.build()
```

The flag itself must be fetched **without** going through the pinned stack — typically from a separate domain with OS-default trust. This trades a small attack surface (compromise the flag service to disable pinning everywhere) for incident-response capability.

The defensible middle ground:
- Flag exists but defaults to **enabled**.
- Flipping it requires multi-sig approval.
- Disabled state is time-bounded (auto-re-enable after 24h).
- Telemetry alerts when disabled.

If your security team forbids any kill switch, the rotation discipline becomes mandatory.

---

## 7. Pinning Other HTTP Stacks

### Ktor

```kotlin
val ktorClient = HttpClient(OkHttp) {
    engine {
        config {
            certificatePinner(pinner)        // same OkHttp pinner
        }
    }
}
```

### Cronet (Chromium net stack)

```kotlin
val builder = CronetEngine.Builder(context)
builder.addPublicKeyPins(
    "api.example.com",
    setOf("7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y="),
    /* includeSubdomains = */ true,
    Date(/* expiration */ 2026, 11, 31)
)
val engine = builder.build()
```

### WebView

WebView doesn't honor Network Security Config for its internal HTTPS traffic. Override `shouldInterceptRequest` or `onReceivedSslError`, but the better answer is: don't load sensitive content in WebView. If you must, pre-validate the URL is yours, and trust the OS root store only for `https://` content rendered inside.

---

## 8. Pinning the Leaf vs Intermediate vs Root

| Pin target | Survives cert reissue? | Survives CA change? | Risk if compromised |
|---|---|---|---|
| **Leaf SPKI** | Only with re-key (same key pair on new cert) | No | Need rotation discipline |
| **Intermediate CA SPKI** | Yes, any new leaf signed by same intermediate | No (rare in practice) | An attacker with that intermediate's key can impersonate you |
| **Root CA SPKI** | Yes | Only if you change CAs | An attacker with root key can impersonate anyone using that root |

**Most pragmatic for mobile**: pin the leaf SPKI **and** the intermediate as a backup. If ops re-keys without warning, the intermediate pin saves you; if ops changes CAs entirely, you have to ship a release anyway.

```xml
<pin-set expiration="2026-12-31">
    <!-- Leaf SPKI (today's server cert) -->
    <pin digest="SHA-256">7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y=</pin>
    <!-- Next leaf SPKI (offline-held, will rotate to) -->
    <pin digest="SHA-256">fwza0LRMXouZHRC8Ei+4PyuldPDcf3UKgO/04cDM1oE=</pin>
    <!-- Intermediate SPKI (last-resort survival) -->
    <pin digest="SHA-256">JbQbUG5JMJUoI6brnx0x3vZF6jilxsapbXGVfjhN8Fg=</pin>
</pin-set>
```

---

## 9. Local Development & Proxying

Pinning breaks Charles, Proxyman, and `mitmproxy` because they present their own CA's cert.

```xml
<!-- Allow user-installed certs ONLY in debuggable builds -->
<debug-overrides>
    <trust-anchors>
        <certificates src="user" />
        <certificates src="system" />
    </trust-anchors>
</debug-overrides>
```

Verify the release build still pins:

```bash
# Build release APK
./gradlew assembleRelease

# Decode network security config to confirm debug-overrides removed
aapt2 dump xmltree app/build/outputs/apk/release/app-release.apk \
    --file res/xml/network_security_config.xml
```

The release-build dump should NOT contain `<debug-overrides>`.

---

## 10. Telemetry & Observability

Pin failures are silent killers — the user just sees "no internet." Instrument:

```kotlin
class PinFailureInterceptor(...) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response = try {
        chain.proceed(chain.request())
    } catch (e: SSLPeerUnverifiedException) {
        // Capture host, observed SPKI hash, time, app version
        val sanInfo = extractObservedHash(e)
        analytics.log("tls_pin_failure", mapOf(
            "host" to chain.request().url.host,
            "observed_spki" to sanInfo,
            "app_version" to BuildConfig.VERSION_NAME,
            "android_api" to Build.VERSION.SDK_INT,
        ))
        throw e
    }
}
```

Dashboards to maintain:
- Pin failure rate per host per app version. Spike = ops rotated without your knowing OR an active MITM in some user's environment.
- Days until pin expiry per release. Alert at 90, 60, 30 days.
- TLS handshake error breakdown (`SSLPeerUnverifiedException` vs `SSLHandshakeException` vs `CertificateException`).

---

## 11. Common Pitfalls

- **Only one pin.** A single misstep (cert rotation, lost key) bricks the entire fleet permanently. Always at least two pins.
- **Pinning the cert hash instead of SPKI.** Cert hash changes on every reissue, even with the same key. SPKI survives re-keys.
- **Forgetting `expiration`.** Network Security Config ignores expired pin sets, falling back to OS trust — silent loss of pinning. Pick a date and rotate before.
- **Pinning third-party domains.** You don't control their cert rotation; they will break you.
- **Not testing release builds against pinning.** Debug builds bypass via `debug-overrides`; bugs slip into release. Run a release-mode smoke test in CI.
- **Failing to handle `SSLPeerUnverifiedException` in the UI.** Show a meaningful "couldn't verify server — possibly a network issue" message, not just a generic network error.
- **Pin Network Security Config in shared library.** If your app and a library both ship a config, the manifest merge picks one — be explicit about which.
- **Cleartext exemptions for "debug" still in the release manifest.** `usesCleartextTraffic="true"` for `app-staging.example.com` accidentally shipped to prod.
- **Trusting `Build.VERSION.SDK_INT < 24` to skip pinning.** API 23 still in the wild on some emerging-markets devices; OkHttp's `CertificatePinner` works on all API levels.

---

## 12. Testing

```kotlin
@Test
fun release_certificatePinnerRejectsUnknownCert() {
    // Use MockWebServer with a self-signed cert
    val server = MockWebServer()
    val cert = HeldCertificate.Builder().build()
    val handshake = HandshakeCertificates.Builder()
        .heldCertificate(cert)
        .build()
    server.useHttps(handshake.sslSocketFactory(), false)
    server.start()

    val client = OkHttpClient.Builder()
        .certificatePinner(
            CertificatePinner.Builder()
                .add(server.hostName, "sha256/INTENTIONALLY_WRONG_PIN_XXXXXXXXXXXX=")
                .build()
        )
        .sslSocketFactory(handshake.sslSocketFactory(), handshake.trustManager)
        .build()

    val request = Request.Builder().url(server.url("/")).build()
    assertFailsWith<SSLPeerUnverifiedException> {
        client.newCall(request).execute()
    }
}
```

Integration test on a real device against staging with intentionally wrong pin — confirms `SSLPeerUnverifiedException` and confirms the interceptor logs.

---

## 13. Further Reading

- [Android Developers — Network Security Configuration](https://developer.android.com/training/articles/security-config) — official guide.
- [OkHttp CertificatePinner API](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/CertificatePinner.kt) — programmatic API.
- [OWASP — Certificate and Public Key Pinning](https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning) — threat model and tradeoffs.
- [HPKP retrospective (Mozilla)](https://blog.mozilla.org/security/2018/10/09/) — why HTTP Public Key Pinning failed on the web (relevant context for mobile pinning).
- [Cronet PublicKeyPins API](https://developer.android.com/develop/connectivity/cronet) — for Cronet-based stacks.

---

> **In short:** pin SPKI hashes via Network Security Config (and OkHttp `CertificatePinner` if you need runtime control). Always ship a backup pin. Rotate yearly with overlap. Telemetry pin failures. Make sure debug-only overrides never reach production.

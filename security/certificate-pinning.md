# Security: Certificate Pinning (Preventing MITM)

## The Theory
When an Android app connects to `https://api.company.com`, it uses TLS (Transport Layer Security) to encrypt the traffic. To prove it is talking to the real server, the app checks the server's SSL certificate against the list of Trusted Root Certificate Authorities (CAs) installed on the Android OS.
-   **The Threat (Man-in-the-Middle / MITM):** A user connects to a malicious public Wi-Fi hotspot. The hotspot intercepts the traffic and presents its own fake SSL certificate. Normally, Android rejects this. However, if the user was tricked into installing a malicious Root CA on their device (or if a rogue government forces a CA to issue a fake certificate), the OS will trust the fake certificate. The attacker can now decrypt and read all passwords, API keys, and PII in plaintext.

## Staff-Level Application in Mobile

### 1. Certificate Pinning (The Defense)
Certificate Pinning is the practice of hardcoding the hash (Public Key Pin) of the server's SSL certificate directly into the mobile app's binary.
When the app connects to the server, it ignores the Android OS's list of Trusted CAs. Instead, it computes the hash of the certificate presented by the server. If the hash does not match the hardcoded Pin in the app, the connection is instantly aborted.

### 2. Implementation via Network Security Configuration
Android provides a declarative XML way to implement pinning without writing custom OkHttp interceptors.
```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <domain-config>
        <domain includeSubdomains="true">api.company.com</domain>
        <pin-set expiration="2027-01-01">
            <pin digest="SHA-256">7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y=</pin>
            <!-- Backup Pin! -->
            <pin digest="SHA-256">fwza0LRMXouZHRC8Ei+4PyuldPDcf3UKgO/04cDM1oE=</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```

### 3. The Backup Pin Rule (Catastrophic Failure Prevention)
Certificates expire (usually every 12 months). If the backend team rotates the server certificate, the hash changes. If the mobile app only has the old hash pinned, **every single instance of the app worldwide will instantly lose network connectivity.** They cannot even download an update via an API call.
-   **The Rule of Two:** You must *always* pin a Backup Certificate. The backend team generates the next year's certificate today, keeps it offline, and gives you the hash. You pin both the active hash and the backup hash. When the backend rotates to the backup cert next year, the app continues to function seamlessly.

## Common Pitfalls
-   **Pinning the Leaf vs Root:**
    -   **Pinning the Leaf (End-Entity):** Highly secure, but requires app updates every year when the certificate expires. Very dangerous if coordination between backend and mobile fails.
    -   **Pinning the Intermediate/Root CA:** More flexible. The app trusts any certificate issued by a specific provider (e.g., Let's Encrypt or DigiCert). It survives annual certificate rotations automatically, but if the Root CA itself is compromised, the app is vulnerable. Staff engineers often pin the Intermediate CA as a pragmatic middle ground.
-   **Staging Environments:** Pinning breaks debugging proxies like Charles or Proxyman. You must configure your Network Security Config to trust user-installed CAs *only* in `debug` builds, ensuring the `release` build remains strictly pinned.

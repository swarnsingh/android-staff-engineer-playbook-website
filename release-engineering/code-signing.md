# Release Engineering: Code Signing & Play App Signing

## The Prompt

*"A Junior developer accidentally commits the `release.keystore` and its password to a public GitHub repository. A hacker downloads it, creates a fake version of your Bank app containing malware, signs it with your keystore, and emails it to your customers. Their phones accept the update. Design the cryptographic defense against this, and explain how Google Play App Signing changes the architecture."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Cryptographically prove that an APK/AAB was built by the authentic developer.
- Ensure the Android OS rejects any update that wasn't signed by the original key.
- Provide a recovery mechanism if the signing key is compromised.

### Non-Functional Requirements (NFRs)
- **Security (Priority 0):** The Private Key must never be exposed. If a hacker possesses the Private Key, they effectively own the application's identity.
- **Integrity:** Modifying a single byte of the APK must break the signature.

## 2. High-Level Architecture (Asymmetric Cryptography)

Android security relies entirely on **Asymmetric Cryptography (RSA or Elliptic Curve)** and SHA-256 hashing.

```mermaid
graph TD
    subgraph The Keystore (The Vault)
        PrivateKey[Private Key]
        PublicKey[Public Key / Certificate]
    end
    
    subgraph The Signing Process (CI/CD)
        RawAPK[Unsigned APK] -->|SHA-256 Hash| Hash[Hash String]
        Hash -->|Encrypted with Private Key| Signature[Digital Signature]
        RawAPK --> FinalAPK[Signed APK + Signature + Public Key]
        Signature --> FinalAPK
    end
    
    subgraph The Device (Android OS)
        FinalAPK -->|User taps Install| OS[Package Manager]
        OS -->|Extracts| PublicKey2[Public Key]
        OS -->|Extracts| Signature2[Signature]
        OS -->|Decrypts Signature with Public Key| DecryptedHash[Decrypted Hash]
        OS -->|Hashes APK itself| LocalHash[Local Hash]
        DecryptedHash -->|Must Equal| LocalHash
    end
```

## 3. The Core Flows (Deep Dive)

### Flow 1: The App Update Verification
*Interviewer:* "A user has Bank App v1.0 installed. A hacker emails them Bank App v2.0 (containing malware). The user clicks install. Why does the Android OS block it?"

**Staff Answer:**
"The Android OS enforces the **Application Sandbox**.
1. When v1.0 was installed, the OS stored the Public Key Certificate used to sign it.
2. The user attempts to install v2.0.
3. The OS checks the package name (`com.bank.app`). It sees the app is already installed.
4. The OS extracts the Public Key Certificate from the new v2.0 APK.
5. It compares the v2.0 Public Key to the saved v1.0 Public Key.
6. The hacker does not have the authentic Private Key, so they had to sign v2.0 with a fake key.
7. The Public Keys do not match. The OS violently rejects the installation, displaying an `INSTALL_FAILED_UPDATE_INCOMPATIBLE` error. The malware cannot overwrite the authentic app."

### Flow 2: The Compromised Keystore (The Nightmare Scenario)
*Interviewer:* "The Junior developer leaked the Keystore. The hacker *does* have your Private Key. They sign the malware. The Android OS verifies it perfectly. The users are hacked. How do you recover?"

**Staff Answer:**
"Historically, if you lost your Keystore, the app was dead forever. You had to create a new package name (`com.bank.app2`) and lose all 10 million users.
Today, we use **Play App Signing**.
1. We opt into Google Play App Signing.
2. We generate an **Upload Key** and an **App Signing Key**.
3. We send the *App Signing Key* to Google's highly secure vault.
4. We keep the *Upload Key* locally. We use the Upload Key to sign the App Bundle we upload to the Play Console.
5. Google verifies the Upload Key, strips it off, and re-signs the APKs with the actual App Signing Key before sending them to users.
**The Recovery:** If the Junior developer leaks the Upload Key, the hacker cannot harm users (the hacker cannot upload to our Play Console account). We simply contact Google Support, revoke the compromised Upload Key, and generate a new one. The users are completely unaffected because the actual App Signing Key remains safe inside Google's vault."

### Flow 3: V1 vs V2 vs V3 Signatures (APK Signature Scheme)
*Interviewer:* "Why did Google introduce APK Signature Scheme V2 and V3? What was wrong with V1?"

**Staff Answer:**
"V1 (JAR signing) was flawed. It only signed the *contents* of the ZIP file, not the ZIP archive itself. A hacker could theoretically append metadata to the APK without breaking the signature, causing the 'Janus Vulnerability'.
- **V2 Scheme:** Signs the *entire* APK file as a single binary blob. If a hacker changes a single byte anywhere in the file, the signature is invalid. It is also massively faster for the OS to verify during installation.
- **V3 Scheme:** Introduced **Key Rotation**. If your actual App Signing Key is compromised (or migrating ownership), V3 allows you to cryptographically link the old key to a new key (Lineage). The Android OS will recognize the new key as a valid successor to the old key, allowing users to update successfully without losing their data."

## 4. Failure Modes & Bottlenecks

### Bottleneck: Keystore Passwords in CI/CD
*Interviewer:* "How does your CI pipeline sign the app if the Keystore file and its two passwords (Keystore Password & Key Alias Password) cannot be checked into Git?"

**Staff Answer:**
"We must use a **Secret Injection Pipeline**.
1. The `.keystore` file is encoded in Base64 and stored as a secure environment variable in GitHub Secrets (or HashiCorp Vault).
2. The two passwords are also stored as separate encrypted secrets.
3. When the CI job runs on the ephemeral runner, a script decodes the Base64 string back into a binary `.keystore` file.
4. The Gradle build consumes the passwords from the environment variables:
```groovy
signingConfigs {
    release {
        storeFile file(System.getenv("KEYSTORE_FILE_PATH"))
        storePassword System.getenv("KEYSTORE_PASSWORD")
        keyAlias System.getenv("KEY_ALIAS")
        keyPassword System.getenv("KEY_PASSWORD")
    }
}
```
5. After the build, the runner is destroyed, and the secrets vanish from memory. They never exist on disk permanently."

### Bottleneck: The SHA-1 API Key Failure
*Interviewer:* "You migrate to Google Play App Signing. Your Google Maps SDK and Facebook Login instantly break in production. Why?"

**Staff Answer:**
"Third-party APIs (Maps, Firebase, Facebook) authenticate your Android app by checking its SHA-1 Certificate Fingerprint.
When we migrated, we were using the local Upload Key's SHA-1 in the Google Cloud Console.
However, Google Play stripped the Upload Key and re-signed the app with the *App Signing Key*.
The OS reports the App Signing Key's SHA-1 to Google Maps. Google Maps rejects it because it doesn't match the Upload Key's SHA-1 on file.
**The Fix:** We must go into the Google Play Console, copy the SHA-1 of the *App Signing Key*, and add it to the API provider's whitelist alongside the Upload/Debug keys."

## 5. Staff Engineer Thinking: Digital Asset Links

A Staff Engineer knows that Code Signing is not just about the APK on the phone; it is the cryptographic foundation for the entire ecosystem.

When we configure **Android App Links** (to prevent malicious apps from intercepting `https://bank.com`), the `assetlinks.json` file hosted on `bank.com` must contain the SHA-256 fingerprint of the App Signing Key.
If you do not strictly control your Code Signing infrastructure, your deep links will break, your APIs will reject you, and your app updates will fail. Code Signing is the ultimate anchor of trust in the Android ecosystem.

## 6. Probing Questions (For Practice)

1.  Explain how Asymmetric Cryptography (Public/Private Keys) ensures that the Android OS can verify an APK was created by the authentic developer.
2.  Describe the mechanism the Android Package Manager uses to block an app update that was signed by a different developer.
3.  Walk through the difference between an Upload Key and an App Signing Key in the Google Play App Signing architecture.
4.  If a Junior Developer leaks the Upload Key to a public GitHub repo, explain the exact steps required to recover without losing any users.
5.  Why is the V1 (JAR) signature scheme considered insecure, and how does the V2 scheme mathematically protect the entire APK binary blob?
6.  Explain the concept of "Key Rotation" introduced in the V3 Signature Scheme.
7.  Describe the secure pipeline required to provide the CI/CD runner with the Keystore file and its passwords without committing them to version control.
8.  Why do Google Maps, Firebase Auth, and Facebook Login break immediately after a team migrates to Google Play App Signing, and how is it fixed?
9.  Explain the role of the SHA-256 fingerprint in the `assetlinks.json` file. How does this cryptographically link a website to a specific Android application?
10. If an app was released 5 years ago without Google Play App Signing, and the developer loses the physical `.keystore` hard drive, what happens to the application and its users?

## Further Reading

- [`ci-cd-for-mobile.md`](ci-cd-for-mobile.md) — How the CI runner pulls secrets to execute the signing.
- [`deep-links-and-universal-links.md`](../mobile-system-design/deep-links-and-universal-links.md) — How the `assetlinks.json` uses the SHA-256 signature for verification.
- [`security-and-privacy.md`](../mobile-system-design/security-and-privacy.md) — The concepts of Asymmetric Cryptography.

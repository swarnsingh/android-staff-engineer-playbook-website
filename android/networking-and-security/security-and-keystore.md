# Android Keystore — Platform Application

> **Canonical owners:** [Secure Storage on Android](../../security/secure-storage-on-android.md) and [Key Management](../../security/key-management.md).
>
> This application page explains where Android platform mechanics affect those decisions. It does not redefine the storage policy.

## Platform Boundary

Android Keystore is a system provider for generating or importing cryptographic keys and performing operations without returning raw key material to the app. A key can additionally be bound to a Trusted Execution Environment or StrongBox when the device and requested algorithm support it.

Three guarantees must not be conflated:

1. **App sandbox:** another ordinary UID cannot open the app's files.
2. **Non-exportable key:** application code receives a key handle rather than raw key bytes.
3. **Secure-hardware backing:** key material and some authorizations are enforced by TEE or StrongBox.

The first two can exist without the third. “Android 6 made all Keystore keys hardware-backed” is false; inspect `KeyInfo.securityLevel` when hardware assurance is a requirement.

## Application Decisions

- Generate device keys in the `AndroidKeyStore` provider; never hardcode a symmetric key in source or resources.
- Persist ciphertext and its IV in an app-private store; persist no raw key bytes.
- Request StrongBox only when the risk justifies availability and performance costs, and handle `StrongBoxUnavailableException` explicitly.
- Bind keys to biometrics only when the feature can recover from enrollment changes, lock-screen removal, and device restore.
- Keep authorization on the server. A Keystore key can establish device possession; it cannot prove that every request is legitimate.

## Failure Modes

| Failure | Platform cause | Application response |
|---|---|---|
| `KeyPermanentlyInvalidatedException` | Authentication enrollment or lock-screen state changed | Delete dependent ciphertext and re-authenticate |
| `UserNotAuthenticatedException` | Authentication-bound key is locked | Prompt within a user-initiated flow; do not loop |
| `StrongBoxUnavailableException` | Requested secure element unavailable | Follow written fallback/block policy |
| AEAD tag failure | Wrong key, corrupt data, or tampering | Reject the record; never return partial plaintext |
| Restore-time decryption failure | Ciphertext restored without device-bound key | Clear the vault and establish a new session |

## Review Checklist

- Is the secret necessary on-device, or can the backend retain custody?
- Is encryption addressing a real threat beyond the UID sandbox?
- Are backup and device-transfer exclusions tested?
- Is actual key backing measured without exposing identifiers or secrets?
- Can key invalidation recover without data loss beyond the intended secret?
- Are tokens redacted from logs, crash reports, traces, and network inspectors?
- Does the server rotate, scope, revoke, and rate-limit the credential?

## Probing Questions

1. What is the difference between a non-exportable key and a hardware-backed key?
2. Why is root detection not a substitute for Keystore-backed design?
3. What happens when encrypted app data is restored to a new device?
4. When should StrongBox unavailability block enrollment rather than fall back to TEE?
5. How would you instrument key invalidation without logging sensitive material?

## Answer Key

1. Non-exportability keeps bytes out of the app; hardware backing additionally confines key material and supported authorizations to TEE or StrongBox.
2. Root detection is bypassable and does not prevent a compromised process from accessing plaintext; Keystore changes key custody but still needs server controls.
3. The old device-bound key is absent, so the app must discard unrecoverable ciphertext and re-authenticate unless it designed another recovery mechanism.
4. Block only when policy or regulation requires a StrongBox assurance level; otherwise document and observe the TEE/software fallback.
5. Record outcome, API level, requested/actual security class, and exception category—never aliases, ciphertext, or token material.

## Further Reading

- [Android Keystore system](https://developer.android.com/privacy-and-security/keystore)
- [Verify hardware-backed key pairs](https://developer.android.com/privacy-and-security/security-key-attestation)
- [Secure Storage on Android](../../security/secure-storage-on-android.md)
- [Certificate Pinning](../../security/certificate-pinning.md)
- [Authentication on Mobile](../../security/auth-on-mobile.md)

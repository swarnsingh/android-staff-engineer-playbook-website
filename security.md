# Security

## Purpose

Threats, attack vectors, and mitigations for mobile systems. The cross-cutting topic from the v2 spec — privacy, GDPR, data residency — lives here.

## Why It Matters

Mobile is the attack surface for financial, identity, and personal-data systems. Privacy regulation (GDPR and equivalents) shapes architecture as much as performance does.

## What This Folder Helps You Do

- Think from threat models instead of checklists: compromised devices, token theft, MITM, replay, data leakage, rooted phones, and malicious deep links.
- Design mobile authentication, secure storage, key management, certificate pinning, attestation, privacy, GDPR, and data residency controls.
- Know where mobile security ends: the client can raise confidence and reduce exposure, but the server must enforce authorization, risk scoring, revocation, and auditability.
- Review product features for minimization, consent, retention, observability redaction, and failure behavior before sensitive data ships.

## Guided Reading Sequence

Prerequisites: Android storage/networking fundamentals and basic backend authentication. Begin with minimization—data that does not exist cannot leak—then move from identity and local custody to transport and device trust.

1. [Privacy, GDPR & Data Residency](security/privacy-gdpr-data-residency.md)
2. [Privacy Sandbox: Rise, Retirement & What Replaces It](security/privacy-sandbox.md) — policy-history application.
3. [Authentication on Mobile](security/auth-on-mobile.md)
4. [Secure Storage](security/secure-storage-on-android.md)
5. [Key Management](security/key-management.md)
6. [Certificate Pinning](security/certificate-pinning.md)
7. [App & Device Attestation](security/attestation.md)

**Next:** revisit a [Reference Architecture](reference-architectures.md) and threat-model it end to end.

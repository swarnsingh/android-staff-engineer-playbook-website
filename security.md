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

## Learning Order

Start with privacy and data residency because they shape what data should exist at all. Then move through authentication, secure storage, and key management. Finish with certificate pinning and attestation, where threat models meet mobile device reality.

## Topics

- [Privacy, GDPR & Data Residency](security/privacy-gdpr-data-residency.md)
- [Authentication on Mobile](security/auth-on-mobile.md)
- [Secure Storage](security/secure-storage-on-android.md)
- [Key Management](security/key-management.md)
- [Certificate Pinning](security/certificate-pinning.md)
- [App & Device Attestation](security/attestation.md)

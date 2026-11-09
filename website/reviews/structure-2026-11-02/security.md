# Security: structure plan

Planning baseline: approved source `fb8354edb079e901edf18710ca9388a124712a5b` (source PRs #76–#80). Order below is the exact guided tree-index order, not filename order. This plan precedes teaching-layer drafting. Only Delivery Semantics is implemented in this milestone; all other entries are conversion plans awaiting later topic ownership and approval.

Each chapter retains its complete original text, code, tables, diagrams, operational sections and existing questions/answers in order. The coverage field names the chapter-specific mechanisms that must remain understandable; it is not permission to drop other original sections. Original Mermaid sources get designed FigureMaps when converted. New figures use shared role tokens, labelled relationships, explicit boundaries and captions stating the point. Motion is optional; listed traces are manual candidates, not promised animations. No new prediction questions, decision-card interactions or answer hiding are approved. Source links below are the primary authorities to consult at conversion, not a claim that every linked page or integration has been tested.

The content layer supplies content and component selection only. Layout and behaviour remain in the shared design system. Official requirements and product status must be rechecked at conversion, especially Security and Release policy chapters. The accompanying inventory records exact Git-object hashes and section/diagram counts; planning reads do not synchronize whole trees.

## 1. Security and Privacy: GDPR, CCPA and Data Residency

- **Opening problem:** A deletion request reaches the server while an offline device retains the data.
- **Narrative route:** Inventory/minimize data; follow collection, region routing, retention and deletion through offline custody.
- **Preserved coverage / internals:** Requirements, consent pipeline, residency beyond edges, telemetry/SDK review, minimization register and enforcement points.
- **Figures / step-throughs:** Data custody/region map; deletion acknowledgement lifecycle.
- **Production / staff decisions:** Name data/controller ownership and verify jurisdictional obligations before conversion.
- **Prerequisites:** Android storage/networking; backend auth.
- **Official sources:** [EU Regulation 2016/679: General Data Protection Regulation](https://eur-lex.europa.eu/eli/reg/2016/679/oj).

## 2. Privacy Sandbox on Android: Architecture, Phaseout and Migration

- **Opening problem:** A platform privacy bet changes status before the product ships.
- **Narrative route:** Present dated policy history, current official status and architecture exit decisions.
- **Preserved coverage / internals:** Rise/retirement history, current Android privacy controls and platform-bet review.
- **Figures / step-throughs:** Dated static timeline; no simulated policy animation.
- **Production / staff decisions:** Reverify announcements at conversion; separate historical availability from current planning.
- **Prerequisites:** Privacy and data minimization.
- **Official sources:** [Privacy Sandbox: Official announcements](https://privacysandbox.google.com/blog).

## 3. Security: Authentication on Mobile (OAuth, PKCE, Tokens, Biometric Step-Up)

- **Opening problem:** A login callback or refresh response arrives after the user changed session.
- **Narrative route:** Follow browser authorization and PKCE; bind redirect/state/issuer; trace refresh and logout ownership.
- **Preserved coverage / internals:** Threat model, OAuth/PKCE, token custody, Authenticator coordination, logout races, biometric step-up and Google identity.
- **Figures / step-throughs:** Browser/app/IdP boundary map; manual refresh vs logout trace.
- **Production / staff decisions:** Server authorization and revocation remain explicit; scope old-response rejection and account binding.
- **Prerequisites:** Privacy; backend authentication and lifecycle.
- **Official sources:** [RFC 8252: OAuth 2.0 for Native Apps](https://www.rfc-editor.org/rfc/rfc8252); [RFC 9700: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700).

## 4. Secure Storage on Android

- **Opening problem:** A restored encrypted file arrives without the original key.
- **Narrative route:** Start from the attacker/custody model; choose storage; show encryption envelope and restore recovery.
- **Preserved coverage / internals:** Current platform position, direct Keystore envelope, hardware/StrongBox limits, auth-bound keys, backup/transfer and legacy migration.
- **Figures / step-throughs:** Key/file custody map; missing/invalidated-key recovery state trace.
- **Production / staff decisions:** Specify what remains exposed in process and how recovery avoids silent plaintext fallback.
- **Prerequisites:** Android storage; authentication.
- **Official sources:** [Android Keystore system](https://developer.android.com/privacy-and-security/keystore); [Android: Back up user data with Auto Backup](https://developer.android.com/identity/data/autobackup).

## 5. Security: Key Management & Secrets on Android

- **Opening problem:** An embedded third-party credential is extracted from the APK.
- **Narrative route:** Classify secrets; separate public configuration, device keys and server secrets; rotate by owner.
- **Preserved coverage / internals:** Build-time constants, Keystore, asymmetric/auth-bound keys, backend proxy, rotation and signing-key custody.
- **Figures / step-throughs:** Secret owner/lifetime map; static rotation overlap.
- **Production / staff decisions:** Make extraction assumptions explicit and define recovery for each key class.
- **Prerequisites:** Secure storage; authentication.
- **Official sources:** [Android Keystore system](https://developer.android.com/privacy-and-security/keystore); [Google Cloud: Cloud KMS overview](https://cloud.google.com/kms/docs/key-management-service).

## 6. Security: Certificate Pinning (Defeating Active MITM)

- **Opening problem:** Certificate rotation strands installed clients behind an obsolete pin.
- **Narrative route:** Threat model first; compare trust validation and pins; exercise rotation and recovery per network stack.
- **Preserved coverage / internals:** NSC, OkHttp/Cronet/WebView/Ktor boundaries, pin scope, backup pins, kill-switch risks, debug overrides and telemetry.
- **Figures / step-throughs:** Trust-chain and stack enforcement maps; manual pin-overlap trace.
- **Production / staff decisions:** Balance added trust restrictions against outage/recovery risk and installed-client lifetime.
- **Prerequisites:** TLS; key management.
- **Official sources:** [Android: Network Security Configuration](https://developer.android.com/privacy-and-security/security-config); [OkHttp: HTTPS](https://lysine.dev/okhttp/features/https/).

## 7. Security: App and Device Attestation

- **Opening problem:** A genuine-device verdict is replayed for a different high-risk action.
- **Narrative route:** Bind request evidence to action/session; separate Standard, Classic and key enrollment; verify on server.
- **Preserved coverage / internals:** Threat model, Integrity paths, nonce/request binding, verdict labels, server policy, Keystore enrollment and tests.
- **Figures / step-throughs:** App/Google/backend trust map; challenge-verification trace.
- **Production / staff decisions:** Treat evidence as one risk signal; define freshness, failure policy and revocation owner.
- **Prerequisites:** Auth, key management and replay protection.
- **Official sources:** [Play Integrity: Standard API requests](https://developer.android.com/google/play/integrity/standard); [Play Integrity: Classic API requests](https://developer.android.com/google/play/integrity/classic); [Android: Verify hardware-backed key pairs with key attestation](https://developer.android.com/privacy-and-security/security-key-attestation).

## Separate prerequisite follow-up

The published Mobile System Design Authentication lesson still requires a separate synchronization to source #80 after the prerequisite canonical Security #78 snapshot and dependency review. This milestone does not synchronize, alter or publish those chapters. Their source merges do not imply website publication.

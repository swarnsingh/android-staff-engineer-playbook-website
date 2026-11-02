# Release Engineering: structure plan

Planning baseline: approved source `fb8354edb079e901edf18710ca9388a124712a5b` (source PRs #76–#80). Order below is the exact guided tree-index order, not filename order. This plan precedes teaching-layer drafting. Only Delivery Semantics is implemented in this milestone; all other entries are conversion plans awaiting later topic ownership and approval.

Each chapter retains its complete original text, code, tables, diagrams, operational sections and existing questions/answers in order. The coverage field names the chapter-specific mechanisms that must remain understandable; it is not permission to drop other original sections. Original Mermaid sources get designed FigureMaps when converted. New figures use shared role tokens, labelled relationships, explicit boundaries and captions stating the point. Motion is optional; listed traces are manual candidates, not promised animations. No new prediction questions, decision-card interactions or answer hiding are approved. Source links below are the primary authorities to consult at conversion, not a claim that every linked page or integration has been tested.

The content layer supplies content and component selection only. Layout and behaviour remain in the shared design system. Official requirements and product status must be rechecked at conversion, especially Security and Release policy chapters. The accompanying inventory records exact Git-object hashes and section/diagram counts; planning reads do not synchronize whole trees.

## 1. Release Engineering: Code Signing & Play App Signing

- **Opening problem:** The release artifact is valid but its signing identity differs from the installed app.
- **Narrative route:** Prove identity from upload to installed APK; separate upload and app-signing custody; rehearse compromise recovery.
- **Preserved coverage / internals:** Key generation, Play App Signing, Gradle/CI injection, verification, v3/v3.1 rotation, debug identity and compromise playbook.
- **Figures / step-throughs:** Signer/custodian boundary map; static rotation lineage.
- **Production / staff decisions:** Assign key custody and independent verification; avoid recovery promises unsupported by distribution path.
- **Prerequisites:** Android builds; security key management.
- **Official sources:** [Android: Sign your app](https://developer.android.com/studio/publish/app-signing); [AOSP: APK signature scheme v3.1](https://source.android.com/docs/security/features/apksigning/v3-2).

## 2. Release Engineering: CI/CD for Mobile

- **Opening problem:** A pipeline is green but the artifact promoted is not the one tested.
- **Narrative route:** Follow source, checks, signed artifact, evidence and promotion; distinguish test and cache trust.
- **Preserved coverage / internals:** PR/release workflows, Gradle configuration/cache, publisher, Test Lab, reproducibility, memory and benchmark gates.
- **Figures / step-throughs:** Artifact/evidence lineage map; promotion trace only for state changes.
- **Production / staff decisions:** Pin provenance and release identity; own secrets, flaky-test disposition and cache trust.
- **Prerequisites:** Code signing; observability SLIs/SLOs.
- **Official sources:** [GitHub Actions: Security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions); [Gradle: Build Cache](https://docs.gradle.org/current/userguide/build_cache.html).

## 3. Release Engineering: Android App Bundles (AAB)

- **Opening problem:** The universal APK passes but a device-specific delivered split does not.
- **Narrative route:** Follow AAB to device splits; inspect dynamic features/assets; verify size budgets per device configuration.
- **Preserved coverage / internals:** AAB/APK, dynamic/conditional/asset delivery, bundletool, size matrix, ABI/density and internal distribution.
- **Figures / step-throughs:** Bundle/Play/device ownership map; static split configuration matrix.
- **Production / staff decisions:** Test delivered configurations and define install/on-demand failure UX.
- **Prerequisites:** CI/CD and artifact signing.
- **Official sources:** [Android App Bundle overview](https://developer.android.com/guide/app-bundle); [Android: bundletool](https://developer.android.com/tools/bundletool).

## 4. Release Engineering: Play Store Internals

- **Opening problem:** Aggregate crash data hides a severe regression on one device cohort.
- **Narrative route:** Begin with a release question; choose the correct Console/API surface and aligned cohort evidence.
- **Preserved coverage / internals:** Console map, Vitals vs telemetry, cohort example, API boundaries, pre-launch reports, adoption, updates and incidents.
- **Figures / step-throughs:** Evidence-source map; cohort drill-down as static tables.
- **Production / staff decisions:** Separate rollout eligibility from adoption and telemetry coverage; assign incident evidence owner.
- **Prerequisites:** App bundles; metrics and SLIs.
- **Official sources:** [Android vitals](https://developer.android.com/google/play/vitals); [Google Play Developer Reporting API](https://developers.google.com/play/developer/reporting).

## 5. Android Developer Verification

- **Opening problem:** A distribution route needs a verified identity and package registration.
- **Narrative route:** Inventory channels; verify current official requirements; bind package/signing proof and operational ownership.
- **Preserved coverage / internals:** Distribution inventory, signing-key proof, operations, failures and original Q&A.
- **Figures / step-throughs:** Publisher/package/signing identity map; no invented enforcement timeline.
- **Production / staff decisions:** Track official policy dates and exemptions at conversion; define proof custody and escalation.
- **Prerequisites:** Code signing and Play distribution.
- **Official sources:** [Android developer verification](https://developer.android.com/developer-verification); [Android developer verification: FAQs](https://developer.android.com/developer-verification/guides/faq).

## 6. Android Platform Compatibility Program

- **Opening problem:** A platform deadline arrives while a transitive SDK blocks migration.
- **Narrative route:** Map each annual requirement to affected artifacts, owners, evidence and a release window.
- **Preserved coverage / internals:** Annual workflow, ownership, failure modes, target/behaviour/tooling separation and Q&A.
- **Figures / step-throughs:** Requirement-to-owner map; dated evidence table.
- **Production / staff decisions:** Verify current deadlines and supported toolchain; do not hard-code a permanent annual answer.
- **Prerequisites:** Developer verification; Android builds.
- **Official sources:** [Google Play: Target API level requirements](https://developer.android.com/google/play/requirements/target-sdk); [Android Gradle plugin release notes](https://developer.android.com/build/releases/gradle-plugin).

## 7. 16 KB Page Sizes: The Native-Code Compliance Gate

- **Opening problem:** An app containing native dependencies works on one page size and fails on another.
- **Narrative route:** Inventory native code; separate package and ELF alignment from runtime assumptions; test both configurations.
- **Preserved coverage / internals:** Two alignment requirements, hard-coded page assumptions, detection/CI, runtime tests, backcompat limits and rollout.
- **Figures / step-throughs:** APK/ELF/runtime boundary map; static compliance evidence matrix.
- **Production / staff decisions:** Own transitive native SDK readiness and real-device evidence; compatibility mode is not readiness proof.
- **Prerequisites:** Bundles and platform compatibility.
- **Official sources:** [Android: Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes).

## 8. Release Engineering: Staged Rollouts

- **Opening problem:** A release becomes eligible to more users before sufficient evidence is available.
- **Narrative route:** Follow draft/in-progress/halted/completed states; compare exposure, adoption and evidence windows.
- **Preserved coverage / internals:** Stage model, publisher/API transitions, halt runbook, gates, country/device limits, priority and audit trail.
- **Figures / step-throughs:** Rollout state FigureMap; manual halt/promotion trace.
- **Production / staff decisions:** Set promotion owner and halt criteria; distinguish halt from rollback of already installed apps.
- **Prerequisites:** Play internals; CI/CD and SLIs.
- **Official sources:** [Play Console: Release app updates with staged rollouts](https://support.google.com/googleplay/android-developer/answer/6346149); [Google Play Developer API: Tracks and staged rollouts](https://developers.google.com/android-publisher/tracks).

## 9. Release Engineering: Crash-Rate Gating (Automated Holds and Halts)

- **Opening problem:** A low crash rate comes from stale or insufficient observations.
- **Narrative route:** Define eligible outcomes/cohorts; query evidence; require freshness and sample sufficiency before promotion.
- **Preserved coverage / internals:** Vitals/Crashlytics denominator differences, auto-halt, multi-signal gates, cohorts, override, time windows and ANRs.
- **Figures / step-throughs:** Signal/decision ownership map; missing-data decision trace.
- **Production / staff decisions:** Treat unknown evidence explicitly; retain auditable override and cohort ownership.
- **Prerequisites:** Staged rollout; observability SLIs/SLOs.
- **Official sources:** [Play Developer Reporting API: vitals.crashrate](https://developers.google.com/play/developer/reporting/reference/rest/v1beta1/vitals.crashrate); [Firebase Crashlytics: Crash-free metrics](https://firebase.google.com/docs/crashlytics/crash-free-metrics).

## 10. Release Engineering: Kill Switches

- **Opening problem:** A broken installed feature must be disabled before an app update can reach users.
- **Narrative route:** Separate server and client controls; follow fetch, validation, activation, live apply and worker reconciliation.
- **Preserved coverage / internals:** Flag model, live policy, propagation limits, authorization, granular/server kill, compatibility, local overrides, telemetry and tests.
- **Figures / step-throughs:** Control-plane/app/worker map; manual pending-to-active trace.
- **Production / staff decisions:** Define safe defaults, stale/offline behaviour and cancellation/continuation semantics.
- **Prerequisites:** Crash gates; auth and background work.
- **Official sources:** [Firebase Remote Config: Loading strategies](https://firebase.google.com/docs/remote-config/loading); [WorkManager: Managing work](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work).

## 11. Release Engineering: Release Strategy (Trains, Branches, Cadence)

- **Opening problem:** An incident requires choosing halt, disable, hotfix or continue while versions remain installed.
- **Narrative route:** Synthesize the preceding controls around impact, reversibility and evidence; assign decision and communication owners.
- **Preserved coverage / internals:** Train, versioning, branches/cherry-picks/CODEOWNERS, hotfix, roles, stop-line, lever selection, severity and communication.
- **Figures / step-throughs:** Control/owner decision map; static incident decision table.
- **Production / staff decisions:** Tie each lever to its actual reach and revisit trigger; preserve old-client API compatibility.
- **Prerequisites:** All preceding release chapters; Security.
- **Official sources:** [Google SRE Book: Release Engineering](https://sre.google/sre-book/release-engineering/); [Android: Version your app](https://developer.android.com/studio/publish/versioning).

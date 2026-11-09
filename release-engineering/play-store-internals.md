# Release Engineering: Play Store Internals

## Console Map for Release Decisions

Console navigation can change; use these capability names rather than memorizing a menu path.

| Capability | Question it answers | Limit |
|---|---|---|
| Release tracks | Which candidate and exposure state are configured? | Eligibility differs from installed adoption |
| App integrity | Which signing certificates and integrity settings apply? | Upload and installed-app identities differ |
| Android vitals | Which eligible cohorts show stability/performance problems? | Population, freshness and coverage are constrained |
| Statistics | How does supported install/device activity vary? | Metric definitions and exports must match the question |
| Device catalog | Which devices are supported or excluded? | Exclusion affects app availability, not a binary canary percentage |
| Pre-launch report | What did automated tested paths reveal? | Unvisited flows and unavailable devices remain gaps |
| Policy status | Which requirements or enforcement actions need attention? | Review requirements for the actual app/account |
| Store listing and reviews | What do users see and report? | Qualitative reports do not replace cohort denominators |

## Vitals and Application Telemetry

Android vitals describes the eligible, opted-in population observed by Play, not every installed device. Crashlytics sees the population covered by its SDK/session instrumentation and collection policy. Fatal crashes, non-fatal errors, user-perceived outcomes and ANRs are different metrics; never count a non-fatal log as a fatal crash merely because both appear in a crash-reporting tool.

Compare definitions, eligibility, version/cohort, window, freshness and sample coverage before interpreting a difference. Some startup failures occur before SDK initialization, and Crashlytics also supports ANR reporting on supported Android versions. The claim that it cannot observe ANRs is wrong. Neither source is a complete census or an instant decision oracle.

Use [crash-rate gating](crash-rate-gating.md) for the canonical metric/converter contract. Play's quality signals affect discoverability, but that does not establish a documented automatic halt or deterministic rollout slowdown for every regression. Keep the release owner's explicit halt and mitigation automation.

## Fleet and Cohort Analysis

Use Play Console's supported install/device statistics and actual product telemetry to size the fleet. Label illustrative percentages as examples; they are not Android market share. The ANR metric set's `distinctUsers` is its rounded normalization population for a declared aggregation period, not an install count or a universal active-user metric.

The Reporting API supports resource-specific dimensions such as version code, API level, device model and country code. It can paginate results and suppress data when coverage is insufficient. A dictionary keyed only by country/model can overwrite multiple dates or cohorts; retain the complete row identity. Do not add distinct-user rows across overlapping periods as if they were a deduplicated population.

### Worked Cohort Investigation

Suppose the new version has a startup-crash signal concentrated on one device model and API level. This is a hypothetical investigation, not a measured market-share claim:

1. Pin the version code and compare the same eligible cohort and complete reporting windows with the previous release. Keep freshness, suppression and sample coverage visible.
2. Inspect the stack/cluster and startup initialization order. A crash before an SDK starts can explain missing SDK evidence, but does not prove that every discrepancy has that cause.
3. Halt further exposure under the incident policy. If the faulty initializer is remotely gateable, disable that path and retain a tested fallback for already-updated clients.
4. Reproduce on an available matching device or a justified substitute, including an upgrade with existing app data. Record the reproduction gap when the exact model is unavailable.
5. Ship a minimal fix with a greater version code, then watch the affected cohort and the broader guardrails during recovery. Halting does not downgrade installed users.

Do not add country, date or device rows together when their user populations overlap. A cohort label needs its version, time window, metric definition and population to support a release decision.

## API Boundaries

```http
# Publishing API: current track, inside an edit
GET https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/edits/{editId}/tracks/production

# Reporting API: metric queries use POST with a reviewed query body
POST https://playdeveloperreporting.googleapis.com/v1beta1/apps/{packageName}/crashRateMetricSet:query
POST https://playdeveloperreporting.googleapis.com/v1beta1/apps/{packageName}/anrRateMetricSet:query

# Publishing API: store reviews
GET https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/reviews
```

Publishing uses the `androidpublisher` scope; Reporting uses `playdeveloperreporting`. Do not invent an `installCountMetricSet` or send GET to a documented POST query endpoint. Select the actual supported Console export/API for installation statistics. Fetch freshness metadata and handle pagination; calling the API rather than looking at Console does not remove upstream reporting delay.

## Pre-Launch Reports and Release Readiness

Play's pre-launch testing can discover stability, performance, accessibility and security issues on its tested paths. Coverage, eligible uploads, authentication setup, supported devices and completion time depend on the current service. It is not a guaranteed thirty-minute exhaustive suite for every upload and never replaces the app's own device and upgrade tests.

Review whether the crawler can reach meaningful authenticated flows with safe test accounts. Exercise payment and destructive actions in an appropriate test environment. Capture what paths/devices were covered and investigate gaps instead of treating a green report as universal validation.

## Staged Rollout and Adoption

A staged rollout sets eligibility for an **update**, not immediate installed adoption. Review, publication, user settings, connectivity, device state and foreground use affect timing. Do not promise internal, testing or production delivery in fixed seconds or hours. A halt stops further serving of the release; users who already installed it keep that version.

For one production release, country targeting selects an included set and `userFraction` supplies one rollout percentage. It is not a map of per-country percentages. The Publishing API exposes country targeting, while Play documents constraints on changing the set after starting. A device-catalog exclusion changes device/app availability; it is not a release-scoped canary mechanism. Assess its impact on existing users before using it as mitigation.

## In-App Updates

The API reports update availability, priority and permitted flow types. The app decides whether to request a flexible or immediate update; priority alone does not trigger either UI. Check `isUpdateTypeAllowed`, handle cancellation/failure and process/activity recreation, resume an in-progress flow where documented, and complete a flexible download through its install-state workflow.

An immediate flow is not guaranteed enforcement against every user state. Server compatibility and authorization remain independent. Keep backend support and recovery paths for users who have not installed the new binary.

## Incident Workflow

1. Identify the exact affected version, eligible cohort, metric and evidence freshness.
2. Halt further exposure under the release policy and preserve the evidence.
3. Apply an audited server or client mitigation, accounting for unreachable clients.
4. Reproduce on relevant devices and upgrade paths; do not assume a cloud test lab has every production model.
5. Ship a greater-version-code fix, verify it and recover through staged exposure.

Do not install a second uncaught-exception handler as a blanket fix for missing startup crashes; it cannot recover evidence from before registration or every native/process failure and can interfere with existing handlers. Diagnose the coverage gap using appropriate platform and application signals.

## Further Reading

- [Android vitals collection and definitions](https://developer.android.com/google/play/vitals).
- [Console technical-quality guidance](https://support.google.com/googleplay/android-developer/answer/9844486).
- [ANR metric-set population and dimensions](https://developers.google.com/play/developer/reporting/reference/rest/v1beta1/vitals.anrrate).
- [ANR query method and pagination](https://developers.google.com/play/developer/reporting/reference/rest/v1beta1/vitals.anrrate/query).
- [Publishing release fields](https://developers.google.com/android-publisher/api-ref/rest/v3/edits.tracks).
- [Staged rollout rules](https://support.google.com/googleplay/android-developer/answer/6346149).
- [Pre-launch reports](https://support.google.com/googleplay/android-developer/answer/9842757).
- [In-app update integration](https://developer.android.com/guide/playcore/in-app-updates/kotlin-java).
- [Crashlytics ANR diagnosis](https://firebase.google.com/docs/crashlytics/troubleshooting#anr-requires-android-11-plus).

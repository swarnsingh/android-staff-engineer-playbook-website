# Android Platform Compatibility Program

## Overview

Android compatibility is an annual engineering program, not a late change to `targetSdk`. Four values have different jobs: `minSdk` defines the oldest runtime the app supports; `compileSdk` exposes APIs to the compiler; `targetSdk` opts the app into compatibility behaviors and is constrained by distribution policy; the device API level decides runtime availability. Updating one does not substitute for testing the others.

As of July 29, 2026, Google Play states that beginning August 31, 2026, new phone/tablet apps and updates must target Android 16 (API 36) or higher, with different floors for Wear OS, Automotive OS, TV, and XR. Existing-app availability has a separate target requirement, and an extension path is described through November 1, 2026. These dates are deliberately recorded in the currency watchlist because the official Play page, not this paragraph, is authoritative when planning a release.

## Annual Workflow

1. Inventory platform-touching capabilities: permissions, background work, foreground services, storage, notifications, media, WebView, edge-to-edge, native code, package visibility, and third-party SDKs.
2. Upgrade the toolchain using the official AGP/Gradle/JDK/API compatibility matrix. Keep this distinct from raising `targetSdk` so toolchain failures and behavior changes are diagnosable.
3. Compile against the new SDK and remove blocked/private API assumptions.
4. Test behavior changes that affect all apps on the new OS before opting in.
5. Raise `targetSdk`, then test target-gated changes and Play policy flows.
6. Run a device/API matrix including the oldest supported release, current production concentration, the new OS, low-memory hardware, and relevant form factors.
7. Stage rollout with kill switches, crash/ANR gates, permission and funnel telemetry, and a server-compatible rollback plan.

Use Android compatibility toggles during development to isolate target-gated changes, but do not mistake toggles for release validation. Exercise clean install, upgrade from multiple production versions, restore/backup, permission denial and auto-reset, process death, background/foreground transitions, notification delivery, deep links, and OEM-specific critical paths.

## Ownership

A Staff-level program has a named DRI, capability owners, a dependency/SDK escalation list, policy and store-console owners, and deadlines earlier than the Play cutoff. The release train needs buffer for SDK vendors, app review, staged rollout, and hotfixes. Dashboards segment failures by OS, target, app version, device model, install/upgrade path, and capability.

Do not freeze `minSdk` and `targetSdk` into the same decision. Raising `minSdk` removes users and can simplify code; raising `targetSdk` changes behavior and preserves old-device support. Decide each with separate evidence.

## Failure Modes

- The build compiles with a new SDK but runtime behavior was never tested.
- A third-party SDK declares incompatible components, permissions, or native binaries.
- Teams discover target-gated foreground-service or permission changes during final rollout.
- Only clean installs are tested, missing upgrade and restored-state failures.
- Phone policy is copied to Wear, TV, Automotive, or XR despite different requirements.

## Probing Questions

1. Explain `minSdk`, `compileSdk`, `targetSdk`, and runtime API level.
2. Why split the toolchain upgrade from the target-SDK change?
3. Which test cohorts belong in the annual program?
4. Why is a Play deadline a release-engineering concern months earlier?
5. What evidence supports raising `minSdk`?

## Answer Key

1. They control install eligibility, compile-time API visibility, opted-in behavior/policy, and actual device capability respectively.
2. Separating changes narrows failures and lets teams validate build-system migration before behavior changes.
3. Clean and upgraded installs across oldest/current/new OS versions, key OEMs/form factors, permission states, process/background transitions, restored data, and native-code devices.
4. Vendor fixes, testing, review, staged rollout, and remediation require buffer before submission is blocked.
5. Active-user/device distribution, maintenance and security cost, feature needs, revenue/support impact, and an explicit sunset plan—not convenience alone.

## Further Reading

- [Google Play target API requirements](https://developer.android.com/google/play/requirements/target-sdk)
- [Android behavior changes](https://developer.android.com/about/versions/16/behavior-changes-all)
- [Android Gradle plugin releases and compatibility](https://developer.android.com/build/releases/gradle-plugin)
- [16 KB page-size support](https://developer.android.com/guide/practices/page-sizes)

# Permissions and AppOps

## Overview

Android permissions are the user- and system-facing contract for access to protected data and capabilities: location, camera, microphone, contacts, notifications, Bluetooth, storage/media, exact alarms, background work, and many system APIs.

`AppOps` is the lower-level operation gate Android uses internally to decide whether a specific operation is currently allowed for a UID/package. A manifest permission may be granted, while an app-op mode, user toggle, policy, device state, or platform rule still blocks the actual operation.

Staff-level Android security means understanding both layers: permissions as API contracts, AppOps as runtime enforcement, and user trust as the product constraint.

---

## Why It Matters

1. **Permissions are not just boilerplate.** They define what users and the OS believe your app can do.
2. **Runtime grants can change.** Users can revoke permissions at any time, including while your app is backgrounded.
3. **Modern Android narrows access.** Approximate location, one-time grants, media-specific permissions, notification permission, and background restrictions all reduce ambient access.
4. **AppOps can deny at operation time.** Checking permission once at startup is not enough.
5. **Permission UX affects conversion.** Asking too early or too broadly trains users to deny.

---

## Permission Categories

| Category | Examples | Behavior |
|---|---|---|
| Normal | Internet, network state | Granted at install; low risk |
| Dangerous/runtime | Camera, location, contacts, microphone | User must grant at runtime |
| Signature | Privileged partner/internal APIs | Only apps signed with same cert or platform |
| Special access | Exact alarms, overlay, notification listener | Managed by settings/policy-specific flows |

Do not rely on permission groups as stable product logic. The platform can change grouping and UI across Android versions.

---

## Runtime Permission Flow

```kotlin
when {
    ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.CAMERA
    ) == PackageManager.PERMISSION_GRANTED -> {
        openCamera()
    }

    shouldShowRequestPermissionRationale(Manifest.permission.CAMERA) -> {
        showCameraRationale()
    }

    else -> {
        requestPermissionLauncher.launch(Manifest.permission.CAMERA)
    }
}
```

Staff rule: the permission request should be tied to user intent. Ask for camera when the user taps "scan card," not on first launch.

---

## AppOps Mental Model

Permission check asks:

```text
Does this package hold the declared permission?
```

AppOps asks:

```text
Is this UID/package allowed to perform this specific operation right now?
```

Examples where operation-level rules matter:

- Location may be granted only approximately.
- Background location may be denied even when foreground location is granted.
- Microphone/camera indicators and privacy toggles can block use.
- Exact alarms require special policy/setting paths for many apps.
- Notification posting depends on runtime permission on modern Android.

Do not cache "permission granted" as permanent state. Check at the point of use and handle denial gracefully.

---

## Location Permissions

Location is the canonical example of layered access:

| Need | Permission / Constraint |
|---|---|
| Approximate foreground location | `ACCESS_COARSE_LOCATION` |
| Precise foreground location | `ACCESS_FINE_LOCATION`, user may still choose approximate |
| Background location | `ACCESS_BACKGROUND_LOCATION` plus platform-specific UX |
| Foreground service location | Foreground service type + notification + location permission |

Design the product for reduced accuracy. A weather app should not require precise location. A turn-by-turn navigation app can justify it during active navigation.

---

## Notifications

Modern Android requires runtime permission to post notifications for most apps:

```xml
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

Staff UX:

- Ask after explaining value.
- Respect denial; do not nag.
- Provide in-app settings.
- Keep notification channels meaningful and user-controllable.

---

## Storage and Media

Avoid broad storage access. Prefer:

- App-specific storage for private files.
- Photo picker for user-selected media.
- MediaStore for shared media collections.
- `FileProvider` URI grants for sharing specific files.

Broad file access is a policy and privacy risk. If you need it, the product should have a strong user-facing reason.

---

## Custom Permissions

For cross-app APIs:

```xml
<permission
    android:name="com.example.permission.READ_SECURE_DATA"
    android:protectionLevel="signature" />

<provider
    android:name=".SecureProvider"
    android:authorities="com.example.secure"
    android:exported="true"
    android:readPermission="com.example.permission.READ_SECURE_DATA" />
```

Use signature permissions for trusted suites of apps signed by the same key. Dangerous custom permissions are hard to explain to users and easy to misuse.

---

## Production Patterns

### Permission as State Machine

```kotlin
sealed interface PermissionState {
    data object Granted : PermissionState
    data object NotAsked : PermissionState
    data object Denied : PermissionState
    data object PermanentlyDenied : PermissionState
}
```

Model permission state explicitly in UI. Avoid boolean soup like `hasAsked && !granted && !showRationale`.

### Capability-Oriented APIs

Instead of exposing raw permission decisions everywhere:

```kotlin
interface LocationCapability {
    suspend fun currentLocation(): LocationResult
}
```

The implementation handles permission, settings, accuracy, timeout, and fallback. Callers handle domain outcomes.

---

## Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Crash after revoke | Permission cached as permanent | Check at point of use |
| User denies permission | Asked too early without context | Ask after intent + rationale |
| Background location rejected | Foreground-only design disguised as background need | Redesign or justify active use |
| Feature unusable with approximate location | Assumed precise coordinates | Add degraded mode |
| Play policy issue | Broad storage/package/permission access | Minimize and document need |
| Security bug | Exported component protected by weak/no permission | Signature permission or export false |

---

## Staff Engineer Thinking

1. **Least privilege is product strategy.** Smaller permission surface builds trust.
2. **Permissions are revocable.** Every protected operation needs a denial path.
3. **Design degraded modes.** Approximate/no permission should still produce a useful product where possible.
4. **Audit permissions during architecture review.** Every new `uses-permission` needs owner, feature, and user value.
5. **Separate capability from UI prompts.** Domain code should not know the permission dialog choreography.

---

## Probing Questions

1. What is the difference between normal, dangerous, signature, and special permissions?
2. Why is a granted permission not always enough to perform an operation?
3. Why should permission requests be tied to user intent?
4. How does approximate location change product design?
5. When would you use a signature permission?
6. Why is broad storage access risky?
7. How should UI model permanently denied permission?
8. Why should you check permission at point of use?

## Answer Key

1. **What is the difference between normal, dangerous, signature, and special permissions?**
   Normal permissions are granted automatically at install. Dangerous permissions require explicit runtime user consent. Signature permissions are granted only to apps signed with the same certificate. Special permissions require the user to navigate to system settings to toggle access manually.
2. **Why is a granted permission not always enough to perform an operation?**
   Because Android uses AppOps as a secondary runtime gate. Even if a manifest permission is granted, AppOps might deny the operation due to device state, privacy toggles, background restrictions, or enterprise policies.
3. **Why should permission requests be tied to user intent?**
   Asking for permissions out of context (like on app startup) trains users to deny them out of suspicion. Tying requests to a specific user action (e.g., tapping a microphone icon) provides clear context and drastically improves grant rates.
4. **How does approximate location change product design?**
   It forces products to degrade gracefully. Apps must be designed to provide useful functionality (like city-level weather or nearby restaurants) without failing or blocking the user if they refuse to grant precise GPS coordinates.
5. **When would you use a signature permission?**
   When building a suite of applications (like a company's ecosystem of apps) or a secure SDK that needs to expose sensitive IPC APIs that should absolutely never be accessible to third-party or malicious apps on the device.
6. **Why is broad storage access risky?**
   It grants access to potentially sensitive user files, photos, and documents across the entire device, presenting a massive privacy risk and increasing the likelihood of App Store policy rejection. Scoped storage or FileProviders should be used instead.
7. **How should UI model permanently denied permission?**
   It should be modeled as an explicit state (e.g., `PermanentlyDenied`) that triggers UI to explain why the feature is disabled and provides a clear, deep-linked button to the OS App Settings screen so the user can manually re-enable it.
8. **Why should you check permission at point of use?**
   Users or the OS can revoke permissions at any time while the app is in the background. Caching a "granted" state during startup will lead to a SecurityException and a hard crash if the permission is subsequently revoked before the operation occurs.

## Further Reading

- [`intent-resolution-and-manifest.md`](intent-resolution-and-manifest.md)
- [`content-providers-and-contentresolver.md`](content-providers-and-contentresolver.md)
- [`../networking-and-security/security-and-keystore.md`](../networking-and-security/security-and-keystore.md)
- [`../../security/privacy-gdpr-data-residency.md`](../../security/privacy-gdpr-data-residency.md)
- [Android Developers: Permissions on Android](https://developer.android.com/guide/topics/permissions/overview)
- [Android Developers: Request app permissions](https://developer.android.com/training/permissions/requesting)

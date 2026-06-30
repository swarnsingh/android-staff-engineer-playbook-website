# Release Engineering: Android App Bundles (AAB)

> Why Play accepts `.aab` not `.apk`, what splits Play generates from the bundle, and how to ship dynamic delivery without breaking offline installs or testing.

---

## 1. AAB vs APK

An `.apk` is the final installer: code + resources for a specific ABI, screen density, and language. An `.aab` is your bundle of all of those — Play uses it to *generate* per-device APKs at download time.

| Aspect | APK | AAB |
|---|---|---|
| Contains | Per-device build | All variants in one |
| Distributed to user | Yes (directly) | Never (Play generates per-device APK from it) |
| Size on download | Full APK | Only what device needs (40-60% smaller typical) |
| Signing | You sign final APK | You sign bundle; Play re-signs the generated APK |
| Required by Play | No | Yes (since Aug 2021 for new apps) |
| Side-loadable | Yes | No (via `bundletool` only) |

The size win is the main pitch. A "universal" APK with all densities, ABIs, and languages might be 80 MB; the AAB-generated device-specific APK is 30-50 MB.

---

## 2. Building An AAB

```kotlin
// app/build.gradle.kts
android {
    bundle {
        language { enableSplit = true }    // one locale per device
        density  { enableSplit = true }    // one density per device
        abi      { enableSplit = true }    // one ABI per device
    }
}
```

```bash
./gradlew :app:bundleRelease
# Output: app/build/outputs/bundle/release/app-release.aab
```

The AAB is a ZIP-like format containing:

```
app-release.aab
├── base/                   ← always installed
│   ├── manifest/AndroidManifest.xml
│   ├── dex/
│   ├── res/
│   ├── lib/{abi}/
│   └── assets/
├── dynamic-feature-foo/    ← dynamic feature module (optional)
└── BundleConfig.pb         ← split configuration
```

---

## 3. Splits Play Generates

Play's Dynamic Delivery slices the bundle along three axes:

| Split type | Examples | What user gets |
|---|---|---|
| **Language** | `values-en`, `values-es`, `values-ar` | Resources matching device locale |
| **Density** | `drawable-mdpi/hdpi/xhdpi/xxhdpi` | One density bucket |
| **ABI** | `armeabi-v7a`, `arm64-v8a`, `x86_64` | One CPU architecture |

A Pixel 7 (arm64, xxhdpi, en-US) downloads only `base + en + xxhdpi + arm64-v8a`. The bundle on Play has all variants; only the relevant slice ships.

> **Verify with bundletool.** `bundletool build-apks --bundle=app.aab --output=app.apks` produces a `.apks` ZIP — extract it and inspect what device-class APKs were generated.

---

## 4. Dynamic Feature Modules

Ship features as separate downloadable modules — installed on demand or conditionally based on device class.

```kotlin
// settings.gradle.kts
include(":app", ":feature:premium", ":feature:onboarding-rich")
```

```kotlin
// feature/premium/build.gradle.kts
plugins {
    id("com.android.dynamic-feature")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.feature.premium"
    compileSdk = 35
    defaultConfig { minSdk = 26 }
}

dependencies {
    implementation(project(":app"))            // dynamic feature depends on app, not vice versa
    implementation(libs.androidx.core)
}
```

```xml
<!-- feature/premium/src/main/AndroidManifest.xml -->
<manifest xmlns:dist="http://schemas.android.com/apk/distribution">
    <dist:module
        dist:instant="false"
        dist:title="@string/premium_title">
        <dist:delivery>
            <dist:on-demand />
        </dist:delivery>
        <dist:fusing dist:include="true" />
    </dist:module>
</manifest>
```

| Delivery mode | When installed |
|---|---|
| `on-demand` | App requests download at runtime |
| `install-time` | At app install, included by default |
| `conditional` | Install-time, but only on devices meeting criteria (min SDK, RAM, country) |
| `instant` | Available for Instant Apps via Play Instant |

```kotlin
// Request on-demand install
class PremiumModuleInstaller @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val manager = SplitInstallManagerFactory.create(context)

    suspend fun installPremium(): Boolean = suspendCancellableCoroutine { cont ->
        val request = SplitInstallRequest.newBuilder()
            .addModule("premium")
            .build()
        manager.startInstall(request)
            .addOnSuccessListener { cont.resume(true) {} }
            .addOnFailureListener { cont.resume(false) {} }
    }
}
```

After installation, the new module's classes are available via `SplitCompat` integration in your `Application` and `Activity` base classes.

---

## 5. Asset Packs (Large Assets, Out of the Base APK)

For games or apps shipping > 200 MB of assets, asset packs separate them from the binary:

```kotlin
// asset_pack/build.gradle.kts
plugins { id("com.android.asset-pack") }

assetPack {
    packName.set("game_levels")
    dynamicDelivery {
        deliveryType.set("on-demand")    // or "install-time", "fast-follow"
    }
}
```

Limits:
- Base APK: up to 200 MB.
- Each install-time asset pack: up to 1 GB.
- Total install-time assets: up to 2 GB.
- On-demand asset packs: up to 1 GB each, total uncapped (within Play's overall limits).

Without asset packs, the 200 MB base APK cap is a hard wall. With them, you can ship games up to several GB.

---

## 6. Conditional Delivery

```xml
<dist:module>
    <dist:delivery>
        <dist:install-time>
            <dist:conditions>
                <dist:device-feature dist:name="android.hardware.camera.ar" />
                <dist:min-sdk dist:value="28" />
                <dist:user-countries dist:exclude="false">
                    <dist:country dist:code="US" />
                    <dist:country dist:code="GB" />
                </dist:user-countries>
            </dist:conditions>
        </dist:install-time>
    </dist:delivery>
</dist:module>
```

Useful for:
- AR features only for AR-capable devices.
- Country-specific compliance modules.
- High-RAM-only features.

---

## 7. Testing AAB Builds Locally (bundletool)

Side-loading an AAB on a device is a two-step process:

```bash
# Generate the device-specific APKs from the AAB
bundletool build-apks \
  --bundle=app/build/outputs/bundle/release/app-release.aab \
  --output=local.apks \
  --connected-device \
  --ks=upload-key.jks \
  --ks-pass=pass:$KS_PASS \
  --ks-key-alias=upload \
  --key-pass=pass:$KEY_PASS

# Install on the connected device
bundletool install-apks --apks=local.apks
```

`--connected-device` tells bundletool to pick splits matching the attached device. For testing a specific device class:

```bash
bundletool build-apks \
  --bundle=app.aab \
  --output=mid-tier-emerging-market.apks \
  --device-spec=device-specs/mid-tier-emerging-market.json
```

```json
{
  "supportedAbis": ["armeabi-v7a"],
  "supportedLocales": ["pt-BR"],
  "screenDensity": 320,
  "sdkVersion": 28
}
```

This is the only sane way to debug "this works on flagship, breaks on emerging market" issues.

---

## 8. AAB Size Gates In CI

```bash
# Generates a report.json showing per-device APK sizes
bundletool get-size total --apks=local.apks
```

```
+--------+--------+
| MIN    | MAX    |
+--------+--------+
| 25 MB  | 41 MB  |
+--------+--------+
```

By dimension:

```bash
bundletool get-size total --apks=local.apks --dimensions=SDK,ABI,LANGUAGE
```

CI gate: fail the build if any device class crosses a threshold:

```yaml
- name: AAB size gate
  run: |
    MAX_MB=$(bundletool get-size total --apks=local.apks | tail -1 \
              | awk -F'|' '{print $3}' | tr -d ' MB')
    if [ "$MAX_MB" -gt 50 ]; then
      echo "ERROR: max-device APK size $MAX_MB MB exceeds 50 MB budget"
      exit 1
    fi
```

### Size budget matrix

Use multiple device specs, not one global max. A flagship `arm64` English install and a low-end `armeabi-v7a` install can have different risk profiles.

| Device class | Example budget | Why |
|---|---|---|
| Low-end emerging market | 35 MB max download | Install conversion and storage pressure |
| Mid-tier global | 50 MB max download | Default product budget |
| High-end flagship | 65 MB max download | More native/high-density assets acceptable |
| Internal universal APK | No product budget | QA artifact only; never compare to user download |

For every regression, store:
- AAB size.
- Generated APK size by device spec.
- Top growing files/modules.
- Owning team.
- Whether the feature is base, install-time, conditional, or on-demand.

This is how app size becomes governable instead of emotional.

---

## 9. ABI and Density — Sanity Checks

```kotlin
android {
    bundle { abi { enableSplit = true } }
    splits { abi { isEnable = false } }   // bundle handles this, not legacy splits
}
```

`splits { abi { isEnable = true } }` is the OLD per-APK split mechanism. With AAB, leave it disabled.

For native libraries (`.so` files), audit what ABIs you actually ship:

```bash
unzip -l app-release.aab | grep '\.so$' | awk -F/ '{print $3}' | sort -u
# Expect: arm64-v8a, armeabi-v7a (drop x86 unless you support emulators in distribution)
```

---

## 10. The Universal APK (Internal Distribution Only)

For internal QA on heterogeneous devices, generate a universal APK:

```bash
bundletool build-apks --bundle=app-release.aab --output=universal.apks --mode=universal
unzip -p universal.apks universal.apk > universal.apk
```

This APK works on any device matching min-SDK. Never ship to Play — defeats the point. Use only for:
- QA on devices Play won't accept (special-purpose hardware).
- Side-load to enterprise distribution outside Play.
- Forensic reproducibility.

---

## 11. Common Pitfalls

- **Treating dynamic features as optional after launch.** Once shipped, removing a dynamic feature requires version bump + manifest cleanup. Plan splits at design time.
- **Not testing on low-tier device-spec.** Flagship devs see a tiny APK; mid-tier emerging market may see 45 MB and break update budgets.
- **Forgetting `SplitCompat`.** Without `SplitCompatApplication` and `SplitCompat.install(Activity)`, freshly-installed dynamic modules don't work until process restart.
- **Asset packs with on-demand delivery but no UX for download progress.** Users wonder why nothing happens.
- **`splits` block and `bundle` block both enabled.** Conflicting — pick one.
- **Disabling language splits to ship all locales.** Wastes per-device size unless you support runtime language switching.
- **Universal APK leaking to Play.** Configure `play { artifactDir }` to point only to AAB, never universal APK.
- **No size budget gate in CI.** Bundles grow silently. Set a per-device-class budget.
- **`bundletool` version mismatch with build-tools.** Pin both.

---

## 12. Further Reading

- [Android Developers — App Bundles overview](https://developer.android.com/guide/app-bundle) — official.
- [bundletool](https://developer.android.com/tools/bundletool) — local AAB inspection.
- [Dynamic delivery](https://developer.android.com/guide/playcore/feature-delivery) — Play Feature Delivery API.
- [Asset delivery](https://developer.android.com/guide/playcore/asset-delivery) — large assets.
- [SplitCompat](https://developer.android.com/reference/com/google/android/play/core/splitcompat/SplitCompat) — runtime support for dynamic features.

---

> **In short:** AAB is the only Play upload format that matters today. Enable `language`/`density`/`abi` splits. Dynamic features for on-demand. Asset packs for > 200 MB. Test with bundletool against a device-spec JSON. Gate size in CI.

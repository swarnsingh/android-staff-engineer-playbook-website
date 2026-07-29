# 16 KB Page Sizes: The Native-Code Compliance Gate

Since **November 1, 2025**, Google Play requires that all new apps and updates targeting Android 15 (API 35) or higher support devices with 16 KB memory pages. This composes with the target-API policy — new apps and updates must target API 35+ already, and **API 36+ from August 31, 2026** (extension available to November 1, 2026) — so for any actively shipped app, 16 KB support is not optional. It belongs in release engineering because the failure mode is a *blocked release*: a single misaligned `.so` from a transitive SDK stops your submission.

## 1. Why the platform moved

ARM64 kernels can use 4 KB or 16 KB pages. Larger pages mean fewer TLB misses and less page-table overhead as devices grow RAM: Google measured ~3% faster average app launch (up to 30% for some apps), ~4.5% lower power draw during launch, and ~8% faster boot on 16 KB configurations. Manufacturers are shipping 16 KB devices, so Play now enforces compatibility at submission time.

## 2. Who is affected

- **Pure Kotlin/Java apps (including all their libraries): compliant by default.** Nothing to do.
- **Apps with native code** — your own NDK code *or any dependency shipping `.so` files* (crash reporters, media, ML runtimes, database engines, React Native/Flutter/Unity) — must be built with 16 KB-aligned ELF segments and properly packaged.

At staff level the second bullet is an *inventory problem*: most large apps have 30–80 `.so` files, and the long tail comes from transitive dependencies nobody on the team chose deliberately.

## 3. The two alignment requirements

Compliance is two separate properties, and both must hold:

1. **ELF LOAD-segment alignment** — every `.so` must be linked with 16 KB max-page-size so its LOAD segments show `align 2**14` (or higher):

```bash
llvm-objdump -p libfoo.so | grep LOAD
# every LOAD line must show align 2**14 or greater
```

2. **ZIP packaging alignment** — uncompressed `.so` entries inside the APK must sit on 16 KB boundaries:

```bash
zipalign -v -c -P 16 4 app-release.apk
# must print: Verification successful
```

Toolchain versions that make this automatic:

| Tool | Version | Effect |
|---|---|---|
| AGP | **8.5.1+** | Packages `.so` files 16 KB ZIP-aligned by default |
| NDK | **r28+** | Links 16 KB-aligned ELF segments by default |
| NDK ≤ r27 | manual | Add both `-Wl,-z,max-page-size=16384` and `-Wl,-z,common-page-size=16384` to linker flags |
| AGP ≤ 8.5 | escape hatch | `jniLibs.useLegacyPackaging = true` (compressed libs; bigger installed size — a last resort) |

Prebuilt third-party `.so` files ignore your toolchain: they were linked wherever the vendor built them. Those you can only *detect* and demand updates for.

## 4. Runtime assumptions (the subtle class)

Alignment gets you loaded; hardcoded page-size math still crashes at runtime. Audit native code for:

```c
#define PAGE_SIZE 4096              // ❌ wrong on 16 KB devices
int ps = getpagesize();             // ✅ query at runtime
int ps = sysconf(_SC_PAGESIZE);     // ✅ equivalent
```

Anything doing `mmap()` arithmetic, custom allocators, or ELF parsing with a 4096 constant is suspect. This is why "it links and loads" is not the end of testing.

## 5. Detection and CI

- **Play Console app bundle explorer** shows your build's compliance verdict — the authoritative check, since Play is the enforcer.
- **Android Studio** APK Analyzer shows an Alignment column for `lib/`; lint flags misaligned prebuilts.
- **CI gate:** run the alignment checks on every release candidate so a newly bumped SDK can't regress you silently:

```bash
# fail the build if any 64-bit .so is misaligned — check every 64-bit ABI
# you ship (arm64-v8a AND x86_64; universal/internal artifacts often carry both)
unzip -o app-release.apk 'lib/arm64-v8a/*' 'lib/x86_64/*' -d out/
for so in out/lib/arm64-v8a/*.so out/lib/x86_64/*.so; do
  [ -e "$so" ] || continue
  llvm-objdump -p "$so" | awk '/LOAD/ && $NF !~ /2\*\*(1[4-9]|[2-9][0-9])/ { exit 1 }' || {
    echo "UNALIGNED: $so"; exit 1; }
done
zipalign -c -P 16 4 app-release.apk
```

This slots next to your existing [AAB size gates](app-bundles.md) in the release pipeline: same philosophy — catch it at build time, not at submission time.

## 6. Testing on 16 KB configurations

- **Emulator:** install the "Google APIs Experimental 16 KB Page Size" system images (ARM64 and x86_64) from SDK Manager; verify with `adb shell getconf PAGE_SIZE` → `16384`.
- **Hardware:** Pixel 8/8a/8 Pro (Android 15 QPR1+) and Pixel 9 series (QPR2+) expose **Developer options → Boot with 16KB page size**.
- Run your instrumentation and smoke suites on a 16 KB image at least once per release cycle if you ship native code — runtime page-size bugs (§4) only reproduce there.

## 7. Backcompat mode — and why not to rely on it

Devices can run a 4 KB-aligned app on a 16 KB kernel in a compatibility mode, but it shows users a warning dialog on first launch, and **Android 17 can treat incompatible binaries as fatal** (`bionic.linker.16kb.app_compat.enabled fatal`). Play submission enforcement plus a user-visible warning plus a future hard failure means backcompat mode is a grace period, not a strategy. The `android:pageSizeCompat` manifest attribute only suppresses the warning; it doesn't fix the binaries.

## 8. The staff-level rollout playbook

1. **Inventory:** enumerate every `.so` in the release artifact and map each to an owning team or vendor. The mapping is the hard part and pays off for every future platform migration.
2. **Upgrade the toolchain floor:** use a current AGP and NDK across all modules (convention plugins make this one change — see [Convention Plugins](../android/build-tooling/convention-plugins.md)). For Play submissions targeting Android 15+, verify 16 KB support against the current Android guidance rather than treating the historical minimum as a permanent recommendation.
3. **Chase vendors:** file upgrade tickets for every misaligned third-party SDK with the submission deadline as leverage; track them like any other launch blocker.
4. **Gate:** add the CI check (§5) before the first compliant release ships, so compliance can't silently regress.
5. **Test:** one full pass on a 16 KB emulator image per release; targeted native-code tests for anything that does page-size math.

The general lesson: Play compliance deadlines (target API, 16 KB, billing library versions) are recurring, externally imposed release-train events. Teams that maintain a dependency inventory and a toolchain floor treat them as routine; teams that don't discover them as submission-week emergencies.

## Further Reading

- [Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes) — the canonical guide: detection, fixes, testing
- [Prepare your apps for Google Play's 16 KB requirement](https://android-developers.googleblog.com/2025/05/prepare-play-apps-for-devices-with-16kb-page-size.html) — the policy announcement
- [Google Play target API level requirement](https://developer.android.com/google/play/requirements/target-sdk) — the composing deadline (API 36 from August 31, 2026)

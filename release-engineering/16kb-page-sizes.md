# 16 KB Page Sizes: The Native-Code Compliance Gate

Google Play's [current 16 KB compatibility policy](https://developer.android.com/guide/practices/page-sizes#google-play-compatibility-requirement) applies to apps targeting Android 15 (API 35) or higher on 64-bit devices. Starting **February 1, 2027**, Play will block updates that do not support 16 KB memory pages. The earlier November 1, 2025 deadline was superseded. The separate target-API policy has required API 36+ for most new apps and updates since August 31, 2026 (with form-factor exceptions; the published extension ended November 1, 2026). Treat 16 KB support as release work now: a misaligned `.so` from a transitive SDK can prevent a future submission and can fail on devices already using 16 KB pages.

## 1. Why the platform moved

ARM64 kernels can use 4 KB or 16 KB pages. Larger pages mean fewer TLB misses and less page-table overhead as devices grow RAM: Google measured ~3% faster average app launch (up to 30% for some apps), ~4.5% lower power draw during launch, and ~8% faster boot on 16 KB configurations. Manufacturers are shipping 16 KB devices, and Play's update-submission block begins February 1, 2027.

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

Prebuilt third-party `.so` files ignore your toolchain: they were linked wherever the vendor built them. Those you can only *detect* and demand updates for. Managing these 16KB `.so` migrations is often the longest pole in the tent: platform engineers must audit all transitives and replace or escalate non-compliant vendor prebuilts. Use the time before the February 1, 2027 update-submission block to replace incompatible vendor prebuilts and test on 16 KB devices.

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

```python
# scripts/check_elf_alignment.py
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

apk = Path(sys.argv[1])
with zipfile.ZipFile(apk) as archive, tempfile.TemporaryDirectory() as directory:
    for entry in archive.infolist():
        parts = entry.filename.split("/")
        if (len(parts) != 3 or parts[0] != "lib" or
                parts[1] not in {"arm64-v8a", "x86_64"} or not parts[2].endswith(".so")):
            continue
        binary = Path(directory) / "library.so"
        binary.write_bytes(archive.read(entry))
        output = subprocess.run(["llvm-objdump", "-p", str(binary)],
                                check=True, capture_output=True, text=True).stdout
        loads = [line for line in output.splitlines() if re.search(r"\bLOAD\b", line)]
        if not loads:
            raise SystemExit(f"No LOAD segments: {entry.filename}")
        for line in loads:
            alignment = re.search(r"align\s+2\*\*(\d+)", line)
            if alignment is None or int(alignment.group(1)) < 14:
                raise SystemExit(f"Unaligned or unrecognized LOAD: {entry.filename}")
subprocess.run(["zipalign", "-c", "-P", "16", "4", str(apk)], check=True)
```

A tool failure, unrecognized output or missing LOAD segment fails this gate. Fresh temporary files prevent a previous artifact's libraries from satisfying it. Validate the parser against the pinned LLVM output, and run it on generated APKs for every supported 64-bit configuration, not only the AAB container. Packaging/alignment is still separate from runtime tests.



This slots next to your existing [AAB size gates](app-bundles.md) in the release pipeline: same philosophy — catch it at build time, not at submission time.

## 6. Testing on 16 KB configurations

- **Emulator:** install the "Google APIs Experimental 16 KB Page Size" system images (ARM64 and x86_64) from SDK Manager; verify with `adb shell getconf PAGE_SIZE` → `16384`.
- **Hardware:** Pixel 8/8a/8 Pro (Android 15 QPR1+) and Pixel 9 series (QPR2+) expose **Developer options → Boot with 16KB page size**.
- Run your instrumentation and smoke suites on a 16 KB image at least once per release cycle if you ship native code — runtime page-size bugs (§4) only reproduce there.

## 7. Backcompat mode — and why not to rely on it

Devices can run a 4 KB-aligned app on a 16 KB kernel in a compatibility mode, but it shows users a warning dialog on first launch, and **Android 17 can treat incompatible binaries as fatal** (`bionic.linker.16kb.app_compat.enabled fatal`). The announced Play update-submission block, a user-visible warning, and a possible hard failure mean backcompat mode is a grace period, not a strategy. The `android:pageSizeCompat` manifest attribute configures compatibility-mode behavior and its warning; it does not realign or rebuild incompatible binaries.

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
- [Google Play target API level requirement](https://developer.android.com/google/play/requirements/target-sdk) — API 36 from August 31, 2026 for most new apps and updates, with form-factor exceptions

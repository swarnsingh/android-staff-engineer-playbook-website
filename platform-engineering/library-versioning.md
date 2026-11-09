# Platform Engineering: Library Versioning & Dependency Management

> A 200-module project with no versioning discipline is a runtime bomb. Two modules pull two versions of OkHttp; Gradle silently picks one; the other module's code path crashes in production on a device you can't reproduce. The Platform team's job is to make this class of bug structurally impossible.

---

> [!NOTE]
> **Kotlin Multiplatform Deep Dive:** For a comprehensive guide on managing dependencies across source sets (`commonMain`, `iosMain`) using Version Catalogs in a KMP environment, see [`../android/kotlin-multiplatform/tooling/build-system-and-source-sets.md`](../android/kotlin-multiplatform/tooling/build-system-and-source-sets.md).

---

## The Three Problems Versioning Solves

1. **Alignment** — every consumer of `Retrofit` in your build uses the same version.
2. **Predictability** — upgrades happen on a schedule, not by accident.
3. **Safety** — public-API changes in your own SDKs surface at compile time, not at runtime in a customer's hand.

A Platform team that solves these three earns the right to ship cross-cutting upgrades for the whole org.

---

## The Gradle Version Catalog (`libs.versions.toml`)

Hardcoded dependency strings across 200 `build.gradle.kts` files are a maintenance graveyard.

```kotlin
// BAD — every module repeats versions
dependencies {
    implementation("com.squareup.retrofit2:retrofit:3.0.0")
    implementation("com.squareup.okhttp3:okhttp:5.5.1")
}
```

The version catalog centralizes it (versions shown are illustrative; check each library's release notes before copying them):

```toml
# gradle/libs.versions.toml
[versions]
kotlin = "2.4.21"
agp = "9.5.1"
compose-bom = "2026.09.00"
retrofit = "3.0.0"
okhttp = "5.5.1"
hilt = "2.60.1"
room = "2.8.5"
coroutines = "1.11.0"

[libraries]
compose-bom = { module = "androidx.compose:compose-bom", version.ref = "compose-bom" }
retrofit-core = { module = "com.squareup.retrofit2:retrofit", version.ref = "retrofit" }
retrofit-converter-moshi = { module = "com.squareup.retrofit2:converter-moshi", version.ref = "retrofit" }
okhttp-core = { module = "com.squareup.okhttp3:okhttp", version.ref = "okhttp" }
okhttp-logging = { module = "com.squareup.okhttp3:logging-interceptor", version.ref = "okhttp" }
hilt-android = { module = "com.google.dagger:hilt-android", version.ref = "hilt" }
hilt-compiler = { module = "com.google.dagger:hilt-android-compiler", version.ref = "hilt" }

[bundles]
networking = ["retrofit-core", "retrofit-converter-moshi", "okhttp-core", "okhttp-logging"]

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
```

Consumers:

```kotlin
// :feature:cart:impl/build.gradle.kts
dependencies {
    implementation(libs.bundles.networking)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
}
```

Upgrading Retrofit globally is one line in `libs.versions.toml`. The IDE auto-completes library refs. A typo'd module name is a build error, not a runtime mystery.

---

## Bill of Materials (BOM): Aligning Library Ecosystems

Some library families ship dozens of artifacts that must be version-compatible (Compose, Firebase, Kotlinx Coroutines test+core, AndroidX Lifecycle). Mixing versions across them is silent breakage.

```kotlin
dependencies {
    // Pin ONE version — the BOM — and let it pick the matrix
    implementation(platform(libs.compose.bom))

    // No versions here. BOM dictates.
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.ui:ui-tooling-preview")
}
```

For your own internal SDKs that span many artifacts, **publish your own BOM**:

```kotlin
// :sdk:bom/build.gradle.kts
plugins {
    `java-platform`
    `maven-publish`
}
dependencies {
    constraints {
        api("com.yourorg.sdk:auth:1.4.0")
        api("com.yourorg.sdk:analytics:2.1.0")
        api("com.yourorg.sdk:design-system:3.0.0")
        api("com.yourorg.sdk:networking:1.7.2")
    }
}
publishing {
    publications {
        create<MavenPublication>("bom") {
            from(components["javaPlatform"])
            groupId = "com.yourorg.sdk"
            artifactId = "sdk-bom"
            version = "2024.06"
        }
    }
}
```

Now consumers (your Rider app, Driver app, Merchant app) import one BOM and get a guaranteed-compatible matrix:

```kotlin
implementation(platform("com.yourorg.sdk:sdk-bom:2024.06"))
implementation("com.yourorg.sdk:auth")        // no version
implementation("com.yourorg.sdk:analytics")   // no version
```

Versioning the BOM by calendar (`2024.06`, `2024.09`), as the Compose BOM does, makes the cadence visible. Every quarter, a new BOM; consumers upgrade at their own pace. SemVer-style BOM versions also work: the Firebase Android BoM bumps its major version when it removes libraries (v34.0.0 dropped the KTX artifacts). Pick one scheme and document what a bump means.

---

## Semantic Versioning for Internal SDKs

When your Platform team publishes SDKs to a private Maven repo and other Android apps in the company consume them, SemVer is the contract.

| Bump | Triggers | Examples |
|---|---|---|
| **PATCH** (`x.y.Z`) | Internal change only | Bug fix; refactor; perf improvement |
| **MINOR** (`x.Y.0`) | Backwards-compatible additions | New function, new overload that keeps the old signature, new module |
| **MAJOR** (`X.0.0`) | Breaking change | Removed function, changed signature, changed default behavior |

The rule: **if a consumer's code that used to compile, link and run on version `X.Y.Z` no longer compiles, fails to link (`NoSuchMethodError`) or breaks its documented contract on a later version, it's a MAJOR bump.** In Kotlin, adding a parameter with a default value keeps source compatibility but changes the JVM signature, so already-compiled callers break; keep the old signature as an overload (or use the experimental `@IntroducedAt`) to make it a MINOR change.

### Enforce with ABI validation

Manual SemVer policing fails at scale. Snapshot the ABI and fail CI on accidental changes. The Kotlin Gradle plugin now has experimental built-in [binary compatibility validation](https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html) (`kotlin { abiValidation() }`, tasks `checkKotlinAbi` / `updateKotlinAbi`). The older [`binary-compatibility-validator`](https://github.com/Kotlin/binary-compatibility-validator) plugin is in maintenance mode but still widely used; its workflow is shown here:

```kotlin
// :sdk:auth/build.gradle.kts
plugins {
    id("org.jetbrains.kotlinx.binary-compatibility-validator") version "0.18.2"
}
```

Run `./gradlew apiDump` once to create `:sdk:auth/api/auth.api`, listing every public class, function, and field, and commit it. From then on `apiCheck` (part of `check`) compares the build against it. Any diff fails CI unless the engineer regenerates the dump (`./gradlew apiDump`) — which forces them to explicitly acknowledge the API change in the PR.

```diff
 public final class com/yourorg/sdk/auth/AuthClient {
-    public final fun login (Ljava/lang/String;Ljava/lang/String;)V
+    public final fun login (Ljava/lang/String;)V
 }
```

A reviewer sees the diff in the `.api` file and asks: "Did you mean to remove the password param? If so, this is a MAJOR bump."

### Explicit API Mode

Kotlin defaults class members to `public`. Engineers forget visibility modifiers; private helpers accidentally become public ABI.

```kotlin
// :sdk:auth/build.gradle.kts
kotlin {
    explicitApi()    // strict: declarations that would be public by default need an explicit modifier
}
```

Now the compiler refuses to build until every declaration that would otherwise be public by default has an explicit visibility (and public functions and properties have explicit types). The SDK's public surface stays intentional.

---

## Resolution Strategy: When Versions Conflict

If `:feature:cart` brings OkHttp 4.12 and `:sdk:analytics` brings OkHttp 4.9, Gradle picks the higher version by default. Usually fine. Sometimes catastrophic.

Detect and audit:

```kotlin
// :app/build.gradle.kts
configurations.all {
    resolutionStrategy {
        failOnVersionConflict()   // hard-fail until a human resolves
        // OR force a specific version:
        force("com.squareup.okhttp3:okhttp:4.12.0")
    }
}
```

For routine audit, run:

```bash
./gradlew :app:dependencies --configuration releaseRuntimeClasspath > deps.txt
# Look for lines containing "->" indicating version upgrade
grep " -> " deps.txt
```

When you spot a forced upgrade you didn't expect, file a JIRA, pin the version explicitly, and notify the responsible team.

### `strictly` / `require` / `prefer` declarations

```kotlin
dependencies {
    implementation("com.squareup.okhttp3:okhttp") {
        version {
            strictly("4.12.0")   // excludes every other version; can downgrade transitive requests
        }
    }
}
```

Use `strictly` only when a specific version is load-bearing and must not move. On a declared dependency it can downgrade what other modules request; on a transitive one, resolution fails if no acceptable version exists. For a security floor ("at least the patched version"), a normal `require` version or a dependency constraint is enough and still lets later upgrades through. Gradle recommends `strictly` over `resolutionStrategy.force()` for new builds. Otherwise prefer the catalog default.

---

## Dependency Update Automation

A Platform team should not manually check for new versions. Automate it.

```json
{
  "extends": ["config:recommended"],
  "labels": ["dependencies"],
  "schedule": ["after 1am on monday"],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "automerge": true,
      "automergeType": "branch"
    },
    {
      "matchPackageNames": ["/^com\\.yourorg\\.sdk/"],
      "schedule": ["at any time"],
      "minimumReleaseAge": "0 days"
    },
    {
      "matchUpdateTypes": ["major"],
      "addLabels": ["needs-rfc"]
    }
  ]
}
```

Renovate (configured in `renovate.json`, above) or Dependabot scans `libs.versions.toml`, opens PRs for new releases, runs full CI, and merges patches automatically if green. Majors and minors land in a PR queue for the Platform team to review.

Gate dangerous bumps:

- **PATCH** — auto-merge on green CI.
- **MINOR** — Platform team reviewer required.
- **MAJOR** — RFC required; coordinated rollout.

Measure the time it saves; at scale it adds up quickly.

### Dependency governance board

New top-level dependencies are platform surface area. They need a lightweight review before they become everyone else's transitive problem.

| Question | Why it matters |
|---|---|
| Who owns upgrades and security advisories? | Unowned libraries rot |
| Is it on the paved road or team-owned dirt road? | Determines support expectations |
| What is the method count, DEX, native, and resource impact? | Size and startup budgets are real |
| Does it bring annotation processors? | Build graph and KAPT/KSP impact |
| Does it require keep rules or reflection? | R8 and crash risk |
| Does it duplicate an existing capability? | Fragmentation tax |
| What is the exit plan? | Prevents permanent vendor lock-in |

Review does not mean "platform says no." It means the maintenance cost is visible before the dependency lands. Approved dependencies go into the version catalog with an owner comment; rejected dependencies can still be used as dirt-road choices if the feature team accepts the support burden.

---

## Internal SDK Repos: Private Maven

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://artifactory.yourorg.internal/android-releases")
            credentials {
                username = providers.gradleProperty("artifactoryUser").orNull
                    ?: System.getenv("ARTIFACTORY_USER")
                password = providers.gradleProperty("artifactoryPassword").orNull
                    ?: System.getenv("ARTIFACTORY_PASSWORD")
            }
            mavenContent { releasesOnly() }
        }
        maven {
            url = uri("https://artifactory.yourorg.internal/android-snapshots")
            mavenContent { snapshotsOnly() }
        }
    }
}
```

Conventions:

- Releases (`1.2.0`) are immutable; once published, never overwritten.
- Snapshots (`1.2.0-SNAPSHOT`) are mutable; for cross-team integration testing only.
- Production app builds **never** depend on `-SNAPSHOT` versions. Enforce in CI.

```kotlin
// :app/build.gradle.kts — guard every release variant (release, demoRelease, …)
androidComponents {
    onVariants(selector().withBuildType("release")) { variant ->
        val variantName = variant.name
        listOf(variant.compileConfiguration, variant.runtimeConfiguration).forEach { classpath ->
            classpath.resolutionStrategy.eachDependency {
                if (requested.version?.endsWith("-SNAPSHOT") == true) {
                    throw GradleException("SNAPSHOT dependency in $variantName: ${requested.module}")
                }
            }
        }
    }
}
```

Select variants through the Android variant API rather than by configuration-name prefix: with product flavors, release classpaths are named `<flavor>ReleaseCompileClasspath` and `<flavor>ReleaseRuntimeClasspath` (for example `demoReleaseRuntimeClasspath`), so a `startsWith("release")` filter would silently skip them.

---

## Deprecation: How to Remove an API Without Burning Trust

You decided `AuthClient.login(username, password)` should become `AuthClient.login(credentials: Credentials)`. Don't just delete the old function.

```kotlin
public class AuthClient {
    @Deprecated(
        message = "Use login(Credentials) for safer credential handling. Removed in 3.0.",
        replaceWith = ReplaceWith("login(Credentials(username, password))"),
        level = DeprecationLevel.WARNING,
    )
    public fun login(username: String, password: String): AuthResult {
        return login(Credentials(username, password))
    }

    public fun login(credentials: Credentials): AuthResult { /* ... */ }
}
```

Cadence:

1. **Minor release N.1** — add the new API; mark the old `@Deprecated(WARNING)`.
2. **Minor release N.2** — change the deprecation to `DeprecationLevel.ERROR`. Source that calls it no longer compiles, but already-compiled callers still link and run.
3. **Minor release N.3** — change it to `DeprecationLevel.HIDDEN`. Source can no longer see it; the method stays in the binary, so compiled callers keep working.
4. **Next major release (N+1.0)** — remove the old API.

This follows Kotlin's library guidance: warning, then error, then hidden across several minor releases, with removal only in a major release. Space the steps by time, not just release count, so consumers have a real migration window.

Document deprecations in release notes. Use IDE hints (`ReplaceWith`) so consumers get one-click migrations.

For widely-used APIs, ship a [structural search/replace template](https://www.jetbrains.com/help/idea/structural-search-and-replace.html) so consumers can migrate in seconds.

---

## Tracking SDK Adoption

If you publish an SDK and don't know who's on which version, you fly blind.

```kotlin
// :sdk:core/src/main/kotlin/.../SdkInitializer.kt
public object SdkInitializer {
    public fun initialize(context: Context, config: Config) {
        // Library BuildConfig has had no VERSION_NAME since AGP 4.1; define your own
        // buildConfigField (BuildConfig generation is off by default since AGP 8.0).
        reportSdkVersion(BuildConfig.SDK_VERSION, config.consumerAppId)
        // ...
    }
}
```

The reporting endpoint feeds a dashboard:

| Consumer app | SDK version | DAU on this version |
|---|---|---|
| Rider | 3.2.0 | 4.2M |
| Driver | 3.1.4 | 850k |
| Merchant | 2.8.0 | 110k |

Two questions the Platform lead now answers in seconds:

- "If we remove `AuthClient.login(username, password)` in 3.0, who breaks?" → Driver and Merchant.
- "Can we drop support for 2.x?" → Merchant is still on 2.x; coordinate with their team.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Two modules pull two OkHttp versions | No catalog, ad-hoc versions | `libs.versions.toml`; CI conflict check |
| Compose imports fail compatibility | No BOM, mixed Compose versions | Compose BOM |
| Consumer app breaks on SDK 1.2.1 PATCH | Accidental ABI break | `binary-compatibility-validator` |
| Engineers add deps without review | No policy | RFC for new top-level deps |
| Dependabot floods PR list | All updates trigger PRs | Renovate config; group + auto-merge patches |
| Production app shipped with a SNAPSHOT | No CI guard | Resolution strategy: fail on SNAPSHOT in release |
| Deprecation removed without warning | Skipped the WARNING→ERROR→HIDDEN cycle | Documented deprecation policy |
| Don't know which apps use SDK 1.x | No telemetry | Init-time version ping |

---

## Common Pitfalls

- **Dynamic versions (`1.+`, `latest.release`).** Non-deterministic builds. Yesterday's CI passed; today's fails because a transitive dep released a bad version. Pin always.
- **`force()` everywhere.** When you force a version of every dep, you bypass the resolver's ability to upgrade safely. Use sparingly.
- **`api` on internal SDK transitives.** Don't leak Retrofit out of your auth SDK; consumers can't upgrade Retrofit themselves. Use `implementation` and re-expose only the types you intend to.
- **No deprecation runway.** Cutting an API in a MINOR release breaks downstream apps unexpectedly. Go WARNING → ERROR → HIDDEN across minor releases, and remove only in a MAJOR release.
- **An undocumented BOM version scheme.** Date-based (`2024.06`, like the Compose BOM) signals cadence; SemVer-style (like the Firebase BoM) signals breaking removals. Either works if consumers know what a bump means.
- **No catalog policy.** Engineers add libraries individually; the catalog drifts. Escalate Android Lint's built-in `UseTomlInstead` check (it flags dependencies declared directly in build files when a version catalog exists) to an error.

---

## Probing Questions

1. Walk through a complete `libs.versions.toml` upgrade from Kotlin 2.3.x to 2.4.x. What can go wrong?
2. Why date-version a BOM (`2024.06`) instead of SemVer-version it?
3. The `binary-compatibility-validator` fails CI for a PR. Walk through how you'd evaluate whether to bump MAJOR.
4. A feature team forces a higher OkHttp version "for a security fix." How do you assess and respond?
5. Compose 1.5 → 1.6 breaks a consumer's snapshot tests. How do you decide what to do?
6. SNAPSHOT vs release conventions — why are they enforced?
7. A widely-used API needs to change. Walk through a 6-month deprecation plan.
8. Renovate opens 30 PRs/week. How do you keep up without spending all of Monday merging?

---

## Answer Key

1. **Walk through a complete `libs.versions.toml` upgrade from Kotlin 2.3.x to 2.4.x. What can go wrong?**
   Updating the version string in `libs.versions.toml` is easy, but it changes the compiler for all modules. Things that can go wrong: the KSP release no longer supports the new Kotlin version (check KSP's compatibility table), AGP's built-in Kotlin or other compiler plugins lag behind, new compiler warnings fail `allWarningsAsErrors` modules, transitive dependency conflicts (for example on `kotlin-stdlib`), and a one-time wave of build-cache misses because every Kotlin compile task's key changes. Since Kotlin 2.0 the Compose compiler ships with Kotlin, so there is no separate Compose Compiler version to align.
2. **Why date-version a BOM (`2024.06`) instead of SemVer-version it?**
   A BOM represents a snapshot of compatible library versions at a point in time across many different artifacts that evolve independently. Date versioning (the Compose BOM) sets a clear expectation of cadence and age. SemVer-style versioning (the Firebase BoM) is also used, with a major bump when the BOM drops or breaks artifacts. Either is defensible; the mistake is leaving consumers to guess what a bump means.
3. **The `binary-compatibility-validator` fails CI for a PR. Walk through how you'd evaluate whether to bump MAJOR.**
   Review the `.api` diff. If the change removes, renames, or modifies the signature of a `public` or `protected` member in a way that breaks existing consumers at compile or runtime, it requires a MAJOR bump. If it was accidental, revert the change.
4. **A feature team forces a higher OkHttp version "for a security fix." How do you assess and respond?**
   Audit the change: verify the security advisory, check for API breakages in the new version, and test the app. If valid, update the catalog version centrally so all modules benefit, and remove the feature team's `force()` to maintain a single source of truth.
5. **Compose 1.5 → 1.6 breaks a consumer's snapshot tests. How do you decide what to do?**
   Determine if the breakage is a genuine UI regression or just rendering engine tweaks (e.g., anti-aliasing changes). If it's expected rendering changes, coordinate a one-time mass update of golden images. If it's a regression, file a bug and block the upgrade.
6. **SNAPSHOT vs release conventions — why are they enforced?**
   Releases are immutable and guarantee reproducible builds. SNAPSHOTs are mutable, causing non-deterministic builds where CI might pass today and fail tomorrow without code changes. Enforcing release-only in production prevents shipping unstable artifacts.
7. **A widely-used API needs to change. Walk through a 6-month deprecation plan.**
   Month 1 (minor release): Introduce the new API, mark the old one with `@Deprecated(level = WARNING)` providing a `ReplaceWith` snippet. Month 3 (minor release): Elevate to `@Deprecated(level = ERROR)` so source that still calls it fails to compile and teams must migrate. Month 5 (minor release): Move to `HIDDEN`, which keeps the method in the binary for already-compiled callers. Month 6: Remove the old API completely in a MAJOR release.
8. **Renovate opens 30 PRs/week. How do you keep up without spending all of Monday merging?**
   Configure Renovate to auto-merge `PATCH` updates if CI passes. Group related updates (e.g., all AndroidX libraries) into single PRs. Require manual review only for `MINOR` and `MAJOR` updates.

## Further Reading

- [`build-graph-scaling.md`](build-graph-scaling.md) — `libs.versions.toml` is the foundation.
- [`sdk-distribution.md`](sdk-distribution.md) — how to publish SDKs you've versioned correctly.
- [`internal-developer-platforms.md`](internal-developer-platforms.md) — versioning as a platform service.
- [`../android/data-and-di/hilt-vs-koin-vs-manual-di.md`](../android/data-and-di/hilt-vs-koin-vs-manual-di.md) — how upgrade cadence differs across DI choices.
- [Gradle — Version Catalogs](https://docs.gradle.org/current/userguide/version_catalogs.html) — version catalogs official docs.
- [Gradle — Java Platform Plugin](https://docs.gradle.org/current/userguide/java_platform_plugin.html) — BOM publishing.
- [Kotlin — Binary compatibility validation in the Kotlin Gradle plugin](https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html) — built-in ABI guard (experimental).
- [Kotlin — binary-compatibility-validator](https://github.com/Kotlin/binary-compatibility-validator) — ABI guard plugin (maintenance mode).
- [Kotlin — Backward compatibility guidelines for library authors](https://kotlinlang.org/docs/api-guidelines-backward-compatibility.html) — default arguments, overloads and deprecation cycles.
- [Kotlin — Explicit API mode](https://kotlinlang.org/docs/whatsnew14.html#explicit-api-mode-for-library-authors) — official docs.
- [Renovate Bot](https://docs.renovatebot.com/) — config reference.
- [SemVer.org](https://semver.org/) — canonical definition.

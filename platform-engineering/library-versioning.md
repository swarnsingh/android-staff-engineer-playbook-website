# Platform Engineering: Library Versioning & Dependency Management

> A 200-module project with no versioning discipline is a runtime bomb. Two modules pull two versions of OkHttp; Gradle silently picks one; the other module's code path crashes in production on a device you can't reproduce. The Platform team's job is to make this class of bug structurally impossible.

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
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
```

The version catalog centralizes it:

```toml
# gradle/libs.versions.toml
[versions]
kotlin = "1.9.22"
agp = "8.3.1"
compose-bom = "2024.02.02"
retrofit = "2.9.0"
okhttp = "4.12.0"
hilt = "2.50"
room = "2.6.1"
coroutines = "1.7.3"

[libraries]
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
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
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

Versioning the BOM by calendar (`2024.06`, `2024.09`) makes the cadence visible. Every quarter, a new BOM; consumers upgrade at their own pace.

---

## Semantic Versioning for Internal SDKs

When your Platform team publishes SDKs to a private Maven repo and other Android apps in the company consume them, SemVer is the contract.

| Bump | Triggers | Examples |
|---|---|---|
| **PATCH** (`x.y.Z`) | Internal change only | Bug fix; refactor; perf improvement |
| **MINOR** (`x.Y.0`) | Backwards-compatible additions | New function, new optional parameter, new module |
| **MAJOR** (`X.0.0`) | Breaking change | Removed function, changed signature, changed default behavior |

The rule: **if a consumer's code that used to compile and run on version `X.Y.Z` no longer compiles or behaves differently on `X.Y.Z+1`, it's a MAJOR bump.**

### Enforce with binary-compatibility-validator

Manual SemVer policing fails at scale. Use [`binary-compatibility-validator`](https://github.com/Kotlin/binary-compatibility-validator) to snapshot the ABI and fail CI on accidental changes.

```kotlin
// :sdk:auth/build.gradle.kts
plugins {
    id("org.jetbrains.kotlinx.binary-compatibility-validator") version "0.14.0"
}
```

After the first build, a `:sdk:auth/api/auth.api` file is generated, listing every public class, function, and field. Subsequent builds compare against it. Any diff fails CI unless the engineer regenerates the dump (`./gradlew apiDump`) — which forces them to explicitly acknowledge the API change in the PR.

```
public final class com/yourorg/sdk/auth/AuthClient {
    public fun login(Ljava/lang/String;Ljava/lang/String;)V    ← old
    public fun login(Ljava/lang/String;)V                       ← new (param removed)
}
```

A reviewer sees the diff in the `.api` file and asks: "Did you mean to remove the password param? If so, this is a MAJOR bump."

### Explicit API Mode

Kotlin defaults class members to `public`. Engineers forget visibility modifiers; private helpers accidentally become public ABI.

```kotlin
// :sdk:auth/build.gradle.kts
kotlin {
    explicitApi()    // strict: every public API must be explicitly declared `public` or `internal`
}
```

Now the compiler refuses to build until every member has an explicit visibility. The SDK's public surface stays intentional.

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
            strictly("4.12.0")   // build fails if anyone forces a different version
        }
    }
}
```

Use `strictly` only when a specific version is load-bearing (e.g., security patch you must apply). Otherwise prefer the catalog default.

---

## Dependency Update Automation

A Platform team should not manually check for new versions. Automate it.

```yaml
# renovate.json
{
  "extends": ["config:base"],
  "labels": ["dependencies"],
  "schedule": ["after 1am on monday"],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "automerge": true,
      "automergeType": "branch"
    },
    {
      "matchPackagePatterns": ["^com.yourorg.sdk"],
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

Renovate (or Dependabot) scans `libs.versions.toml`, opens PRs for new releases, runs full CI, and merges patches automatically if green. Majors and minors land in a PR queue for the Platform team to review.

Gate dangerous bumps:

- **PATCH** — auto-merge on green CI.
- **MINOR** — Platform team reviewer required.
- **MAJOR** — RFC required; coordinated rollout.

Save dozens of engineer-hours per week.

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
configurations.all {
    resolutionStrategy.eachDependency {
        if (requested.version?.contains("SNAPSHOT") == true && isReleaseBuild) {
            throw GradleException("SNAPSHOT dependency in release: ${requested.module}")
        }
    }
}
```

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

1. **Release N.x** — add the new API; mark the old `@Deprecated(WARNING)`.
2. **Release N+1.x** — change the deprecation to `DeprecationLevel.ERROR`. Code still runs, but compilation warns hard.
3. **Release N+2 (MAJOR bump)** — remove the old API.

Document deprecations in release notes. Use IDE hints (`ReplaceWith`) so consumers get one-click migrations.

For widely-used APIs, ship a [structural search/replace template](https://www.jetbrains.com/help/idea/structural-search-and-replace.html) so consumers can migrate in seconds.

---

## Tracking SDK Adoption

If you publish an SDK and don't know who's on which version, you fly blind.

```kotlin
// :sdk:core/src/main/kotlin/.../SdkInitializer.kt
public object SdkInitializer {
    public fun initialize(context: Context, config: Config) {
        reportSdkVersion(BuildConfig.VERSION_NAME, config.consumerAppId)
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
| Deprecation removed without warning | Skipped the WARNING→ERROR cycle | Documented deprecation policy |
| Don't know which apps use SDK 1.x | No telemetry | Init-time version ping |

---

## Common Pitfalls

- **Dynamic versions (`1.+`, `latest.release`).** Non-deterministic builds. Yesterday's CI passed; today's fails because a transitive dep released a bad version. Pin always.
- **`force()` everywhere.** When you force a version of every dep, you bypass the resolver's ability to upgrade safely. Use sparingly.
- **`api` on internal SDK transitives.** Don't leak Retrofit out of your auth SDK; consumers can't upgrade Retrofit themselves. Use `implementation` and re-expose only the types you intend to.
- **No deprecation runway.** Cutting an API in a MINOR release breaks downstream apps unexpectedly. Always WARNING → ERROR → remove across at least two MAJOR cycles.
- **Versioning the BOM in semver (`1.2.3`).** Confuses consumers; the BOM is a snapshot of a moment, not an evolving API. Use date-based (`2024.06`).
- **No catalog policy.** Engineers add libraries individually; the catalog drifts. Lint rule: any direct version string in `build.gradle.kts` fails build.

---

## Probing Questions

1. Walk through a complete `libs.versions.toml` upgrade from Kotlin 1.9.10 to 1.9.22. What can go wrong?
2. Why date-version a BOM (`2024.06`) instead of SemVer-version it?
3. The `binary-compatibility-validator` fails CI for a PR. Walk through how you'd evaluate whether to bump MAJOR.
4. A feature team forces a higher OkHttp version "for a security fix." How do you assess and respond?
5. Compose 1.5 → 1.6 breaks a consumer's snapshot tests. How do you decide what to do?
6. SNAPSHOT vs release conventions — why are they enforced?
7. A widely-used API needs to change. Walk through a 6-month deprecation plan.
8. Renovate opens 30 PRs/week. How do you keep up without spending all of Monday merging?

---

## Further Reading

- [`build-graph-scaling.md`](build-graph-scaling.md) — `libs.versions.toml` is the foundation.
- [`sdk-distribution.md`](sdk-distribution.md) — how to publish SDKs you've versioned correctly.
- [`internal-developer-platforms.md`](internal-developer-platforms.md) — versioning as a platform service.
- [`../android/data-and-di/hilt-vs-koin-vs-manual-di.md`](../android/data-and-di/hilt-vs-koin-vs-manual-di.md) — how upgrade cadence differs across DI choices.
- [Gradle — Sharing dependency versions across projects](https://docs.gradle.org/current/userguide/platforms.html) — version catalogs official docs.
- [Gradle — Java Platform Plugin](https://docs.gradle.org/current/userguide/java_platform_plugin.html) — BOM publishing.
- [Kotlin — binary-compatibility-validator](https://github.com/Kotlin/binary-compatibility-validator) — ABI guard.
- [Kotlin — Explicit API mode](https://kotlinlang.org/docs/whatsnew14.html#explicit-api-mode-for-library-authors) — official docs.
- [Renovate Bot](https://docs.renovatebot.com/) — config reference.
- [SemVer.org](https://semver.org/) — canonical definition.

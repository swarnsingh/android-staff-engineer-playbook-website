# Platform Engineering: SDK Distribution & Publishing

> Shipping an Android SDK is publishing a public API to engineers you'll never meet. Every method signature is a contract; every default behavior is an assumption you can't take back. The Platform Engineer's job is not just the code — it's the distribution pipeline, the API surface discipline, the deprecation cadence, and the consumer integration story. A well-shipped SDK adds leverage across every app that consumes it; a badly-shipped one becomes the reason the next reorg happens.

---

## When You Have An SDK (Whether You Realize It Or Not)

You have an SDK the moment **another team consumes your code via Maven coordinates** — not when you stand up `sdk.yourcompany.com`.

Common scenarios:

- **Multi-app companies** — Rider, Driver, and Merchant apps all consume `:auth-sdk`, `:payments-sdk`, `:analytics-sdk`.
- **Public SDKs** — Firebase, Stripe, Branch, Segment publish to Maven Central or jCenter.
- **White-label / partner SDKs** — Your code embedded in a partner's app; you don't control their release cadence.
- **Cross-org internal libraries** — Your platform team's `:design-system` consumed by 20 product teams.

The discipline is the same in all four cases. The blast radius differs.

---

## The Artifact: AAR vs JAR vs Source

| Format | When to use | Trade-off |
|---|---|---|
| **AAR (Android Archive)** | Android-specific SDK with resources, AndroidManifest entries, or `assets/` | Standard for Android libraries. Includes resources + manifest merging. |
| **JAR** | Pure-Kotlin / pure-Java SDK with no Android dependencies | Smaller, faster to download. No resource support. Use for `:auth-tokens` (pure logic), not `:design-system` (resources). |
| **Source dependency / composite build** | Internal monorepo modules consumed by sibling modules | Re-compiled on every build — bad for cross-team SDKs. Good for tight feedback inside one repo. |
| **Klib (Kotlin Multiplatform)** | KMP SDK targeting iOS + Android from one codebase | Multiplatform; more complex publishing. Use when iOS team is also a consumer. |

For internal SDKs consumed by separate apps: **publish AARs**. Consuming source forces every consumer to rebuild your SDK on every clean build — destroys their build times for no benefit.

### Inside an AAR

```
auth-sdk-1.4.0.aar
├── AndroidManifest.xml         # merged into consumer's manifest
├── classes.jar                 # your compiled JVM bytecode
├── res/                        # Android resources
├── assets/                     # raw assets
├── libs/                       # transitive JARs (avoid; use POM)
├── jni/                        # native libs per ABI
├── proguard.txt                # consumer ProGuard / R8 rules
└── R.txt                       # public resource symbols
```

`proguard.txt` is critical — covered below.

---

## The Build: `maven-publish` Pipeline

Pure Kotlin/Java SDK:

```kotlin
// :sdk:auth-tokens/build.gradle.kts
plugins {
    `java-library`
    `maven-publish`
    kotlin("jvm")
    id("org.jetbrains.kotlinx.binary-compatibility-validator")
}

kotlin {
    explicitApi()
    jvmToolchain(17)
}

publishing {
    publications {
        create<MavenPublication>("maven") {
            groupId = "com.yourorg.sdk"
            artifactId = "auth-tokens"
            version = project.version.toString()
            from(components["java"])

            pom {
                name = "Auth Tokens"
                description = "JWT validation and refresh."
                url = "https://github.com/yourorg/auth-tokens"
                licenses {
                    license {
                        name = "Apache-2.0"
                        url = "https://www.apache.org/licenses/LICENSE-2.0"
                    }
                }
                scm {
                    connection = "scm:git:git://github.com/yourorg/auth-tokens.git"
                    url = "https://github.com/yourorg/auth-tokens"
                }
            }
        }
    }
}
```

Android library (AAR):

```kotlin
// :sdk:auth/build.gradle.kts
plugins {
    id("com.android.library")
    kotlin("android")
    `maven-publish`
    id("org.jetbrains.kotlinx.binary-compatibility-validator")
}

android {
    namespace = "com.yourorg.sdk.auth"
    compileSdk = 34
    defaultConfig {
        minSdk = 24
        consumerProguardFiles("consumer-rules.pro")
    }
    publishing {
        singleVariant("release") {
            withSourcesJar()
            withJavadocJar()
        }
    }
}

kotlin { explicitApi() }

afterEvaluate {
    publishing {
        publications {
            create<MavenPublication>("release") {
                from(components["release"])
                groupId = "com.yourorg.sdk"
                artifactId = "auth"
                version = project.version.toString()
                pom { /* ... same as above ... */ }
            }
        }
        repositories {
            maven {
                name = "Artifactory"
                url = uri(
                    if (version.toString().endsWith("SNAPSHOT"))
                        "https://artifactory.yourorg.internal/android-snapshots"
                    else
                        "https://artifactory.yourorg.internal/android-releases"
                )
                credentials {
                    username = providers.environmentVariable("ARTIFACTORY_USER").get()
                    password = providers.environmentVariable("ARTIFACTORY_PASSWORD").get()
                }
            }
        }
    }
}
```

Publish locally to test:

```bash
./gradlew :sdk:auth:publishReleasePublicationToMavenLocal
```

Then in a sample consumer app:

```kotlin
// consumer settings.gradle.kts
dependencyResolutionManagement {
    repositories {
        mavenLocal()                // pick up your local publish
        google()
        mavenCentral()
    }
}
```

This local round-trip is the fastest way to catch publishing bugs before pushing to Artifactory.

---

## API Surface Management: `explicitApi` + `internal`

The default Kotlin visibility is `public`. Every public class, method, field is a binding contract — once shipped in version `1.0`, you cannot change it without a `2.0` major bump.

```kotlin
// :sdk:auth/build.gradle.kts
kotlin { explicitApi() }    // 'strict' is the default for explicitApi()
```

Now the compiler refuses to build until every member has an explicit visibility:

```kotlin
public class AuthClient(
    private val transport: Transport,    // OK: explicit
    val config: Config,                  // ERROR: needs `public` or `internal`
) {
    public fun login(creds: Credentials): AuthResult { /* ... */ }

    internal fun debugDump(): String { /* visible inside SDK, not to consumers */ }

    private fun rotateKeys() { /* ... */ }
}
```

Discipline:

- **`public`** — only the small set of classes consumers should call. The SDK's contract.
- **`internal`** — implementation classes shared *across modules within the SDK* but invisible to consumers.
- **`private`** — single-class implementation detail.

A mature SDK is shaped like an hourglass: a wide internal implementation, a narrow public Facade. The narrower the public surface, the cheaper future evolution is.

### Binary Compatibility Validator

```kotlin
plugins {
    id("org.jetbrains.kotlinx.binary-compatibility-validator") version "0.14.0"
}
```

First build dumps `:sdk:auth/api/auth.api`. Every subsequent change to public ABI fails CI unless the developer runs `./gradlew apiDump` and commits the diff. The diff goes to PR review:

```diff
 public final class com/yourorg/sdk/auth/AuthClient {
-    public fun login (Ljava/lang/String;Ljava/lang/String;)Lcom/yourorg/sdk/auth/AuthResult;
+    public fun login (Lcom/yourorg/sdk/auth/Credentials;)Lcom/yourorg/sdk/auth/AuthResult;
 }
```

Reviewer's job: confirm the major-version bump. Without this guard, SemVer is wishful thinking.

---

## Consumer ProGuard / R8 Rules

When the consumer app runs R8 in release mode, it shrinks, obfuscates, and optimizes their code — including your SDK. If your SDK relies on reflection (Moshi/Gson, JSON parsing, dependency injection), R8 will silently strip the classes it can't see being used, and your SDK crashes at runtime in production only.

Ship `consumer-rules.pro` *inside* the AAR:

```pro
# :sdk:auth/consumer-rules.pro

# Keep public API classes
-keep public class com.yourorg.sdk.auth.AuthClient { public *; }
-keep public class com.yourorg.sdk.auth.AuthResult { *; }
-keep public class com.yourorg.sdk.auth.Credentials { *; }

# Moshi: JSON adapters generated at compile time
-keep,allowobfuscation,allowshrinking @com.squareup.moshi.JsonClass class * { *; }
-keep class **JsonAdapter { <init>(...); }

# Coroutines: keep the suspend marker
-keepclassmembers class kotlinx.coroutines.android.AndroidDispatcherFactory { *; }

# Don't warn on optional Kotlin reflect
-dontwarn kotlin.reflect.jvm.internal.**
```

```kotlin
android {
    defaultConfig {
        consumerProguardFiles("consumer-rules.pro")
    }
}
```

`consumerProguardFiles` (not `proguardFiles`) injects the rules into every consumer's R8 run automatically. The consumer doesn't need to know about them.

Verify by enabling R8 in a sample app and checking `app/build/outputs/mapping/release/missing_rules.txt`.

---

## `api` vs `implementation` in the SDK's POM

```kotlin
dependencies {
    implementation("com.squareup.okhttp3:okhttp:4.12.0")   // hidden from consumer
    api("com.squareup.moshi:moshi:1.15.0")                  // exposed; consumer can use Moshi types
}
```

When you publish, Gradle writes a `.pom` file:

```xml
<dependencies>
    <dependency>
        <groupId>com.squareup.okhttp3</groupId>
        <artifactId>okhttp</artifactId>
        <version>4.12.0</version>
        <scope>runtime</scope>            <!-- implementation → runtime -->
    </dependency>
    <dependency>
        <groupId>com.squareup.moshi</groupId>
        <artifactId>moshi</artifactId>
        <version>1.15.0</version>
        <scope>compile</scope>            <!-- api → compile -->
    </dependency>
</dependencies>
```

**Rules:**

- Use `implementation` for **internal** dependencies. They appear at runtime so your SDK works, but consumers can't call them.
- Use `api` only when your SDK's **public types reference** the dependency's types. If your `login()` method returns a `Moshi.JsonAdapter`, you must `api(moshi)` so the consumer can compile.

If you `api` everything, you force version constraints on the consumer that may conflict with their own dependencies. Minimize `api`; **never `api` a third-party HTTP client.**

---

## Fat AARs vs Transitive Dependencies

The temptation: "let me bundle OkHttp inside the AAR so the consumer doesn't need to declare it."

The result: **`DuplicateClassException`**. The consumer already has OkHttp in their build (every Android app does); now they have two copies; the build fails.

Don't fat-AAR. Let the POM declare your transitives:

```kotlin
dependencies {
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
```

The consumer's Gradle sees `okhttp` in your POM, resolves it once at the version both your SDK and they agreed on, and the build works.

### Exception: relocated/shadowed deps

If your SDK genuinely cannot share a transitive (e.g., you've forked a library, or the version skew with the consumer is unfixable), use `com.github.johnrengelman.shadow` to relocate the package:

```kotlin
plugins {
    id("com.github.johnrengelman.shadow")
}

tasks.shadowJar {
    relocate("okhttp3", "com.yourorg.sdk.shaded.okhttp3")
}
```

Now the SDK uses `com.yourorg.sdk.shaded.okhttp3.OkHttpClient` — invisible to consumers. Use very sparingly; doubles the size of the artifact and you maintain a shaded copy forever.

---

## Sample Integration App

Every SDK must ship a **sample app** in the same repo:

```
sdk-repo/
  :sdk:auth/                  # the SDK
  :sample/                    # the sample app — integrates the SDK like a real consumer
  :integration-tests/         # full E2E flow tests
```

The sample app:

- Uses the SDK via the **published Maven coordinates** (locally or from `mavenLocal()`), not a `project(":sdk:auth")` dependency. This catches POM bugs.
- Runs in CI on every commit.
- Demonstrates the documented usage pattern.

Without a sample app, you ship breakage to consumers and learn about it from their Slack messages.

---

## GitHub Actions Release Workflow

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*.*.*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17' }

      - name: Set version from tag
        run: echo "ORG_GRADLE_PROJECT_version=${GITHUB_REF_NAME#v}" >> $GITHUB_ENV

      - name: Validate API
        run: ./gradlew :sdk:auth:apiCheck

      - name: Run all tests
        run: ./gradlew :sdk:auth:test :sample:assembleRelease

      - name: Publish to Artifactory
        env:
          ARTIFACTORY_USER: ${{ secrets.ARTIFACTORY_USER }}
          ARTIFACTORY_PASSWORD: ${{ secrets.ARTIFACTORY_PASSWORD }}
        run: ./gradlew :sdk:auth:publish

      - name: Generate Dokka docs
        run: ./gradlew :sdk:auth:dokkaHtml

      - name: Publish docs to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./sdk/auth/build/dokka/html

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          name: ${{ github.ref_name }}
          body_path: CHANGELOG.md
          files: sdk/auth/build/outputs/aar/*.aar
```

Pipeline guarantees:

- Tag-driven (`v1.4.0`) — no accidental publishes.
- ABI snapshot must match what's in the repo before publishing.
- Sample app must build before publishing.
- Dokka docs auto-published.

---

## Documentation: Dokka + Examples

API reference alone is insufficient. Ship:

1. **Dokka HTML** — auto-generated from KDoc; hosted at `docs.sdk.yourorg.com/auth/1.4.0/`.
2. **Quick-start guide** (`README.md`) — three-line copy-paste integration:
   ```kotlin
   AuthSdk.initialize(this, AuthConfig(apiKey = BuildConfig.AUTH_KEY))
   val result = AuthSdk.client.login(Credentials("user", "pass"))
   ```
3. **Migration guides** for each MAJOR bump (`MIGRATION-v2.md`).
4. **Sample app** — runnable, current.
5. **Changelog** — what changed, every release.

Bad SDK docs cost consumer engineering hours that scale linearly with adoption. Spend the time.

---

## SDK Versioning & Adoption Telemetry

See [`library-versioning.md`](library-versioning.md) for SemVer policy. SDK-specific concerns:

- Publish a stable SemVer (`1.4.0`) and a `1.4.0-SNAPSHOT` channel for early adopters.
- Add **init-time version reporting** so you know who's on what:
  ```kotlin
  public object AuthSdk {
      public fun initialize(context: Context, config: AuthConfig) {
          reportVersion(BuildConfig.SDK_VERSION, config.consumerAppId, context.packageName)
          // ...
      }
  }
  ```
- Dashboard: SDK version × consumer app × DAU. Now "can we drop 1.x?" is a data-driven decision.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Consumer crashes only in release build | Missing `consumer-rules.pro` for reflection | Add R8 keep rules; ship inside AAR |
| `DuplicateClassException` on integration | Fat AAR or `api` of a popular lib | Use `implementation`; don't bundle transitives |
| Consumer Moshi types don't compile | `implementation(moshi)` instead of `api` | Use `api` only when types appear on SDK's public surface |
| ABI broke on a PATCH release | No binary-compatibility-validator | Add the plugin; gate CI on `apiCheck` |
| Sample app passes; consumer fails | Sample uses `project(":sdk")` not Maven coordinates | Sample must consume via `mavenLocal()` |
| Multiple SDK versions installed across consumer apps | No BOM | Publish an SDK BOM (see `library-versioning.md`) |
| Mystery NoSuchMethodError on Android 8 | `minSdk` mismatch between SDK and consumer | Document `minSdk`; assert at init time |
| Released `1.4.0` but consumers can't find it | Artifactory ACLs / repo not declared | Verify in a clean sample app via `mavenLocal()` first |
| Public API leaks `internal` types | No `explicitApi` | Enable `kotlin { explicitApi() }` |
| SDK pulls in 14 MB of transitive deps | Heavy deps not isolated | Audit; relocate if needed; replace heavy deps |

---

## SDK Size: A First-Class Metric

Consumer engineers will ask: "How much will this add to my APK?"

Measure and publish:

```bash
./gradlew :sdk:auth:assembleRelease
# Then run APK Analyzer on the AAR + a tiny sample app diff
```

Targets for an Android SDK:

| SDK type | Target compressed size |
|---|---|
| Pure-logic SDK | < 100 KB |
| Network + logic SDK | < 300 KB |
| UI + media SDK | < 1 MB |
| ML / video SDK | "as small as possible" + explicit doc on impact |

Crash these thresholds and consumers will resist adoption. Use R8 effectively, avoid heavy transitives, audit periodically.

---

## Common Pitfalls

- **Treating the SDK like internal code.** A typo'd method name is a 2-month deprecation cycle, not a quick rename. Review every public-API change like a published contract.
- **No ProGuard rules shipped.** Works in debug, crashes in release. Always ship `consumer-rules.pro` and exercise R8 in your CI.
- **Heavy transitives.** Pulling Apache HttpClient, Gson, and Guava into an "auth SDK" wastes 4 MB of consumer APK. Audit and replace with lighter equivalents.
- **No sample app.** First sign you can't see how your SDK feels to consumers. The sample doubles as integration test + onboarding doc.
- **Single-channel publishing.** No snapshot channel = no way to try a fix before tagging a release. Publish snapshots from `main`.
- **No version telemetry.** You won't know which versions are live and can't make data-driven sunset decisions.
- **Manual publishing from a laptop.** One engineer holding the signing key is a SEV-2 waiting to happen. CI-driven, tag-driven, reproducible.
- **Skipping Dokka docs.** Forces every consumer to read your source. Multiplies onboarding cost.

---

## Probing Questions

1. Walk through every step from a `git push` of a tag to the consumer app pulling in the new AAR. Where can it go wrong?
2. Your SDK works in debug, crashes with `NoSuchMethodException` only in release builds. Walk through the first 30 minutes of investigation.
3. Why is `consumer-rules.pro` shipped inside the AAR instead of letting the consumer manage R8 rules?
4. When does `api(dep)` make sense vs `implementation(dep)`? Give an example of each.
5. A consumer team complains the SDK adds 3 MB to their APK. Walk through your audit.
6. Walk through your deprecation plan for removing a widely-used public method.
7. Your SDK depends on OkHttp 4.12; the consumer app uses OkHttp 4.9. What happens? How would you protect against the worst case?
8. Why is shipping a sample app non-negotiable for an SDK team?

---

## Further Reading

- [`library-versioning.md`](library-versioning.md) — SemVer + BOM + deprecation policy.
- [`build-graph-scaling.md`](build-graph-scaling.md) — keeping SDK builds fast.
- [`internal-developer-platforms.md`](internal-developer-platforms.md) — SDKs as platform deliverables.
- [`design-systems-architecture.md`](design-systems-architecture.md) — UI SDK case study.
- [`../android/performance/app-size-and-r8.md`](../android/performance/app-size-and-r8.md) — R8 mechanics consumers rely on.
- [Android — Create an Android Library](https://developer.android.com/studio/projects/android-library) — official AAR reference.
- [Gradle — `maven-publish` plugin](https://docs.gradle.org/current/userguide/publishing_maven.html) — publishing reference.
- [Kotlin — binary-compatibility-validator](https://github.com/Kotlin/binary-compatibility-validator) — ABI guard.
- [Dokka](https://kotlinlang.org/docs/dokka-introduction.html) — Kotlin API docs.
- [Square's `okhttp` repo](https://github.com/square/okhttp) — reference Android SDK structure and release workflow.

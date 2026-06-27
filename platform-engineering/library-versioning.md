# Platform Engineering: Library Versioning and Dependency Management

## The Theory
In a monolithic application, you manage dependencies in a single `build.gradle` file. In a massive modularized application (50+ modules) or an ecosystem of discrete internal libraries (SDKs) shared across multiple apps (e.g., Rider App vs Driver App), managing versions becomes a chaotic web of conflicts. 
If Module A uses `Retrofit 2.9.0` and Module B uses `Retrofit 2.6.0`, Gradle will quietly force a resolution (usually upgrading to 2.9.0). If 2.9.0 contains a breaking API change, Module B crashes at runtime.

A Staff Engineer establishes a system to guarantee transitive dependency alignment and predictable upgrades across the entire organization.

## Staff-Level Application in Mobile

### 1. The Version Catalog (libs.versions.toml)
Hardcoding dependency strings (`implementation "com.squareup.retrofit2:retrofit:2.9.0"`) across 50 different `build.gradle` files is impossible to maintain. When you want to upgrade Retrofit, you have to run a global Find-and-Replace and hope you don't miss one.
-   **The Solution:** The Platform team mandates the use of Gradle Version Catalogs (`libs.versions.toml`).
-   This centralized file acts as the single source of truth for every external library and version number used in the company.
-   **The Benefit:** To upgrade Retrofit globally, the Platform engineer changes *one* line in the `.toml` file. The entire project automatically synchronizes to the new version on the next sync.

### 2. The Bill of Materials (BOM)
A Version Catalog helps you align your own modules. A **BOM (Bill of Materials)** helps you align massive third-party ecosystems.
-   **The Problem:** Firebase and Jetpack Compose consist of dozens of individual libraries (`firebase-auth`, `firebase-firestore`, `ui`, `material`, `foundation`). If you manually specify the version for each one, you risk picking incompatible versions (e.g., mixing Compose Foundation 1.4 with Compose Material 1.5).
-   **The Solution:** You import the BOM. The BOM defines a verified, compatible matrix of versions for all related libraries.
```groovy
// You specify the version ONLY on the BOM
implementation platform('com.google.firebase:firebase-bom:32.2.0')
// You DO NOT specify versions here. The BOM dictates them.
implementation 'com.google.firebase:firebase-analytics'
implementation 'com.google.firebase:firebase-auth'
```

### 3. Semantic Versioning (SemVer) for Internal SDKs
If your Platform team builds internal SDKs (e.g., `com.company:auth-sdk`) that are published to a private Maven repository (Artifactory/Nexus) and consumed by multiple separate Android apps within the company, you must strictly enforce **Semantic Versioning (MAJOR.MINOR.PATCH)**.
-   **MAJOR (Incompatible API changes):** You deleted a public function or changed its signature. Apps using the SDK *will* fail to compile if they upgrade.
-   **MINOR (Backwards-compatible functionality):** You added a new feature. Existing code will compile fine.
-   **PATCH (Backwards-compatible bug fixes):** Internal implementation fix. No API surface changes.
-   **The Staff Rule:** The CI pipeline should enforce SemVer. If a developer opens a PR against the `auth-sdk` that changes a public interface but they only bumped the PATCH version, a static analysis tool (like Metalava) should automatically fail the CI build and force them to bump the MAJOR version.

### 4. Dependency Update Automation
Platform engineers shouldn't spend their week manually checking if OkHttp released a new version.
-   **The Automation:** Integrate **Dependabot** or **Renovate**.
-   These bots scan your `libs.versions.toml` file daily. When a new version of a library is released on Maven Central, the bot automatically opens a Pull Request in your repository bumping the version.
-   The PR automatically runs your full suite of unit and UI tests. If the tests pass, the Platform engineer can merge the upgrade with absolute confidence and zero manual effort.

## Common Pitfalls
-   **The "Latest" Tag:** Never use dynamic versions (`implementation "com.library:1.2.+"` or `latest.release`). This makes your builds non-deterministic. If the library author publishes a broken version, your CI pipeline will silently pull it down and break your app, and you won't know why. Always pin to exact, immutable versions.
-   **Dependency Hoarding:** Just because a library exists doesn't mean you should add it. Every new library increases APK size, slows down build times, and introduces a potential security supply-chain vulnerability. A Platform Team should act as a gatekeeper, requiring an RFC to approve the addition of any major new third-party dependency to the Version Catalog.

# Platform Engineering: SDK Distribution & Publishing

## The Theory
When your company has multiple distinct mobile applications (e.g., a Rider App and a Driver App, or a main Banking App and a specialized Trading App), you cannot copy-paste the core authentication or networking logic between them. You must build internal SDKs.
A Platform Engineer is responsible for architecting not just the code of these SDKs, but the **distribution pipeline** that allows product teams to reliably consume them.

## Staff-Level Application in Mobile

### 1. The Artifact: AAR vs Source Modules
How do you share the `CoreAuth` code with the Rider and Driver apps?
-   **The Junior Approach (Git Submodules / Monorepo Sources):** You force both apps to physically include the source code of the `CoreAuth` module in their Gradle builds. This inflates compile times for the product apps because they have to recompile the SDK from scratch every time.
-   **The Staff Approach (Pre-compiled AARs):** The Platform team builds the `CoreAuth` module into a compiled `.aar` (Android Archive) file. This artifact contains the compiled Dalvik bytecode (`classes.jar`), Android resources, and the `AndroidManifest.xml`. Product teams consume the binary, meaning Gradle never wastes time recompiling it.

### 2. The Distribution Channel: Private Maven Repositories
You cannot just email a `.aar` file to the product teams. You must distribute it via a dependency management system.
-   **The Infrastructure:** The Platform team provisions a private Maven repository (e.g., JFrog Artifactory, AWS CodeArtifact, or GitHub Packages).
-   **The Publishing Pipeline:** When a Platform engineer merges a PR into the `CoreAuth` repository, the CI/CD pipeline triggers. It compiles the code, runs the tests, generates the `.aar`, and uses the `maven-publish` Gradle plugin to upload the artifact to the private Artifactory with a specific Semantic Version (e.g., `1.2.0`).
-   **The Consumption:** The product teams simply add the private repository URL to their `settings.gradle` and declare the dependency in their app: `implementation "com.company.sdk:coreauth:1.2.0"`.

### 3. API Surface Management (Public vs Internal)
When you publish an SDK, everything marked `public` in Kotlin becomes a binding contract. If a product team uses a `public` function, and you change its signature in the next release, you break their app.
-   **The Problem:** By default in Kotlin, if you don't specify a visibility modifier, it is `public`.
-   **The Staff Solution (Explicit API Mode):** The Platform team configures the SDK's `build.gradle` to enforce **Explicit API Mode**.
```kotlin
kotlin {
    explicitApi()
}
```
This compiler flag fails the build if a developer forgets to explicitly declare a visibility modifier (`public`, `internal`, or `private`) on a class or function.
-   **The `internal` Modifier:** Platform engineers use `internal` extensively. It allows classes to be shared *within* the SDK module for architecture, but prevents product teams from accessing them when consuming the `.aar`. Only the specific Facade classes intended for consumer use are marked `public`.

### 4. Transitive Dependency Hell (The POM File)
If your `CoreAuth` SDK uses `Retrofit 2.9.0` internally, what happens when a product team consumes your SDK? Do they also get Retrofit?
-   **The POM (Project Object Model):** When you publish an `.aar` to Maven, Gradle also publishes a `.pom` XML file alongside it. This file lists all the dependencies your SDK requires.
-   **`api` vs `implementation`:**
    -   If your SDK uses `implementation "com.squareup.retrofit2:retrofit:2.9.0"`, Retrofit is added to the POM as a *runtime* dependency. The consumer app gets Retrofit at runtime to prevent crashes, but cannot call Retrofit APIs directly.
    -   If your SDK uses `api "com.squareup.retrofit2:retrofit:2.9.0"`, Retrofit is exposed to the consumer. The consumer can write Retrofit code themselves.
    -   **Platform Rule:** SDKs should almost *never* use `api` for external third-party libraries. You do not want to force a specific version of a third-party library onto your consumers and pollute their classpath. Hide your third-party dependencies using `implementation`.

## Common Pitfalls
-   **Fat AARs:** An SDK team decides to physically bundle Retrofit and OkHttp *inside* their `.aar` file to make integration "easier". This is a catastrophe. If the consumer app also uses Retrofit, the app will fail to compile with a `DuplicateClassException`. Never bundle transitive dependencies; rely on the POM file to manage them gracefully.
-   **Lack of Documentation:** A published SDK is useless without documentation. The CI publishing pipeline must automatically generate Dokka (Kotlin's Javadoc equivalent) API references and publish them to a centralized internal documentation portal (e.g., Backstage) every time a new version is released.

# Framework validation

`android/` is a pinned Android Gradle project containing excerpts extracted by `website/scripts/generate_android_validation.py`. `fixtures.json` identifies their source and hashes. Imports, enclosing composable context and explicitly recorded application-owned helpers supply context; Android, Room, Hilt, Compose, lifecycle and Ktor come from real dependencies. The instrumentation examples are compiled, not reported as device-executed.

The JVM/Robolectric suite tests Room transaction commit/rollback, Compose custom snapshot isolation/read observation, failed/cancelled uploads and concurrent batch arrivals, virtual-time deadlines, finite Turbine completion, gated Loading observation, STARTED lifecycle collection, generated JVM overloads, controlled Compose text input, semantic merge boundaries, intermediate animation frames, Ktor error mapping, retry safety and cancellation. The two template ViewModel tests are included in the 22-test result.

`gradle-probe/` extracts the convention-plugin classes and checks real Gradle settings configuration and explicit task registration. It never installs a hook or accesses the example cache server.

Use the installed `gradle-run` skill's compact wrapper for every Gradle command. From `android/`, the nested tasks are `./gradlew :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin` and `./gradlew -p ../gradle-probe verifyDocumentationPlugins`. Keep the nonempty verification question and bounded result with each run. Generate fixtures from the repository root with its Python virtual environment before validation.

This is documentation regression coverage, not an application demonstrating every chapter. No device performance, peripheral, DRM-license or Apple-runtime result is implied. Full Xcode is not installed on this host; the Apple boundary claims are checked against official Kotlin/Apple/project contracts rather than presented as simulator or archive tests.

plugins {
  alias(libs.plugins.ksp)
  alias(libs.plugins.hilt)
  alias(libs.plugins.android.application)
  alias(libs.plugins.compose.compiler)
  alias(libs.plugins.kotlin.serialization)
}

android {
  namespace = "dev.playbook.validation"
  compileSdk = 36
  defaultConfig {
    applicationId = "dev.playbook.validation"
    minSdk = 24
    targetSdk = 36
    versionCode = 1
    versionName = "1.0"
  }

  buildTypes {
    release {
      isMinifyEnabled = false
      proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
    }
  }
  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
  }
  testOptions { unitTests.isIncludeAndroidResources = true }
  buildFeatures {
    compose = true
    aidl = false
    buildConfig = false
    shaders = false
  }

  packaging {
    resources {
      excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
  }
}

kotlin {
  jvmToolchain(17)
}

dependencies {
  val composeBom = platform(libs.androidx.compose.bom)
  implementation(composeBom)
  androidTestImplementation(composeBom)

  // Core Android dependencies
  implementation(libs.androidx.core.ktx)
  implementation(libs.androidx.lifecycle.runtime.ktx)
  implementation(libs.androidx.activity.compose)

  // Arch Components
  implementation(libs.androidx.lifecycle.runtime.compose)
  implementation(libs.androidx.lifecycle.viewmodel.compose)

  // Compose
  implementation(libs.androidx.compose.ui)
  implementation(libs.androidx.compose.ui.tooling.preview)
  implementation(libs.androidx.compose.material3)
  // Tooling
  debugImplementation(libs.androidx.compose.ui.tooling)
  // Instrumented tests
  androidTestImplementation(libs.androidx.compose.ui.test.junit4)
  debugImplementation(libs.androidx.compose.ui.test.manifest)

  // Local tests: jUnit, coroutines, Android runner
  testImplementation(libs.junit)
  testImplementation(libs.kotlinx.coroutines.test)

  // Instrumented tests: jUnit rules and runners
  androidTestImplementation(libs.androidx.test.core)
  androidTestImplementation(libs.androidx.test.ext.junit)
  androidTestImplementation(libs.androidx.test.runner)
  androidTestImplementation(libs.androidx.test.espresso.core)

  // Navigation
  implementation(libs.androidx.navigation3.ui)
  implementation(libs.androidx.navigation3.runtime)
  implementation(libs.androidx.lifecycle.viewmodel.navigation3)
}

dependencies {
  implementation("androidx.lifecycle:lifecycle-service:2.10.0")
  implementation("androidx.room:room-runtime:2.8.5")
  implementation("androidx.room:room-ktx:2.8.5")
  ksp("androidx.room:room-compiler:2.8.5")
  implementation("com.google.dagger:hilt-android:2.60.1")
  ksp("com.google.dagger:hilt-compiler:2.60.1")
  implementation("androidx.work:work-runtime-ktx:2.11.2")
  implementation("androidx.paging:paging-runtime-ktx:3.4.2")
  implementation("androidx.datastore:datastore-preferences:1.2.1")
  testImplementation("org.robolectric:robolectric:4.17")
  testImplementation("androidx.test:core:1.7.0")
}
ksp { arg("room.schemaLocation", "$projectDir/schemas") }

dependencies { implementation("org.jetbrains.kotlinx:kotlinx-collections-immutable:0.5.1") }

dependencies {
 implementation("androidx.tracing:tracing:1.3.0")
 testImplementation("app.cash.turbine:turbine:1.2.1")
 testImplementation(libs.androidx.compose.ui.test.junit4)
 testImplementation(libs.androidx.test.ext.junit)
}

dependencies {
 implementation("io.ktor:ktor-client-core:3.6.0")
 implementation("io.ktor:ktor-client-content-negotiation:3.6.0")
 implementation("io.ktor:ktor-client-logging:3.6.0")
 implementation("io.ktor:ktor-serialization-kotlinx-json:3.6.0")
 implementation("co.touchlab:kermit:2.0.8")
 testImplementation("io.ktor:ktor-client-mock:3.6.0")
}

dependencies {
 androidTestImplementation("com.google.dagger:hilt-android-testing:2.60.1")
 kspAndroidTest("com.google.dagger:hilt-compiler:2.60.1")
 androidTestImplementation("androidx.compose.ui:ui-test-junit4-accessibility")
}

plugins { `kotlin-dsl` }
repositories { gradlePluginPortal(); mavenCentral() }
gradlePlugin { plugins {
 register("cacheFixture") { id="playbook.validation.cache";implementationClass="BuildCacheConventionPlugin" }
 register("hooksFixture") { id="playbook.validation.hooks";implementationClass="GitHooksConventionPlugin" }
} }

import org.gradle.caching.http.HttpBuildCache
pluginManagement { includeBuild("build-logic") }
plugins { id("playbook.validation.cache") }
rootProject.name="documentation-plugin-validation"
check(buildCache.local?.isEnabled==true)
check((buildCache.remote as HttpBuildCache).url.toString()=="https://cache.yourorg.internal")

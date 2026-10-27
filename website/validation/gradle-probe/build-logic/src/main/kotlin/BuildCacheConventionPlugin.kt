import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.initialization.Settings
import org.gradle.caching.http.HttpBuildCache
import org.gradle.kotlin.dsl.*
// A settings plugin, applied from settings.gradle.kts.
class BuildCacheConventionPlugin : Plugin<Settings> {
    override fun apply(settings: Settings) = with(settings) {
        buildCache {
            local { isEnabled = true }
            remote<HttpBuildCache> {
                url = java.net.URI.create("https://cache.yourorg.internal")
                isPush = System.getenv("CI") == "true"
            }
        }
    }
}


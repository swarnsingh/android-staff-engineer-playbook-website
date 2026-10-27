import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.initialization.Settings
import org.gradle.caching.http.HttpBuildCache
import org.gradle.kotlin.dsl.*
class GitHooksConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        if (target != target.rootProject) return
        target.tasks.register("installGitHooks") {
            group = "setup"
            description = "Explicitly install the repository-managed pre-commit hook"
            doLast {
                // Resolve .git/hooks for worktrees/custom hooksPath in the real installer.
                val destination = target.layout.projectDirectory.file(".git/hooks/pre-commit").asFile
                require(destination.parentFile.isDirectory) { "Use the repository installer for worktrees" }
                target.file("config/hooks/pre-commit").copyTo(destination, overwrite = true)
                check(destination.setExecutable(true))
            }
        }
    }
}


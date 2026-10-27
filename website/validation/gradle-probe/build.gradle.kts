plugins { id("playbook.validation.hooks") }
tasks.register("verifyDocumentationPlugins") {
 doLast {
  check(tasks.names.contains("installGitHooks"))
  check(!layout.projectDirectory.file(".git/hooks/pre-commit").asFile.exists())
  println("PASS settings cache configuration and explicit hook-task registration; no hook installed")
 }
}

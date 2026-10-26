# Website source, checks and publication

The website has one source repository: [swarnsingh/android-staff-engineer-playbook-website](https://github.com/swarnsingh/android-staff-engineer-playbook-website). Read [rulebook section 19](../content-rulebook.md#19-separate-website-repository-and-private-previews) before changing hosting. All LLMs and developers use the same repository, branch history, build tools and workflow.

## Current hosting decision

The repository is private. On 2026-10-26, GitHub reported `has_pages: false`; no GitHub Pages site is configured. Earlier Claude artifacts and the ChatGPT-hosted Kotlin reader are historical snapshots. Do not update them or create a replacement agent-specific hosting project.

[GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) can build directly from this repository. However, [private Pages access requires an organization using GitHub Enterprise Cloud](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site). This is a personal repository. Keeping its source private does not make a Pages website private.

The owner confirmed on 2026-10-26 that both source and preview must remain private. The repository workflow therefore publishes a downloadable private Actions build artifact, with no Pages deployment job and no public deployment switch. A live private website remains unconfigured. It requires an owner-approved access-controlled hosting runtime connected to this repository; do not create another source repository or agent-hosted artifact to fill this gap.

## Reproduce the build locally

Run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 website/tools/prepare_browser_audit.py website/.cache/browser-qa
python3 -m http.server 4179 --bind 127.0.0.1 --directory website/.cache/browser-qa
```

Open `/audit.html` and start the full sweep. Also run `/motion-fixture.html` and `/binder-audit.html`. Every result must pass. The instrumented directory is disposable and must never be published. Build output is `website/dist/`; it is generated, not another source repository.

For a project-path build such as GitHub Pages:

```sh
SITE_BASE=/android-staff-engineer-playbook-website/ .venv/bin/python website/scripts/build.py
```

The browser-audit preparation command expects the root-path local build. Rebuild without `SITE_BASE` before local browser auditing.

## Repository workflow

[`.github/workflows/website.yml`](../.github/workflows/website.yml) builds the website on website changes in pull requests, `main`, and `codex/android-completion`, or on manual dispatch. It checks JavaScript syntax, renders Mermaid diagrams, verifies source hashes and original-content preservation, then packages the relative-link reader as a private Actions artifact named `website-private-preview-<commit>`. `build-info.json` identifies the repository, commit and Actions run. Download access follows the private repository's permissions; retention is 14 days and another run can recreate the artifact.

The artifact includes instructions for running a local server after download. It is a verified build package, not a live hosted website. Record the source commit, Actions run URL and artifact outcome in the current handover. The workflow has no Pages deployment job, no source push to another hosting repository, and no publishing credentials.

When the owner chooses a private runtime, add its deployment job to this workflow using the already-built output and repository secrets or supported identity federation. Verify returned access restrictions and deployed commit before reporting a live private URL. Preserve this repository as the only source and keep the same commit provenance.

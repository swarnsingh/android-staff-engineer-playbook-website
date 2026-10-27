# Website source, checks and publication

The website has one source repository: [swarnsingh/android-staff-engineer-playbook-website](https://github.com/swarnsingh/android-staff-engineer-playbook-website). Read [rulebook section 19](../content-rulebook.md#19-separate-website-repository-and-publication). All models and developers use this repository, its branch history, build tools and workflow.

## Public GitHub Pages

The owner approved public source and a public website on 27 October 2026, superseding the earlier private-source/private-preview decision. The original playbook repository remains private and unchanged. Historical Claude and ChatGPT previews are no longer publication targets.

Live URL: [Engineering Playbook](https://swarnsingh.github.io/android-staff-engineer-playbook-website/). Both learning paths and the design-system gallery belong to this deployment. No login is required to read the public website. The repository and rendered content are public.

[`.github/workflows/website.yml`](../.github/workflows/website.yml) checks browser-script syntax, renders Mermaid diagrams, verifies source hashes and original-content preservation, and builds with `SITE_BASE=/android-staff-engineer-playbook-website/`. Pushes to `codex/android-completion` and `main` publish via GitHub Pages; PR runs build only. The current publication branch is `codex/android-completion` while PR #1 remains available for review. Configure Pages to use GitHub Actions, with its deployment environment permitting this branch. Future branch changes must update this guide, workflow and source-reference links together.

The build writes `build-info.json` with repository, commit and Actions run. Deployment uses the built Pages artifact and GitHub OIDC, without a second source repository or stored publishing token. A successful build alone is not publication: verify the deployment job, live page responses, assets, both learning paths and deployed commit. Never deliver a ZIP or localhost address as the published website.

## Reproduce and audit

Run from this repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 website/tools/prepare_browser_audit.py website/.cache/browser-qa
python3 -m http.server 4179 --bind 127.0.0.1 --directory website/.cache/browser-qa
```

Open `/audit.html` and start the 125-page sweep. Also run `/motion-fixture.html`, `/binder-audit.html` and `/refinement-audit.html`. Record raw failures and focused rechecks when a fix is needed. The landing page and gallery require separate responsive and route checks. The instrumented directory is disposable and must never be deployed. Build output is `website/dist/`, intentionally untracked.

For the publication build:

```sh
SITE_BASE=/android-staff-engineer-playbook-website/ .venv/bin/python website/scripts/build.py
```

The browser-audit preparation command expects a root-path local build. Rebuild without `SITE_BASE` before preparing local browser audits. Complete the checks before pushing a publishing branch. Original-chapter corrections remain separate owner decisions.

## Troubleshoot publication

If deployment fails, inspect the failed job before rerunning. Check that Pages uses the workflow build type and that the `github-pages` environment allows the publication branch. If lessons load without styles, verify the project prefix in generated asset URLs. Compare the live provenance commit with the intended branch head before blaming browser caching. Keep failed runs and corrected audit evidence traceable in the current review report.

# External link repair

## Scope

The weekly `check-external-links` job failed on 2026-11-09 (run 42611570160) with 13 URLs returning 404. This change repairs the dead public links and stops checking links to the private source repository. It changes no original chapter text, and no shared CSS, JS, template or renderer.

- **Private source repository.** `scripts/check_external_links.py` now skips `https://github.com/swarnsingh/android-staff-engineer-playbook` and its subpaths, and prints how many links it skipped. These links return 404 to anonymous requests because the repository is private, but they still work for the owner. The public `-website` repository is still checked. Unit tests cover both cases.
- **Layout Inspector.** `developer.android.com/develop/ui/compose/tooling/layout-inspector` no longer exists. The CSG06 correction now cites `developer.android.com/develop/ui/compose/tooling/debug#recomposition-counts`, the "Get recomposition counts" section of the official Compose debugging page.
- **OkHttp and Retrofit.** Square's documentation sites moved from `square.github.io` to `lysine.dev`, as shown by each GitHub repository's homepage and the `site_url` in OkHttp's `mkdocs.yml`. The OkHttp HTTPS and Interceptors links in two review notes now point to `lysine.dev/okhttp/features/`. The Retrofit citation in the Coupling vs Cohesion lesson and its correction now point to `lysine.dev/retrofit/`. The link checker does not scan `.blend` files, so that Retrofit link was not in the failed run.
- **Transactional outbox.** AWS has withdrawn its Prescriptive Guidance "Cloud design patterns" guide; every page now returns 404. Citations in 4 blend files, 8 Engineering Fundamentals corrections, 2 figure models and the matching review records now point to `github.com/aws-samples/transactional-outbox-pattern`. That is AWS's own sample, and the withdrawn page linked to it. Its README states the dual-write problem, the risk of duplicate messages and the need for idempotent consumers, which are the claims these citations support. Source PR #82 made the same change in the source chapters (merged as `2277b5f`). The website's Engineering Fundamentals chapter copies predate those reference lists and contain no AWS link, so `source-snapshot.json` is unchanged.

## Validation

The evidence was produced on `main` at `37383c8`, which includes Leadership, plus this change.

- `check_external_links.py`: 1,086 unique external resources checked, 9 private-repository links skipped, no 404/410 responses. The 2 remaining warnings are O'Reilly 403s, which the checker treats as non-failures.
- The build preserved 35,345 original units in order across 295 pages, and all 22 tampering fixtures were detected. The figure checker passed 268 original models and 197 teaching models. The 1440 px frame check passed 279 pages, 339 figures and 5,142 labels.
- Local CI passed the website tests, docs tests, 74 Computer Science Java examples, the docs gate and 15 browser-script syntax checks.
- All six browser audits passed. The browser suite covered 295 pages, 8,900 code readability cases and 1,732 Q&A pairs. The other suites recorded Binder 560, Motion 13, Refinement 69, UX 278 and Q&A tampering 31.

## Limits

Replacement URLs were checked live on 2026-11-10. Bot-gated sites that return 403 or 429 are reported as warnings and not checked further. The source chapters still link to `square.github.io` for KSP, Coupling vs Cohesion and the memory model. That needs a separate source-repository fix.

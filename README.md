# Android Engineering Playbook — Reader Website

This repository develops the reader website separately from the [original playbook](https://github.com/swarnsingh/android-staff-engineer-playbook). Since repository separation, website work makes no further changes to the original repository. Its earlier website branch remains as historical work; its main branch and original chapters are unchanged.

The current website renders the Kotlin learning path and all 22 Kotlin chapters, plus the Android learning path and all 101 Android chapters across nine phases. Original chapter Markdown is a read-only snapshot; explanations, examples, tables and questions remain in order. The website adds labelled stories, visuals, step-through animations, reading preferences and responsive navigation. Technical corrections are separate proposals and require owner approval before application.

Read the [content rulebook](content-rulebook.md), especially sections 16–19, and the [website build/handover guide](website/README.md). Source provenance and Kotlin and Android checksums are recorded in `source-snapshot.json`.

Website changes and publication use this repository only. Read the [deployment guide](website/DEPLOYMENT.md) for the shared build and audit commands, workflow and public GitHub Pages publication. Earlier Claude and ChatGPT previews are historical snapshots; they are not the current website.

GitHub shows the preserved Markdown and the website source. `website/dist/` is generated during the build and is intentionally not committed.

Live website: [Android & Kotlin Engineering Playbook](https://swarnsingh.github.io/android-staff-engineer-playbook-website/). [Android](https://swarnsingh.github.io/android-staff-engineer-playbook-website/android/), [Kotlin](https://swarnsingh.github.io/android-staff-engineer-playbook-website/kotlin/) and [design-system gallery](https://swarnsingh.github.io/android-staff-engineer-playbook-website/design-system/) use the same build.

## Local preview

```sh
python3 -m venv .venv
.venv/bin/pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 -m http.server 4177 --bind 127.0.0.1 --directory website/dist
```

Run from this new website checkout, choose an available port, and open the localhost address on that computer. Confirm the server serves this checkout’s `website/dist`. Remote access must use the single deployment path in the deployment guide.

## Branch history

- `main`: last published Kotlin preview source (`d9cae81`).
- `codex/android-completion`: current website and GitHub Pages publication branch: Android, Kotlin, 17 temporal scenes, 119 illustrated state figures and static decision diagrams. See the [refinement report](website/reviews/AIRBRIDGE-REFINEMENT-2026-10-27.md) for validation and publication status.
- `codex/reader-website-fixes`: the current fix and repository-separation snapshot.
- `codex/reader-website`: preserved original website draft history.
- `claude/reader-website-kotlin`: preserved teaching-layer and review history through `8a77e22`.

The complete original chapter tree is retained for source references and future migration; Kotlin and all nine Android phases currently render as website lessons. Do not rewrite chapter Markdown to make a presentation change. Follow the rulebook for source imports, approvals and publication.

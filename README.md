# Android Engineering Playbook — Reader Website

This private repository develops the reader website separately from the [original playbook](https://github.com/swarnsingh/android-staff-engineer-playbook). The original repository is not modified by website work.

The current website renders the Kotlin learning path and all 22 Kotlin chapters. Original chapter Markdown is a read-only snapshot; explanations, examples, tables and questions remain in order. The website adds labelled stories, visuals, step-through animations, reading preferences and responsive navigation. Technical corrections are separate proposals and require owner approval before application.

Read the [content rulebook](content-rulebook.md), especially sections 16–19, and the [website build/handover guide](website/README.md). Source provenance and Kotlin checksums are recorded in `source-snapshot.json`.

## Local preview

```sh
python3 -m venv .venv
.venv/bin/pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 -m http.server 4174 --bind 127.0.0.1 --directory website/dist
```

Open the printed localhost address on that computer. Remote phone access uses the separately deployed owner-private preview.

## Branch history

- `main`: current website development and verified preview source.
- `codex/reader-website-fixes`: the current fix and repository-separation snapshot.
- `codex/reader-website`: preserved original website draft history.
- `claude/reader-website-kotlin`: preserved teaching-layer and review history through `8a77e22`.

The complete original chapter tree is retained for source references and future migration; only Kotlin currently renders as website lessons. Do not rewrite chapter Markdown to make a presentation change. Follow the rulebook for source imports, approvals and private publishing.

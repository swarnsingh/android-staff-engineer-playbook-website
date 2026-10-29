---
name: publish-website
description: Build, audit, gate and publish the reader website after changing shared reader files, diagram models or lesson blends. Use when asked to publish, deploy, verify or refresh evidence for the website.
---

Follow the publishing steps in AGENTS.md exactly; they print short summaries.

1. Run `python3 website/tools/dev.py build`, then `figures`, then `ci`. On any failure, open only the log path it prints, fix, and repeat.
2. Run `python3 website/tools/dev.py audit <topic>-<YYYY-MM-DD>` in the background (about 5 minutes) and read only its summary.
3. Write `website/reviews/<topic>-<YYYY-MM-DD>/REPORT.md` covering scope, the summary results and remaining limits.
4. Run `python3 website/tools/dev.py gate <topic>-<YYYY-MM-DD>`.
5. Commit without AI attribution. Push to `main` only if the owner asked to publish; otherwise open a pull request. Confirm the "Website review and GitHub Pages" workflow succeeds.

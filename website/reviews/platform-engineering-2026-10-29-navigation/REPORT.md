# Platform Engineering navigation cache review — 29 October 2026

## Reader problem and cause

The Platform Engineering path and its six chapter pages had been generated and deployed, but a reader reported that five chapter entries still opened their GitHub Markdown sources. The site builds a navigation catalog containing a `rendered` flag for each chapter. The browser uses that flag to choose a reader route; if the flag is false, it deliberately sends the chapter to GitHub. Inspection of the deployed catalog showed all six Platform Engineering entries marked `rendered: true`, and direct requests to their reader routes returned pages. This pointed to an earlier catalog remaining in the reader's browser cache.

The page loaded `nav-data.js` with a version query string calculated from styles, JavaScript, and design-system tokens. That calculation did not include the generated navigation catalog. Registering a new tree changed the catalog but left the version query string unchanged. A browser that had cached the previous catalog could therefore keep the old `rendered: false` values even while showing the newly published path page. The local browser audit used a fresh QA copy, so it did not exercise that cache transition. This report records the gap in the original publication claim as well as the verification of the correction.

## Change and scope

The build now generates the catalog before calculating the asset version and includes the exact generated `nav-data.js` bytes in that hash. A change to the chapter list, reading order, phase, title, or rendered status produces a new script URL. The new Platform Engineering path page references `nav-data.js?v=5054d3989c`, whereas the deployed page before this change referenced `v=0c54866f92`. The change is in the shared build script because cache versioning is a shared reader behavior. No original chapter, topic content, FigureMap model, CSS file, or other topic's source file changed.

## Checks and browser evidence

A fresh local build preserved 19,767 original units across 159 pages with zero preservation problems. The generated catalog lists six Platform Engineering chapters, all marked rendered, and all six corresponding reader `index.html` files exist. A headless browser loaded the Platform Engineering learning path from a local server, inspected the actual sidebar anchors, and found six local reader URLs with no GitHub destinations. Following the Design Systems entry opened its reader page and displayed the expected chapter heading.

`dev.py figures` passed 89 models; `dev.py frames` checked 154 pages, 89 figures, 118 relationship maps and 1,892 labels with no problems. `dev.py ci` passed 15 website unit tests, 31 documentation unit tests, documentation validation and ten browser-script syntax checks. The fresh `dev.py audit platform-engineering-2026-10-29-navigation` completed all six audit groups. Browser checks passed 159 of 159 pages, 5,624 of 5,624 code checks and 1,194 of 1,194 question-answer pairs. Binder passed 560 of 560, motion 13 of 13, refinement 69 of 69, UX 278 of 278 and tampering fixtures 31 of 31. The JSON files in this folder contain the detailed results.

## Publication limit

These checks establish the new build output and local browser behavior. After merging, the main-branch GitHub Pages workflow must complete successfully, and the live page must be checked for the new script URL and local sidebar destinations. Until those live checks pass, this correction is not considered published.

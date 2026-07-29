#!/usr/bin/env python3
"""Check external links without making normal pull-request CI network-dependent.

Run from the repository root. The scheduled GitHub Actions job fails only for
definitive missing-resource responses (404 and 410). Authentication, bot
protection, rate limits, server errors, and transport failures are printed as
warnings because they do not prove that a reader-facing link is broken.
"""

from __future__ import annotations

import concurrent.futures
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_SECONDS = 20
WORKERS = 16
MISSING = {404, 410}
USER_AGENT = "android-staff-engineer-playbook-link-check/1.0"
LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")


def markdown_files():
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
        for name in files:
            if name.endswith(".md"):
                yield os.path.join(root, name)


def collect_links() -> dict[str, list[str]]:
    links: dict[str, list[str]] = {}
    for path in markdown_files():
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        for match in LINK_RE.finditer(text):
            raw = match.group(1)
            parsed = urllib.parse.urlsplit(raw)
            normalized = urllib.parse.urlunsplit(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.query, "")
            )
            links.setdefault(normalized, []).append(path)
    return links


def check(url: str) -> tuple[str, int | None, str | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return url, response.status, None
    except urllib.error.HTTPError as error:
        return url, error.code, str(error)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return url, None, str(error)


def main() -> int:
    links = collect_links()
    missing: list[tuple[str, int, list[str]]] = []
    warnings: list[tuple[str, int | None, str, list[str]]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for url, status, error in pool.map(check, sorted(links)):
            if status in MISSING:
                missing.append((url, status, links[url]))
            elif error:
                warnings.append((url, status, error, links[url]))

    print(f"Checked {len(links)} unique external resources")
    for url, status, paths in missing:
        print(f"MISSING {status}: {url}")
        for path in sorted(set(paths)):
            print(f"    {path}")
    for url, status, error, paths in warnings:
        label = str(status) if status is not None else "transport"
        print(f"WARN {label}: {url} ({error})")
        for path in sorted(set(paths)):
            print(f"    {path}")

    if missing:
        print(f"\nFailed: {len(missing)} external resources returned 404/410")
        return 1
    print(f"\nPassed: no definitive missing resources; {len(warnings)} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())

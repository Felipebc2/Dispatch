---
id: wayback-archived-site-recovery
category: OSINT
tags: [osint, wayback, archive, web-archive, cdx, deleted-page, snapshot, archive-today, history, robots-txt]
tools: []
manuals: []
title: "OSINT: recover deleted or changed web content from archives (Wayback CDX, archive.today)"
difficulty: easy
created: 2026-11-13
updated: 2026-11-13
related: [domain-recon-certificates-dns, username-pivot-cross-platform]
toolsets: [osint/archives]
---

## How to recognize this pattern

- "The page was taken down", "the post was deleted", "the site changed last year".
- A URL returns 404 now, or the current site looks clean while the prompt insists something was there.
- Need the old version of robots.txt, a JS file, a profile bio or a pastebin.

## Method

1. **List everything ever archived** under the domain with the CDX API (one request, JSON):
   ```bash
   curl -s "https://web.archive.org/cdx/search/cdx?url=<domain>/*&output=json&fl=timestamp,original,statuscode&collapse=urlkey&limit=500"
   ```
   Look for paths that no longer exist: `/backup`, `.txt`, `.zip`, admin pages, old JS.
2. **Fetch a snapshot raw** (no Wayback toolbar): add `id_` after the timestamp:
   `https://web.archive.org/web/<timestamp>id_/<url>`.
3. **Diff versions**: `waybackpack <url> -d out --uniques-only`, then `diff` consecutive files.
4. **Not in Wayback?** Try `https://archive.ph/<url>` (good for social posts) and CachedView.
5. Profiles/posts: archive URLs of the persona found in `username-pivot-cross-platform`.

## Gotchas

- `collapse=urlkey` hides duplicates; drop it to see every capture date of one URL.
- Wayback can lag months: absence there doesn't mean the page never existed.
- archive.today rate-limits and shows captchas; space out requests.
- Snapshot timestamps are UTC.

## Cross-reference

- `domain-recon-certificates-dns`: subdomains found there are worth a CDX query each.

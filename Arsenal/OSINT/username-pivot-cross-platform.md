---
id: username-pivot-cross-platform
category: OSINT
tags: [osint, username, alias, handle, pivot, sherlock, whatsmyname, socmint, account-enumeration]
tools: []
manuals: []
title: "OSINT: pivot a username/handle across platforms to reach the flag"
difficulty: easy
created: 2026-11-13
updated: 2026-11-13
related: [email-pivot-account-discovery, social-media-scraping-playwright]
toolsets: [osint/username, osint/socmint-platforms, osint/archives]
---

## How to recognize this pattern

- The challenge gives a nickname, handle, gamer tag, or "the suspect calls themselves X".
- A persona is spread over several sites: the flag (or the next clue) lives on a profile the prompt
  never names (GitHub, Reddit, Pastebin, a forum, a Gist, a Steam profile).
- The same string appears as an email local-part, a repo owner or a commit author.

## Method

1. Enumerate accounts with the toolset, not by guessing sites:
   ```bash
   python3 scripts/arsenal_search.py --toolset osint/username --free
   sherlock <handle>            # if installed; prints only profiles that exist
   ```
   Without Sherlock, WhatsMyName's `wmn-data.json` gives each site's URL pattern and the string that
   proves the account exists: fetch the pattern with the handle and check that string.
2. Drop false positives: a 200 on a catch-all page is not an account. Open each hit and confirm the
   bio, avatar, creation date or cross-links match the persona.
3. Read every confirmed profile for pivots: bio links, linked accounts, location, timezone, avatar.
   Platform helpers: `--toolset osint/socmint-platforms`.
4. CTF personas are usually recent: sort by creation date and check the profile's oldest posts.
5. Deleted or edited content: run the profile URL through `--toolset osint/archives` (Wayback,
   archive.today).
6. GitHub-specific: `https://api.github.com/users/<handle>/events/public` exposes commit emails;
   repos, gists and old commits often hold the flag.

## Gotchas

- Case and separators vary across sites (`john_doe`, `johndoe`, `john.doe`): try the variants.
- Common handles collide with real people: only trust a hit tied to another clue from the challenge.
- Do not interact with real accounts (follow, DM, comment). Collection only.
- Validate the flag against the configured flag format before declaring success.

## Cross-reference

- `email-pivot-account-discovery`: when a profile leaks an email.
- `social-media-scraping-playwright`: when a profile needs scrolling or login to collect posts.

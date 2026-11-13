---
id: email-pivot-account-discovery
category: OSINT
tags: [osint, email, gmail, ghunt, epieos, email-headers, eml, pivot, google-account]
tools: []
manuals: []
title: "OSINT: pivot from an email address (or .eml headers) to the person and their accounts"
difficulty: medium
created: 2026-11-13
updated: 2026-11-13
related: [username-pivot-cross-platform, domain-recon-certificates-dns]
toolsets: [osint/email, osint/leaks, osint/username]
---

## How to recognize this pattern

- The prompt gives an email address, a `.eml`/`.msg` file, or a screenshot of a mail.
- "Who sent this?", "where was the sender?", "find the owner of this Gmail".
- A company domain with a target employee name: you must derive the address first.

## Method

1. **Headers first** (when there is an `.eml`): read `Received:` bottom-up; the first external hop
   gives the sender IP. `X-Originating-IP`, `Message-ID` domain and `X-Mailer` also leak.
   Geolocate the IP with `--toolset osint/domain-infra` (IP2Location, IPtoASN).
2. **Local-part as username**: `john.doe1987@gmail.com` → run `john.doe1987` through
   `username-pivot-cross-platform`.
3. **Google account**: `ghunt email <addr>` (or Epieos) gives the Gaia ID, display name, avatar and
   public Google Maps reviews. Reviews carry places and dates: classic CTF geolocation.
4. **Registered services**: Epieos / check-if-email-exists tell which sites know the address.
5. **Company address unknown**: get the pattern with Email Format or Hunter, generate candidates
   with Email Permutator+, then verify with check-if-email-exists.
6. **Breach presence** (lookup only): `--toolset osint/leaks`. Never download or use leaked creds.

```bash
python3 scripts/arsenal_search.py --tools "email headers sender ip" --top 3
```

## Gotchas

- Gmail ignores dots and `+tags`: `j.o.h.n+ctf@gmail.com` is `john@gmail.com`.
- Webmail (Gmail, Outlook) usually hides the client IP: the first external `Received` is the
  provider's server. Then pivot on other headers instead.
- SMTP verification gives false positives on catch-all domains.

## Cross-reference

- `username-pivot-cross-platform`: for the local-part.
- `domain-recon-certificates-dns`: for the sender's domain.
- `image-geolocation-exif`: for photos found on Maps reviews.

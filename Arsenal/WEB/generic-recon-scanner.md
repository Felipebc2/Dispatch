---
id: generic-recon-scanner
category: WEB
tags: [recon, enumeracao, user-agent, paths-comuns, requests, flag-scan]
tools: []
manuals: []
title: "Generic initial recon — common paths + User-Agent variation"
difficulty: easy
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- A web challenge with no obvious vector in the prompt — the flag might be at a predictable path
  (`/flag`, `/robots.txt`, `/.git/HEAD`), or the app's behavior changes with the `User-Agent`/header
  you send (e.g. a screen shows "your User-Agent is X" and the flag depends on sending a specific UA).
- Worth running as the **first step of any new web challenge**, before investing in something more
  specific (SQLi, JWT, etc.) — it's reconnaissance, not exploitation.

## Method

**Prefer `gobuster`/`ffuf` for pure path enumeration** — they're faster and more battle-tested than an
ad-hoc Python script. This entry covers the complementary case: when the behavior changes by **header**
(not just by path), which `gobuster` alone doesn't cover.

```bash
# Path enumeration (prefer this over a custom script)
gobuster dir -u http://<target>/ -w /usr/share/wordlists/dirb/common.txt -t 30

# "Obvious" paths to also check by hand (low cost, high payoff sometimes)
for p in / /flag /flag.txt /api /robots.txt /sitemap.xml /.git/HEAD; do
    echo "== $p =="; curl -s -o /dev/null -w "%{http_code}\n" "http://<target>$p"
done
```

### User-Agent variation (when the app's behavior depends on the header)

```python
import re, requests

FLAG_RE = re.compile(rb"<FLAG_PREFIX>\{[^}]+\}")  # adjust to the CTF's real flag format

UA_LIST = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "curl/7.68.0",
    "python-requests/2.31.0",
    "Mozilla/5.0",
]

def probe(url, uas=UA_LIST):
    for ua in uas:
        r = requests.get(url, headers={"User-Agent": ua}, timeout=6)
        m = FLAG_RE.search(r.content)
        if m:
            print(f"FLAG with UA='{ua}':", m.group(0).decode())
            return m.group(0)
    return None
```

### Extract and scan images referenced on the page (in case the flag is embedded in an image)

```python
from urllib.parse import urljoin
import re

def extract_image_urls(base_url, html: str):
    urls = set(re.findall(r'src=["\']([^"\']+)["\']', html, re.I))
    return [u if u.startswith("http") else urljoin(base_url, u.lstrip("/")) for u in urls]

# download each one and run FLAG_RE.search(content_bytes) — if it hits, great;
# if not, treat it as a candidate for Arsenal/CRYPTO/ (stego) instead of insisting here.
```

## Gotchas

- Don't reinvent `gobuster`/`ffuf`/`dirsearch` for pure path enumeration — only use a custom script
  when the vector depends on a **header/conditional behavior**, not just a path.
- Testing **one UA value "almost like" the expected one isn't enough** — if the challenge wants an
  exact UA (seen in a screenshot, say), reproduce that string literally.
- If nothing in the common paths or the UA variation turns anything up, don't spend more than 2-3
  minutes on this recon — it's a sign the real vector is something else (SQLi, JWT, SSRF — see other
  Arsenal entries).

## Related / Cross-reference

If an image downloaded during recon looks like it hides data, move on to `Manuals/LSB-Stego/` or
`zsteg`/`binwalk` instead of trying to extract it with a text regex.

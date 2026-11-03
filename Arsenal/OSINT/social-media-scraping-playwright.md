---
id: social-media-scraping-playwright
category: OSINT
tags: [playwright, scraping, instagram, social-media, comments, browser-automation]
tools: []
manuals: []
title: "Automated collection of posts/comments on a social network via Playwright"
difficulty: medium
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- An OSINT challenge asks you to find information/a flag hidden in a post, comment, or profile on a
  social network (Instagram, etc.) — usually in a specific post or scattered across the comments of
  several posts on a profile.
- Signal that automating is worth it: the profile has **many posts/comments** (searching by hand would
  take too long) and/or the flag is gated behind a keyword (`SEARCH_WORD`) that appears in only 1 of many
  comments.
- Requires manual login (most social networks block unauthenticated comment scraping) — it's not 100%
  automatable without human intervention at login.

## Method

General flow with Playwright (manual login + programmatic collection afterward):

1. **Install dependencies:**
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

2. **Open a persistent session and pause for manual login** — avoids logging in every run:
   ```python
   from playwright.sync_api import sync_playwright
   from pathlib import Path

   USER_DATA_DIR = str(Path.home() / ".cache" / "osint_pw_profile")

   with sync_playwright() as p:
       context = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False)
       page = context.new_page()
       page.goto("<url_do_perfil_ou_post>")
       input("Log in manually in the open window, then press ENTER here...")
       # from here on, `page`/`context` are already authenticated
   ```

3. **Collect post links via incremental scroll** (profiles load content on demand):
   ```python
   def collect_post_links(page, want_max, max_scrolls=120, link_selector='a[href*="/p/"], a[href*="/reel/"]'):
       links, seen, last_height = [], set(), 0
       for _ in range(max_scrolls):
           for a in page.locator(link_selector).all():
               href = a.get_attribute("href") or ""
               if href.startswith("/"):
                   href = page.url.split("/", 3)[0] + "//" + page.url.split("/", 3)[2] + href
               if href not in seen:
                   seen.add(href); links.append(href)
           if len(links) >= want_max:
               break
           page.keyboard.press("End")
           page.wait_for_timeout(300)
           h = page.evaluate("() => document.documentElement.scrollHeight")
           if h == last_height:
               break
           last_height = h
       return links[:want_max]
   ```

4. **Expand each post's comments** — most networks hide comments behind "see more"/"load more"
   buttons; click repeatedly until exhausted or a limit is hit:
   ```python
   import re

   def expand_all_comments(page, load_more_patterns, max_clicks=50, delay_ms=600):
       for _ in range(max_clicks):
           clicked = False
           for pattern in load_more_patterns:
               btn = page.get_by_role("button", name=re.compile(pattern, re.I)).first
               if btn.count() > 0:
                   try:
                       btn.click(timeout=3000)
                       clicked = True
                       page.wait_for_timeout(delay_ms)
                       break
                   except Exception:
                       continue
           if not clicked:
               break
   ```

5. **Search the collected comments for the keyword/flag** and save each processed post to its own
   JSON file (makes it easy to resume if the script dies midway):
   ```python
   import json
   from pathlib import Path

   def save_and_search(post_url, comments: list[str], search_word: str, out_dir=Path("comments_json")):
       out_dir.mkdir(exist_ok=True)
       name = post_url.rstrip("/").split("/")[-1]
       (out_dir / f"{name}.json").write_text(json.dumps(comments, ensure_ascii=False, indent=2))
       hits = [c for c in comments if search_word.lower() in c.lower()]
       return hits
   ```

6. **Mark already-processed posts** in a simple file (`processed_urls.txt`) — avoids reprocessing
   everything if the script is interrupted and restarted.

## Gotchas

- `HEADLESS=False` is more stable to avoid bot detection / blocks — run with a visible interface, not in
  the background headless.
- Social networks change their UI/selectors often — the `get_by_role`/`get_by_text` regexes
  (`ver mais`, `load more`, `view all comments`, `mostrar mais`) need to be checked/adjusted against the
  current UI before you trust them.
- Manual login is mandatory — don't try to automate credentials (avoids account blocks and is
  unnecessary: `USER_DATA_DIR` persists the session across runs).
- Aggressive scraping (many fast scrolls/clicks) can trigger rate limits/captcha — use generous delays
  (`wait_for_timeout`), especially if the profile has many posts.
- This is **data collection**, not the solution itself — once you find the flag/clue in the comments,
  validate it against the current CTF's flag format before submitting.

## Related / Cross-reference

No cross-reference with `Manuals/` — if the CTF's OSINT is based on a different network/platform, the UI
selectors change but the flow (manual login → scroll → expand → keyword search) stays the same.

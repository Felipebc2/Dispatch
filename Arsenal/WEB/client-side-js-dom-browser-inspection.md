---
id: client-side-js-dom-browser-inspection
category: WEB
tags: [client-side, javascript, dom, spa, localstorage, sessionstorage, indexeddb, cookie, devtools, browser-automation, network-inspection, websocket, dom-xss, obfuscation, headless, chrome-devtools, mcp]
tools: [chrome-devtools]
manuals: ["Manuals/chrome-devtools/3. Contexto para Claude.md"]
title: "Web client-side — flag/logic in the browser (JS/DOM/storage/network) inspected via the chrome-devtools MCP"
difficulty: easy
created: 2026-10-07
updated: 2026-10-07
related: []
---

## How to recognize this pattern

- `curl` on the page returns an **HTML skeleton + JS bundle** (React/Vue/Angular SPA) — the real
  content only appears after the JS runs. What matters isn't in the raw HTML.
- The prompt/hint points at the front end: "inspect", "the secret is right in front of you",
  obfuscated/minified JS, a canvas, an in-browser game, a multi-step flow that only advances by
  clicking.
- The flag/token probably lives in: a global JS variable, `localStorage`/`sessionStorage`, IndexedDB,
  a cookie, a comment in the rendered DOM, or in an API response that only the front end triggers.
- DOM-XSS: there's a client-side sink (`innerHTML`, `eval`, `document.write`) fed by your input.

## Method

The inspection target lives in the browser → use the **chrome-devtools** MCP (navigate + run JS in the
page context), not `curl`. See `Manuals/chrome-devtools/3. Contexto para Claude.md` for the tool list
and full recipes.

1. `navigate_page` to the challenge URL; `take_snapshot` to map the actionable DOM.
2. `evaluate_script` to read the client state — this cracks most cases right away:
   ```js
   () => ({ local:{...localStorage}, session:{...sessionStorage}, cookie:document.cookie })
   () => Object.keys(window).filter(k=>/flag|token|key|secret|admin/i.test(k)).map(k=>[k,window[k]])
   () => (document.documentElement.innerHTML.match(/flag\{[^}]+\}/gi) || [])
   ```
3. If you need interaction (login/modal/multi-step): `click`/`fill` driven by the snapshot uids, then
   re-evaluate the state.
4. If the front end calls an API/websocket: trigger the action and use `list_network_requests` +
   `get_network_request` to extract the endpoint/headers/token/body — from there the attack can
   continue server-side with `curl`/a solver.
5. Validate the flag against the CTF's configured flag format before declaring success.

## Gotchas

- **Don't use the browser if the attack is server-side** (SQLi/SSRF/LFI via `curl`): the automation
  round-trip costs more contest time. chrome-devtools is only for what `curl` can't see.
- `--isolated` (the current setup) starts **logged out** — a challenge that needs an authenticated
  session requires reconfiguring the MCP (`-u http://127.0.0.1:9222` against a Chrome with
  remote-debugging, or `--userDataDir`).
- "Obfuscated" JS rarely needs to be de-obfuscated by hand: run it in the page context and read the
  result/state instead of reconstructing the logic.
- Some challenges detect headless — if the behavior changes, run with a UI (without `--headless`).

## Related / Cross-reference

- `Manuals/chrome-devtools/3. Contexto para Claude.md` — MCP tools + `evaluate_script` recipes.

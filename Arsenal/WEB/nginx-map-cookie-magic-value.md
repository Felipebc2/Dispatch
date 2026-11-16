---
id: nginx-map-cookie-magic-value
category: WEB
tags: [nginx, map, http-cookie, static, oracle, magic-value, guess, wordlist, discipline, vary-cookie, recon, no-brute]
tools: []
manuals: []
title: "nginx map $http_cookie router + the no-brute rule for magic-value challenges"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [client-side-js-dom-browser-inspection, generic-recon-scanner]
---

## How to recognize this pattern

- A single static server (`Server: nginx`) whose `/` returns a different page depending on a header —
  `Set-Cookie: rick; Path=/` with `Vary: Cookie`, and the same URL serves two sibling `index.html`
  files (different `ETag`/length) selected by an `nginx` `map $http_cookie $page { ... }` rule.
- The challenge reduces to **one unknown exact string** the server matches (a cookie token, a param
  value, a Host). The prompt is a riddle/meme with no canonical answer.

## Method

### 1. Reconstruct the routing rule as an oracle
```bash
curl -sik $U/ -H "Cookie: rick"          # exact key -> page A (524 b)
curl -sik $U/ -H "Cookie: morty"         # any other bare token -> troll page B (517 b)
curl -sik $U/ -H "Cookie: x=1"           # has '=' or ';' -> default
```
Map the boundaries precisely (case-sensitive? substring or exact? `=`/`;` behaviour?). The two
observable pages are a **validation oracle**: the *correct* value yields a third response
(different length / a flag), so a candidate is confirmed locally without touching flag submission.

### 2. Exhaust deterministic leaks first
Config/source leak (`nginx.conf`, `.git`, `*.bak`), alternate vhosts (`Host:`), path traversal/alias
off-by-slash, stego/metadata in served images, a second port/service, HTTP/1 vs /2, request smuggling.
If any leaks the `map` keys, you are done.

### 3. If it is purely a human-judgment magic string, STOP guessing
When the full server model, assets and infra are mapped and dead everywhere except one unknown exact
string, it is an **author's-intended-answer** problem, not a technical handle. Read the hint that the
server *gives* you (e.g. it sets cookie `rick` → the answer may complete it as a meme: `roll` →
Rickroll), try a few small, reasoned, rate-limited rounds (≤ ~20, stop-on-hit), then **park it** for
an out-of-band lead (teammate, organizer hint).

## Gotchas

- **Do not fire wordlists.** Blind/mass fuzzing is usually against the rules and the ephemeral
  container **falls over under burst load** (confirmed: `ffuf` at rate 40 kills it), wasting the TTL
  on restarts — and no wordlist solves an author's-judgment answer anyway.
- **`curl -b "morty"` footgun:** with no `=`, curl treats the arg as a **cookie-jar filename** and
  sends *no* Cookie header, so everything falsely looks like the default. Use `-H "Cookie: <value>"`.
- `map` matching is exact and case-sensitive by default; `RICK`/`xrickx`/trailing space do not hit the
  key. There is no substring behaviour to abuse.
- C2PA/`gpt-image` manifests in AI-generated images hold no prompt/answer — decode once, then drop it.

## Cross-reference

- `client-side-js-dom-browser-inspection`: when the magic value is instead derivable from client code.
- `generic-recon-scanner`: the deterministic-leak sweep to run before any guessing.

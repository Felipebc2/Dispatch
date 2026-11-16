---
id: flask-weak-secret-session-forge
category: WEB
tags: [flask, session, secret-key, itsdangerous, flask-unsign, signed-cookie, session-forgery, privilege-escalation, idor, uid, authorization, cookie-tampering]
tools: []
manuals: []
title: "Flask signed cookie: weak SECRET_KEY → forge session + authz split (IDOR)"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [jwt-alg-none, client-side-js-dom-browser-inspection, generic-recon-scanner]
---

## How to recognize this pattern

- `Server: gunicorn`/`Werkzeug` and a cookie `session=<b64>.<ts>.<sig>` — Flask's `itsdangerous`
  **signed** (not encrypted) cookie. Base64-decoding the first segment gives plain JSON with
  identity fields: `{"uid": N, "is_coordinator": false, "csrf": "..."}`.
- The identity (`uid`, `role`, `is_admin`) lives **inside** the cookie. If the signing key is weak,
  you can mint any session you like.

## Method

### 1. Recover the SECRET_KEY offline (never touches the server)
```bash
pip install flask-unsign[wordlist]
flask-unsign --unsign --cookie "<session value>"          # tries a wordlist (dev, secret, changeme, flask...)
# [+] Found secret key: 'dev'
```
Dev leftovers (`dev`, `secret`, `key`, `changeme`, the app name) are extremely common.

### 2. Forge the session
```bash
flask-unsign --sign --cookie "{'uid': 1, 'is_coordinator': True, 'csrf': 'x'}" --secret 'dev'
```

### 3. Beat the authorization split (the real trap)
Flipping `is_coordinator:true` for *your own* `uid` often only reveals a nav link / renders a
template branch (`{% if session.is_coordinator %}`) — the protected route re-checks the role
**in the DB, keyed on `uid`**, and returns 403. So you must also forge the **right `uid`**:
```
forge {is_coordinator:true, uid:1}  -> /coordination  -> 200   (uid=1 is the real admin)
forge {is_coordinator:true, uid:91} -> /coordination  -> 403   (your student uid; DB says not admin)
```
Sweep a small `uid` range (seeded users are usually `1..N`) and watch the admin route flip to 200.
The flag often is not on the admin panel itself but on that privileged user's `/profile`.

## Gotchas

- **Signed ≠ encrypted.** You can always *read* a Flask cookie's claims; a weak key lets you *write* them.
- Server-side authz may be split: a **forgeable template flag** (cookie) vs a **DB role keyed on uid**.
  Forging the flag alone fails — you need the uid of a user the DB actually trusts (an IDOR on `uid`).
- Professors/admins may live in a **separate table** from the session `uid` space; a forged `uid`
  that redirects instead of 403ing is pointing at the wrong table.
- No mass-assignment on signup (no `role` field honored) does not matter — the cookie is the sink.
- Keep the `csrf` field from a real cookie so same-session POSTs still validate.

## Cross-reference

- `jwt-alg-none`: the JWT equivalent (token identity you can forge when verification is weak).
- `client-side-js-dom-browser-inspection`: enumerate routes and the role-gated nav.

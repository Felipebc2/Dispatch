---
id: jwt-alg-none
category: WEB
tags: [jwt, alg-none, auth-bypass, token-forge, signature]
tools: [JWT]
manuals: ["Manuals/JWT/1. Fundamentos e Quando Usar.md", "Manuals/JWT/3. Contexto para Claude.md"]
title: "JWT alg:none — signature bypass"
difficulty: easy
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- The app uses JWT for session/authorization and accepts the token without validating the `alg`
  declared in the header.
- Strong signal: the server does not reject a token with `alg: none` — common in old JWT libraries
  or homegrown implementations.

## Method (see the full decision tree in `Manuals/JWT/3. Contexto para Claude.md`)

1. Decode the current token to inspect its header/payload (manual Python decoding script, without
   relying on jwt.io — see the Manual).
2. Edit the header to `{"alg":"none","typ":"JWT"}`, re-encode in Base64URL without padding.
3. Keep the payload (editing claims like `role`/`admin` if needed to escalate privilege).
4. Assemble the final token as `header.payload.` — **trailing empty dot**, with no third part.
5. Send that token in place of the original (cookie / `Authorization` header) and check whether the
   app accepts it.

```bash
python3 jwt_tool.py <token> -X a    # jwt_tool has the "alg none" mode built in (-X a)
```

## Gotchas

- Some libraries require literally `alg: none` (case-sensitive) — test capitalization variants
  (`None`, `NONE`) if the first attempt fails; some buggy implementations only filter one case.
- Confirm you are actually removing the signature (not leaving garbage after the last dot).
- If `alg:none` doesn't work, the next cheapest vector is RS256→HS256 confusion (see the Manual,
  the "vector decision tree" section) — don't keep hammering a vector that already failed.

## Cross-reference

Full execution detail, decision tree for every JWT vector (not just `alg:none`) and ready-to-use
commands: `Manuals/JWT/3. Contexto para Claude.md`. JWT structure concepts:
`Manuals/JWT/1. Fundamentos e Quando Usar.md`.

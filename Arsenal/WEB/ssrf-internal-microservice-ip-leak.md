---
id: ssrf-internal-microservice-ip-leak
category: WEB
tags: [ssrf, egress-policy, ip-leak, microservice, openapi, swagger, internal-api, m2m, credit-gate, self-referral, idor, response-preview]
tools: []
manuals: []
title: "SSRF: enumerating an internal microservice via an IP leaked in an egress error (+ credit-gate bypass)"
difficulty: medium
created: 2026-10-07
updated: 2026-10-07
related: [ssrf-lfi-filter-bypass]
---

## How to recognize this pattern

- An "innocent" app that **fetches a URL you supply** server-side and hands you back the response body:
  a malware scanner, preview/thumbnail generator, webhook, "link checker". The return exposes
  `status_code` + a `response_preview` with the body → **full-response SSRF** (direct exfil, not blind).
- A planted infra hint (an HTML comment, a header, a service name): a mention of an internal
  microservice, `swagger`/`openapi`, "backend network, off the internet". That's the pivot target.
- There may be a **gate** before the SSRF: the feature costs "credit/quota" that starts at 0. The gate
  is almost always a separate bug (the challenge's 2nd bug).

## Method

Adapt the target/fields to the current challenge before running. Reference case: MyNotes / StickerBoard,
`POST /notes` with `content` containing URLs; each URL becomes a scan.

### 1. Take down the credit gate (self-redeem)

A referral system like "when someone redeems YOUR code, **both** get credit" almost never validates
that the redeemed code isn't your own. Redeeming your own code credits both sides (= you), repeatable:

```bash
# register → get token + your own referral_code
curl -s -X POST $B/auth/register -d '{"username":"x","email":"x@x.com","password":"p"}'
# redeem your OWN code → +N credit on both sides, can repeat in a loop
curl -s -X POST $B/referrals/redeem -H "Authorization: Bearer $TOK" -d "{\"code\":\"$MY_CODE\"}"
```

### 2. Confirm the SSRF and **harvest the leaked IP**

The egress policy usually blocks by **hostname** and, on error, **leaks the resolved IP**; that's the
bypass:

```
http://internal-swagger/      → "[EGRESS-POLICY] blocked: internal-swagger -> 10.0.27.11"
http://10.0.27.11:8080/       → 200 {openapi...}   # the direct IP passes; mind the PORT
```

Always vary the **port** (80/8080/5000); the block may only be on the hostname, not on the IP:port.

### 3. Enumerate the internal API via OpenAPI and pivot

- Pull `/openapi.json` (or `/swagger.json`, `/v2/api-docs`) from the internal doc service → lists
  `servers` (other microservices) and `paths`.
- Resolve each microservice with the same trick (hostname blocked → IP leaked in the error).
- Typical vault chain: `cache-service` stores secrets under a hidden namespace (`secret:*`, not listed
  in `/cache/keys` but **readable directly** at `/cache?key=secret:vault:m2m`) → use the M2M key on the
  `vault-service` via a **query param** (`?api_key=...`, since SSRF can't set the `X-API-Key` header) →
  the "protected" endpoint (`/get-token`) returns the flag.

```bash
# scan() = redeem to top up credit + POST /notes with the internal URL, read response_preview
http://10.0.27.2:8080/cache/keys                     # lists public keys
http://10.0.27.2:8080/cache?key=secret:vault:m2m     # hidden secret namespace, directly accessible
http://10.0.27.5:8080/get-token?api_key=<m2m-key>    # flag
```

## Gotchas

- **Header vs query param:** via SSRF you only control the URL; if the service accepts auth by header
  OR query param, use the query param (`?api_key=`, `?token=`). Root/`/` may ignore the param and always
  return the hint; the real endpoint is another one (see the OpenAPI).
- **A "hidden" namespace ≠ protected:** `/cache/keys` hiding `secret:*` from the listing doesn't prevent
  `GET /cache?key=secret:...`. Security by obscurity.
- **Truncated response_preview:** the preview has a byte limit. Request specific paths (`/openapi.json`)
  instead of the root so you don't lose what matters at the cutoff.
- It's not this vector if the fetch is **blind** (only returns "safe/suspicious" without a body); then
  it's blind SSRF (DNS/HTTP out-of-band, port-scan by timing). A different pattern.

## Related / Cross-reference

- `Arsenal/WEB/ssrf-lfi-filter-bypass.md`: generating internal-address candidates
  (decimal/octal/hex/IPv6) when the filter is by IP string, not by hostname.
- `Arsenal/WEB/generic-recon-scanner.md`: path enumeration when there's no OpenAPI to guide you.

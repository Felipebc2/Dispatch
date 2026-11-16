---
id: dns-record-chain-exfil
category: NET
tags: [dns, dig, txt-record, mx-record, record-enumeration, record-type, zone, nxdomain, noerror, chain, exfiltration, say-my-name]
tools: []
manuals: []
title: "Data hidden in DNS records: enumerate every type and follow the chain"
difficulty: easy
created: 2026-11-16
updated: 2026-11-16
related: [nmap-port-service-recon, generic-recon-scanner]
---

## How to recognize this pattern

- A hostname that **has no A/AAAA record**, so the browser fails with `DNS_PROBE_...` / "site can't
  be reached". The challenge lives in **DNS itself**, not on a web server.
- The title/prompt points at names: "Say my name", "Nomes", a domain with nothing served. The
  `data:image/png` entries next to the failed request in DevTools are just Chrome's own error-page
  assets, not the challenge.

## Method

### 1. Enumerate every record type
```bash
for t in A AAAA TXT CNAME MX NS SOA SRV HINFO CAA ANY; do
  echo "== $t"
  dig +noall +answer +authority +comments "$HOST" "$t" | grep -E 'status:|IN'
done
```
`NOERROR` with an empty answer (only the zone SOA in the authority section) means the name exists but
that type has no data. Look for the types that **do** return data — usually `TXT` and `MX`.

### 2. Read TXT and follow the pointers
A `TXT` record often carries the first half of the flag plus a hint; an `MX`/`CNAME` points at the
**next name** to query:
```
nomes.<dom>.  3600  IN  TXT  "IDP{n0m3_ - ... mail me"
nomes.<dom>.  3600  IN  MX   10 sobrenome.<dom>.
```
Query the pointed-to name the same way (`dig sobrenome.<dom> TXT`) and concatenate the halves.

## Gotchas

- Don't stop at `A`/web — a failing website is the *hint* to switch to DNS, not a dead end.
- Use `+noall +answer` to cut noise; add `+authority +comments` to see `status:` and the SOA that
  proves a name exists even with an empty answer.
- The SOA being the registrar default (`dns.*.net`, date-serial) means nothing is hidden there — don't
  rabbit-hole on rname/serial.
- `MX` priority numbers are flavor; the **target hostname** is the next hop.
- Try a public resolver (`dig @1.1.1.1`) if the local one filters TXT, and `+tcp` for long records.

## Cross-reference

- `nmap-port-service-recon`: when the host *does* serve something after all.
- `generic-recon-scanner`: broader recon when the DNS trail runs out.

---
id: domain-recon-certificates-dns
category: OSINT
tags: [osint, domain, subdomain, crt-sh, certificate-transparency, whois, dns, txt-record, passive-dns, asn, reverse-ip]
tools: []
manuals: []
title: "OSINT: passive recon of a domain/IP (CT logs, DNS records, WHOIS, history)"
difficulty: easy
created: 2026-11-13
updated: 2026-11-13
related: [wayback-archived-site-recovery, email-pivot-account-discovery, nmap-port-service-recon]
toolsets: [osint/domain-infra, osint/archives]
---

## How to recognize this pattern

- The prompt gives a domain or IP and asks who owns it, what else is hosted there, or hints at a
  "hidden" or "forgotten" subdomain.
- Flags hidden in DNS: TXT records, a subdomain named after the flag, an old certificate's SAN.
- Attribution: "which company/registrar/hosting is behind this site?"

## Method

1. **DNS records** (local, no third party):
   ```bash
   dig +short ANY <domain>; for t in A AAAA MX NS TXT CNAME SOA CAA; do dig +short $t <domain>; done
   dig +short TXT _dmarc.<domain>
   ```
2. **Subdomains from Certificate Transparency** (passive, usually the fastest win):
   ```bash
   curl -s "https://crt.sh/?q=%25.<domain>&output=json" | jq -r '.[].name_value' | sort -u
   ```
   Then `dig` each one: TXT records of subdomains often hold the flag.
3. **WHOIS/RDAP**: `whois <domain>` or ICANN Lookup: registrar, creation date, nameservers.
   For IPs: owner and ASN via IPtoASN / bgp.he.net.
4. **Neighbors**: reverse IP (HackerTarget) lists other vhosts on the same IP; BuiltWith/PublicWWW
   find sites sharing an analytics ID.
5. **History**: SecurityTrails (historical A records) and `wayback-archived-site-recovery`.
6. **Exposed services** (passive): Shodan / Censys host page for banners and old certificates.

```bash
python3 scripts/arsenal_search.py --toolset osint/domain-infra --free
```

## Gotchas

- crt.sh is slow and sometimes times out: retry, or query `%.<domain>` with a narrower name.
- Wildcard DNS makes every subdomain resolve: compare against a random name first.
- Passive only unless the challenge scope allows touching the host; active scans belong to
  `nmap-port-service-recon` (NET).

## Cross-reference

- `wayback-archived-site-recovery`: old pages, old robots.txt, removed files.
- `nmap-port-service-recon`: when active scanning is in scope.

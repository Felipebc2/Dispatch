---
id: dns-exfiltration-pcap-reassembly
category: FOR
tags: [forensics, pcap, dns, dns-exfiltration, dns-tunneling, tshark, wireshark, subdomain, qry-name, iodine, dnscat, reassembly, hex-labels, base32]
tools: []
manuals: []
title: "DNS exfiltration in a PCAP: reassemble data from subdomain query labels"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [pcap-extract-credentials-files, dns-record-chain-exfil, tcp-overlapping-segment-conflict]
---

## How to recognize this pattern

- A capture full of **DNS queries** to one domain with **long, high-entropy subdomains**:
  `0.4a6f.exfil.evil.com`, `01.deadbeef.tunnel.net`, base32/hex gibberish as the leftmost label(s).
  DNS is a favorite covert channel because egress filters rarely inspect it.
- Volume of `A`/`TXT`/`NULL`/`CNAME` queries to the **same** second-level domain, often sequential.
  Prompt hints: "discreet tunnel", "exfiltration", "DNS", a firewall that "only allows DNS out".
- Each query carries a **chunk** of the payload in its name; the data is spread across many queries and
  must be re-ordered and concatenated.

## Method

### 1. Pull the query names (requests only, dedup retransmits)
```bash
tshark -r capture.pcap -Y 'dns.flags.response==0' -T fields -e dns.qry.name \
  | grep exfil | sort -u > names.txt
```
Inspect the shape: is there a sequence number? `NN.<hex>.domain` is common — `NN` orders the chunks.

### 2. Sort by sequence, strip the domain, concatenate, decode
```bash
tshark -r capture.pcap -Y 'dns.flags.response==0' -T fields -e dns.qry.name \
  | grep exfil | sort -t. -k1 -n \
  | awk -F. '{print $2}' | tr -d '\n' | xxd -r -p
```
Swap the decoder to match the label encoding:
- **hex** → `xxd -r -p`
- **base32** (DNS-safe, very common for tunnels) → `base32 -d`
- **base64url** → `tr '_-' '/+' | base64 -d`

### 3. No explicit sequence number
- Order by **packet time** (capture order): `tshark ... -e frame.time_epoch -e dns.qry.name`, sort by
  time, then strip/decode.
- Chunks may live in **answers** (TXT/NULL records) for bidirectional tunnels — pull `dns.txt` /
  `dns.resp.name` too.

### 4. Known tunneling tools leave fingerprints
- **iodine**: base32/base128 labels, `NULL`/`TXT` records, a handshake subdomain.
- **dnscat2**: hex labels, `dnscat` in traffic, encrypted after handshake.
- Recognizing the tool tells you the encoding and whether a key is needed.

## Gotchas

- **Dedup and order first.** Retransmitted queries duplicate chunks; out-of-order delivery scrambles
  the payload — always sort by the sequence field or by time before concatenating.
- The data label may be **one of several** (`<seq>.<data>.<domain>`); `awk -F.` the right field, and
  mind domains with extra dots.
- Case: DNS is case-insensitive, but base32 is upper-case — some tunnels use **0x20 case encoding**
  (mixed case *is* the data); preserve case if the payload looks like random casing.
- A single query can hold **multiple labels** of data; join all data labels, not just one.
- `strings capture.pcap` rarely helps here — the payload is encoded and fragmented across packets.

## Cross-reference

- `pcap-extract-credentials-files`: the HTTP/FTP sibling (Follow Stream, export objects) for plaintext
  exfil.
- `dns-record-chain-exfil`: data hidden in **served** DNS records you query live (NET), not captured
  tunnel traffic.
- `tcp-overlapping-segment-conflict`: another "reassembly order changes the meaning" pcap trick.

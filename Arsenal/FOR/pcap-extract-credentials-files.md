---
id: pcap-extract-credentials-files
category: FOR
tags: [forensics, pcap, pcapng, wireshark, tshark, http, ftp, export-objects, credentials, follow-stream]
tools: [Wireshark]
manuals: ["Manuals/Wireshark/3. Contexto para Claude.md"]
title: "PCAP: extract credentials and files from captured traffic"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- A `.pcap` / `.pcapng` attachment. The challenge asks for a password, a transferred file, or the flag
  lives in some captured payload.
- Cleartext protocols (HTTP, FTP, Telnet, DNS, SMTP) are the obvious target; TLS needs a key (see the
  gotcha).

## Method

### 1. Overview
```bash
capinfos chall.pcap                                  # size, packet count, time range
tshark -r chall.pcap -q -z io,phs                    # protocol hierarchy (where to focus)
tshark -r chall.pcap -q -z conv,tcp                  # TCP conversations (who talks to whom)
```

### 2. Quick sweep for flag/credential
```bash
strings -n 6 chall.pcap | grep -iE 'flag|pass|user|pwd|token'
tshark -r chall.pcap -Y 'http.request.method==POST' -T fields -e http.file_data
tshark -r chall.pcap -Y 'ftp.request.command=="USER" || ftp.request.command=="PASS"' \
       -T fields -e ftp.request.arg
```

### 3. Reconstruct streams and files
- Wireshark: `Follow > TCP Stream` on the suspicious conversation; `File > Export Objects > HTTP/SMB/...`
  to save transferred files.
- CLI equivalent:
```bash
tshark -r chall.pcap --export-objects http,./out/   # extract all HTTP objects
```
Then run `file`/`binwalk`/`strings` on the extracted files.

## Gotchas

- **TLS/HTTPS:** without the private key or an `SSLKEYLOGFILE` included in the challenge, it won't
  decrypt. Look for the key among the attachments before giving up on that vector.
- `Content-Encoding: gzip`/`deflate`: the HTTP payload arrives compressed. Wireshark decompresses it in
  Export Objects; by hand, `gunzip`.
- A flag **split** across several packets or hidden in unusual fields (ICMP data, DNS TXT, packet
  comments). If the obvious path yields nothing, sweep the less common protocols in `io,phs`.
- `.pcapng` can carry embedded comment/decryption-secret blocks. `editcap`/Wireshark show them.

## Cross-reference

Full commands/filters: `Manuals/Wireshark/3. Contexto para Claude.md` and the quick cheat sheet
`docs/cheatsheets/wireshark.md`. Steganography of media extracted from the pcap →
see `Manuals/LSB-Stego/`.

---
id: nmap-port-service-recon
category: NET
tags: [net, nmap, recon, port-scan, enumeracao, servico, versao, nse, banner, host-discovery, udp, smb, ftp, scan]
tools: []
manuals: []
title: "NET: port/service recon with nmap (initial enumeration)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [custom-tcp-service-scripting, scapy-packet-crafting]
---

## How to recognize this pattern

- The challenge gives you **only an IP/host (and maybe a range)** and nothing else: "the server is at X,
  find the flag". The first step is to discover **what's running**: open ports, services, versions.
- Also: you were given a port but the service on it is unknown, or you suspect a hidden UDP port/service
  (SNMP, TFTP, DNS) that a standard TCP scan misses.
- If it's already a text service on a known port (`nc host port` and it responds), skip the scan and go
  to `custom-tcp-service-scripting`.

## Method

### 1. Fast scan of all ports, then detail
```bash
nmap -p- --min-rate 2000 -T4 IP -oN all.txt       # all 65535, fast; note the open ones
nmap -sC -sV -p 22,80,445 IP -oN det.txt          # default scripts + version only on the open ones
```

### 2. If TCP yields nothing: UDP and a host blocking ping
```bash
sudo nmap -sU --top-ports 20 IP                   # common UDP (SNMP 161, DNS 53, TFTP 69), slow
nmap -Pn IP                                        # target drops ping: assume it's alive
nmap -sn 10.10.10.0/24                             # ping sweep over a range (which hosts exist)
```

### 3. Enumerate the service you found (NSE)
```bash
nmap --script vuln -p PORTAS IP                    # known vulns
nmap --script ftp-anon -p21 IP                     # anonymous FTP login
nmap --script http-enum -p80 IP                    # web dirs/files
nmap --script "smb-enum*" -p445 IP                 # SMB shares/users
```

### 4. Interact with the open port (the flag is usually in the banner/share)
```bash
nc -nv IP PORTA                                    # read the banner by hand
smbclient -L //IP -N                               # list SMB shares with no password
showmount -e IP                                    # NFS shares
ftp IP                                             # anonymous FTP
```

## Gotchas

- **Without root** nmap falls back to `-sT` (TCP connect); `-sS`, `-sU`, `-O` require `sudo`.
- `-p-` is slow: use `--min-rate`/`-T4` in a lab. If the network is flaky, `--max-retries 1` speeds it up
  but can **miss** ports. Confirm your suspicions with a targeted scan.
- A `filtered` port = firewall dropping; `open|filtered` in UDP = undetermined (the service may be there
  and just not answering). Don't conclude "closed" too early.
- The flag is rarely in nmap's output. Nmap only **points at where to look**; the next step is to talk
  to the service (`nc`/pwntools) or explore the web.
- Only against authorized CTF targets.

## Cross-reference

- Full flag/script cheat sheet: `docs/cheatsheets/nmap.md`.
- `custom-tcp-service-scripting`: once you've found the port, automate the conversation with the service.
- `scapy-packet-crafting`: when you need to forge a packet/binary protocol rather than just scan.
- A web service found (80/443/8080) → entries in `Arsenal/WEB/`.

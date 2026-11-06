---
id: boot2root-methodology-checklist
category: PWN
tags: [boot2root, privesc, privilege-escalation, enumeration, methodology, checklist, foothold, sudo, user-flag, root-flag, ssh, nmap, linpeas]
tools: []
manuals: []
title: "Boot2root box: the 4-stage methodology (ports to user to user.txt to root)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [nmap-port-service-recon, sudo-nopasswd-writable-input-exec, sudo-helper-forgeable-mac-gate, command-injection]
---

## How to recognize this pattern

- A single IP (often over a VPN) and a prompt like "boot2root", with several flags scored
  separately: open ports, a low-privilege username, a user flag, a root flag.
- The flags form a fixed ladder. Each stage hands you what the next one needs. The only thing
  that changes box to box is the foothold vector, so do not assume the previous box's vector.

## The ladder (what each stage is really asking)

```
Flag 1  open TCP ports        -> full port sweep
Flag 2  low-privilege user    -> read the custom service, extract creds/username, SSH in
Flag 3  user flag             -> usually /home/user.txt (not always the user's own home)
Flag 4  root flag             -> `sudo -l` + one local misconfig
```

## Method

### Stage 1: recon (always a full sweep first)
```bash
sudo nmap -sS -p- -T4 --max-retries 6 -Pn -n <ip> -oN full.txt    # every port, not the top 1000
nmap -sC -sV -p <csv-of-open-ports> -Pn -n <ip> -oN svc.txt       # versions on what is open
```
A patched OpenSSH on a non-standard port is almost never the vector; it is where you log in later.
The custom service (frequently a Python `http.server`/`BaseHTTPServer` on a high port) is the
attack surface. Report the open ports as a sorted comma list.

### Stage 2: foothold (read the custom app, it tells you the vector)
`curl` the service, read every route and hint, then match the foothold to what you see:

| Signal in the app | Likely vector | Arsenal entry |
|---|---|---|
| "ping"/"convert"/a filter on your input | command injection (watch filter bypass) | `command-injection` |
| a path or filename parameter, prefix check | path traversal / arbitrary file read | `ssrf-lfi-filter-bypass` |
| sequential `id=N`, a hidden record | IDOR | `sqli-union-authbypass` (enum section) |
| a crib + a blob, "encoded"/"masked" log | repeating-key XOR to recover creds | `xor-repeating-key` |
| an HMAC/token gate, a leaked key | forge or length-extend the MAC | `sudo-helper-forgeable-mac-gate` |

The foothold yields a username and password (or a key file). SSH in on the port from stage 1.

### Stage 3: user flag
```bash
cat /home/user.txt 2>/dev/null || find / -name 'user.txt' 2>/dev/null   # often /home, not ~
```

### Stage 4: root (enumerate, then one misconfig)
```bash
sudo -l                      # the single most common win on these boxes
id; find / -perm -4000 -type f 2>/dev/null                 # setuid binaries
getcap -r / 2>/dev/null; cat /etc/crontab; ls -la /opt /srv  # caps, cron, app trees
```
A `sudo NOPASSWD` entry on a wrapper script is the classic ending. See
`sudo-nopasswd-writable-input-exec` and `sudo-helper-forgeable-mac-gate` for the two shapes that
recur. Cross-check `gtfobins` for any binary you may run as root.

## Gotchas

- Run the full `-p-` sweep before anything. A high service port (8000 to 9000) is easy to miss on
  a top-ports scan, and it is usually the whole box.
- Flag 2 is the username, derived from the app theme or leaked in the foothold, not a file.
- The user flag is not always in the SSH user's home; search `/home` broadly.
- A service version that is current and patched is a dead end on purpose. Spend time on the custom
  code, not on CVE-hunting the SSH or HTTP banner.
- If the foothold runs as a service account (for example the web user), you may still need a second
  hop to the human user before `sudo -l` is useful.

## Related / Cross-reference

- `nmap-port-service-recon`: the recon manual for stage 1.
- `sudo-nopasswd-writable-input-exec` and `sudo-helper-forgeable-mac-gate`: the two stage-4 shapes.
- `command-injection`, `ssrf-lfi-filter-bypass`, `xor-repeating-key`: common stage-2 footholds.

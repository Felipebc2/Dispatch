---
id: memory-dump-volatility
category: FOR
tags: [forensics, memory, memory-dump, volatility, volatility3, ram, pstree, cmdline, hashdump, filescan, dumpfiles, lime, raw]
tools: []
manuals: []
title: "Memory forensics: RAM dump with Volatility 3"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [pcap-extract-credentials-files]
---

## How to recognize this pattern

- A large attachment (`.raw`, `.mem`, `.vmem`, `.lime`, `.dmp`): a memory dump. `file` says "data";
  the size matches RAM (hundreds of MB to GB).
- The prompt mentions "the process was running", "we captured the machine while it was on", "what the
  user typed/opened". The flag lives in a process, command, in-memory file, or a registry entry.

## Method

### 1. Identify the profile / OS
```bash
vol -f dump.raw windows.info          # Volatility 3: auto-detects the Windows build
vol -f dump.raw banners.Banners       # Linux: find the kernel version for symbols (ISF)
```

### 2. Standard sweep (highest-yield order first)
```bash
vol -f dump.raw windows.pstree        # process tree (find the suspect)
vol -f dump.raw windows.cmdline       # command line of each process (flags, passwords)
vol -f dump.raw windows.filescan | grep -iE 'flag|secret|\.txt|desktop'
vol -f dump.raw windows.dumpfiles --virtaddr <OFFSET>   # extract a file found in filescan
vol -f dump.raw windows.hashdump      # NTLM hashes (crack later)
vol -f dump.raw windows.clipboard     # clipboard (flag copied?)
```
Linux: `linux.pslist`, `linux.bash` (command history), `linux.proc.Maps`.

### 3. String brute force (always-valid fallback)
```bash
strings -n 6 dump.raw | grep -iE 'hik_|flag\{' ; strings -e l dump.raw | grep -i hik_
```

## Gotchas

- **Volatility 3 ≠ 2** in syntax: v3 uses `windows.pstree` (a namespaced plugin), v2 used
  `--profile=... pstree`. Confirm which one is installed (`vol --version`).
- Linux needs the exact kernel's **symbols (ISF)**. If `banners` yields a version with no ready-made
  ISF, it's painful; in that case `strings`/`bulk_extractor` usually deliver the flag faster.
- The flag may sit in a process that is **terminated but still in memory**. `filescan`/`strings` catch
  what `pslist` won't show.
- Don't confuse this with a **single-process dump** (minidump). That's `gdb`/`strings`, not Volatility.

## Cross-reference

- `pcap-extract-credentials-files`: same FOR toolbox, but for network traffic.
- An extracted file that is an image with stego → `lsb-image-steganography` (CRYPTO/STEGO).

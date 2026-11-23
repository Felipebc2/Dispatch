---
id: memory-dump-volatility
category: FOR
tags: [forensics, memory, memory-dump, volatility, volatility3, ram, pstree, cmdline, hashdump, filescan, dumpfiles, lime, raw, heap-dump, core-dump, struct-carving, marker, xor-obfuscated]
tools: []
manuals: []
title: "Memory forensics: RAM dump with Volatility 3"
difficulty: medium
created: 2026-10-04
updated: 2026-11-23
related: [pcap-extract-credentials-files, xor-repeating-key, large-artifact-gigabyte-triage]
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

### 4. Single-process / heap dump: carve a known struct

A `heap.dump`/core dump (one process, not full RAM) where `strings | grep` finds **nothing** usually
means the secret is **obfuscated in memory** — stored inside a struct, often XORed. Volatility doesn't
help here; you carve the bytes by hand. Find the struct's **marker**, then parse the fields after it:
```python
raw = open("heap.dump", "rb").read()
i = raw.find(b"AUTHBLK\x00") + 8          # locate the marker, skip past it
key = raw[i]                               # layout e.g.: [1-byte XOR key]
ln  = int.from_bytes(raw[i+1:i+3], "little")   # [2-byte little-endian length]
tok = raw[i+3:i+3+ln]                      # [length bytes of payload]
print(bytes(b ^ key for b in tok))         # de-XOR → flag
```
Recognize the layout from the binary/source if given; otherwise eyeball the hex around the marker
(`xxd | grep -A2 AUTHBLK`) to infer key/length/data offsets. The de-obfuscation is often a repeating
XOR — see `xor-repeating-key` when the key is multi-byte.

## Gotchas

- **Volatility 3 ≠ 2** in syntax: v3 uses `windows.pstree` (a namespaced plugin), v2 used
  `--profile=... pstree`. Confirm which one is installed (`vol --version`).
- Linux needs the exact kernel's **symbols (ISF)**. If `banners` yields a version with no ready-made
  ISF, it's painful; in that case `strings`/`bulk_extractor` usually deliver the flag faster.
- The flag may sit in a process that is **terminated but still in memory**. `filescan`/`strings` catch
  what `pslist` won't show.
- Don't confuse this with a **single-process dump** (minidump/heap/core). That's `gdb`/`strings` or
  manual struct carving (step 4), not Volatility.

## Cross-reference

- `pcap-extract-credentials-files`: same FOR toolbox, but for network traffic.
- An extracted file that is an image with stego → `lsb-image-steganography` (CRYPTO/STEGO).

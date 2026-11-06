---
id: registry-shimcache-appcompatcache
category: FOR
tags: [forensics, windows, registry, hive, system-hive, regf, shimcache, appcompatcache, application-compatibility, filetime, last-modified, run-key, autostart, persistence, regipy, appcompatcacheparser, utf-16le, mmap]
tools: [Windows-Registry]
manuals: ["Manuals/Windows-Registry/3. Contexto para Claude.md"]
title: "Windows SYSTEM hive: parse ShimCache (AppCompatCache) and cross-check autostart keys"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [large-artifact-gigabyte-triage, memory-dump-volatility]
---

## How to recognize this pattern

- A `SYSTEM` file (`file` says `MS Windows registry file, NT/2000 or above`), magic `regf` at offset 0.
- The question asks which program "was present / seen / ran" on a machine, or for a file's
  modification time, or which program is NOT set to start at logon.
- Location: `SYSTEM\ControlSet00N\Control\Session Manager\AppCompatCache\AppCompatCache`
  (`N` from `SYSTEM\Select\Current`). XP used `...\AppCompatibility\AppCompatCache`.

## Method

### 1. Off-the-shelf parsers
```bash
pip install regipy
regipy-plugins-run SYSTEM -o plugins.json      # runs every plugin, shimcache included
regipy-dump SYSTEM -o dump.json                # whole key tree (small hives only)
# Windows: AppCompatCacheParser.exe -f SYSTEM --csv out   (Eric Zimmerman)
```

### 2. Hand parse with mmap (huge or synthetic hives, GUI viewers stall)
Windows 10/11 layout: a header (`0x34` or `0x30` bytes, its own size in the first u32), then entries:
`"10ts" | u32 | u32 entry_size | u16 path_len_bytes | UTF-16LE path | u64 FILETIME | u32 data_len | data`.
Windows 8/8.1 use `00ts`/`10ts` with a similar layout; Windows 7 starts with magic `0xBADC0FFE`.
```python
import datetime, mmap, struct, sys
f = open(sys.argv[1], 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
ft = lambda v: datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=v // 10)
i, n = m.find(b'10ts'), 0
while i != -1:
    size, plen = struct.unpack('<IH', m[i + 8:i + 14])
    if 0 < plen < 2048 and plen % 2 == 0:
        path = m[i + 14:i + 14 + plen].decode('utf-16le', 'replace')
        mtime = struct.unpack('<Q', m[i + 14 + plen:i + 22 + plen])[0]
        print(n, hex(i), ft(mtime).isoformat() + 'Z', path); n += 1
        i = m.find(b'10ts', i + 12 + size)
    else:
        i = m.find(b'10ts', i + 1)
```
Pipe to `grep -iv 'windows\\system32'` or group by directory to find the outliers among filler.

### 3. Search a known folder directly
```bash
strings -a -t x -el SYSTEM | grep -i 'users\\public'       # UTF-16LE paths with offsets
```
When anchoring on a path hit, take the start from the known prefix (`C:\`): the u16 length just
before the path can be a printable byte and a naive backward scan absorbs it.

### 4. Cross-check autostart and execution evidence
- Run keys: `SOFTWARE\Microsoft\Windows\CurrentVersion\Run` (normally in the SOFTWARE hive, per-user
  in `NTUSER.DAT`), plus `RunOnce`. Services: `SYSTEM\ControlSetN\Services\<name>\Start` (2 = auto).
- Real execution times: BAM (`SYSTEM\...\Services\bam\State\UserSettings\<SID>`), Amcache.hve,
  Prefetch.

## Gotchas

- The ShimCache FILETIME is the file's **last modification time** (`$STANDARD_INFORMATION`), not the
  execution time. On Windows 10+ presence in the cache does not prove execution either.
- Order matters: index 0 is the most recently inserted entry. The cache is written at shutdown, so a
  live-acquired hive may lack recent entries (check memory: Volatility `windows.shimcachemem`).
- FILETIME to Unix: `(ft - 116444736000000000) / 1e7`.
- A planted Run key or the newest-timestamp entry is often the bait; the answer is the entry that
  matches every clause of the question.
- NOT this pattern: if the question is about user activity (recent docs, typed paths, UserAssist),
  look at `NTUSER.DAT` instead of SYSTEM.

## Cross-reference

`large-artifact-gigabyte-triage` for mmap scanning of oversized hives; `memory-dump-volatility` when the
registry must be read from a RAM image.

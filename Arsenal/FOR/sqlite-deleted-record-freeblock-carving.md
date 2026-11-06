---
id: sqlite-deleted-record-freeblock-carving
category: FOR
tags: [forensics, sqlite, sqlite3, deleted-record, deleted-row, freeblock, freelist, unallocated, page-slack, carving, record-header, serial-type, varint, wal, undark, mmap]
tools: []
manuals: []
title: "SQLite: carve a deleted row from freeblocks, page slack or the freelist"
difficulty: hard
created: 2026-11-06
updated: 2026-11-06
related: [large-artifact-gigabyte-triage, file-carving-signature-repair]
---

## How to recognize this pattern

- A `.db` / `.sqlite` attachment (`file` says `SQLite 3.x database`), and the question asks about a
  record (a time, a user, a visit) that **no SQL query returns**, whatever unit or range you try.
- The live rows follow a regular pattern and the target would break it.
- `PRAGMA freelist_count` may be 0 and there may be no `-wal` / `-journal`: the row can still be in
  a freeblock or the unallocated gap of a live leaf page.

## Method

### 1. Triage without modifying the file
```bash
sqlite3 'file:chall.db?mode=ro&immutable=1' '.schema' 'PRAGMA page_size' 'PRAGMA page_count' 'PRAGMA freelist_count'
ls -la chall.db*                     # a -wal file holds older page versions: check it too
sqlite3 'file:chall.db?mode=ro&immutable=1' '.recover' > recovered.sql   # freelist / orphan pages, NOT freeblocks
```

### 2. Search for the packed value, not its text
SQLite stores integers big-endian with the smallest serial type that fits (1=int8, 2=int16,
3=int24, 4=int32, 5=int48, 6=int64, 7=float64). A Unix-seconds timestamp is int32; milliseconds is
int48. `strings | grep` never finds them.
```bash
python3 -c 'import struct;print(struct.pack(">I",1700000000).hex())'
LC_ALL=C grep -obUaP '\x65\x53\xf1\x00' chall.db       # byte offset of each hit; page = off//page_size + 1
```

### 3. Dump freeblocks and unallocated gaps of every table leaf page
```python
import mmap, re, struct, sys
f = open(sys.argv[1], 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
ps = struct.unpack('>H', m[16:18])[0]; ps = 65536 if ps == 1 else ps
for p in range(len(m) // ps):
    base = p * ps; h = base + (100 if p == 0 else 0)
    if m[h] != 0x0D: continue                                  # 0x0D table leaf (0x0A index leaf too)
    fb, ncell, content = struct.unpack('>HHH', m[h+1:h+7])
    regions = [(h + 8 + 2 * ncell, base + (content or 65536))]  # gap: pointer array end -> cell content
    while fb and fb < ps and len(regions) < 1000:                # freeblock chain: u16 next, u16 size
        nxt, sz = struct.unpack('>HH', m[base+fb:base+fb+4]); regions.append((base+fb+4, base+fb+sz)); fb = nxt
    for a, b in regions:
        for s in re.findall(rb'[\x20-\x7e]{5,}', m[a:b]): print(p + 1, hex(a), s[:80])
```

### 4. Decode the carved record
A freed cell loses its first 4 bytes (overwritten by the freeblock header: next offset + size),
which usually kills the payload-length and rowid varints. The **record header survives**:
`[header-length varint][serial type varint per column]`, then the column values back to back.
Text serial type N (odd, >=13) is `(N-13)/2` bytes; blob N (even, >=12) is `(N-12)/2`.
```python
def varint(b, i):
    v = 0
    for k in range(9):
        c = b[i + k]
        if k == 8: return (v << 8) | c, i + 9
        v = (v << 7) | (c & 0x7F)
        if c < 0x80: return v, i + k + 1
def record(b, i):                     # i = offset of the header-length byte
    hl, j = varint(b, i); end, out = i + hl, []
    while j < i + hl:
        t, j = varint(b, j)
        n = [0, 1, 2, 3, 4, 6, 8, 8, 0, 0][t] if t < 10 else (t - 12 - t % 2) // 2
        raw = bytes(b[end:end + n]); end += n
        out.append(raw.decode('utf-8', 'replace') if t >= 13 and t % 2 else
                   int.from_bytes(raw, 'big', signed=True) if 1 <= t <= 6 else {0: None, 8: 0, 9: 1}.get(t, raw))
    return out
```
Find the header by walking back from the needle hit: the columns before it have known sizes, and the
header bytes sit right before the first value. An `INTEGER PRIMARY KEY` column shows as NULL (type 0)
because its value lived in the lost rowid.

## Gotchas

- Open read-only (`immutable=1`, `mmap`). A read-write open can checkpoint a WAL or trigger
  auto-vacuum and overwrite the slack you need. Hash the file before you start.
- The tail of a freed cell is often overwritten by later live cells; columns at the end may be garbage.
- Other gaps hold leftovers of ordinary rows. Validate a hit against the question, not just against
  "it is deleted".
- NOT this pattern: `PRAGMA secure_delete=ON` (freed space is zeroed; some distro builds default it
  ON, so turn it off when you build a local test DB), or the data is in an overflow page (records
  larger than the page): then follow the overflow chain or carve the page.
- Off-the-shelf carvers: `undark`, `sqlite-deleted-records-parser` (sqlparse.py), `bring2lite`.

## Cross-reference

`large-artifact-gigabyte-triage` for mmap and needle-search technique at 1 GB scale;
`file-carving-signature-repair` for carving files rather than records.

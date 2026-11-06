---
id: large-artifact-gigabyte-triage
category: FOR
tags: [forensics, large-file, gigabyte, 1gb, mmap, streaming, binary-search, needle-search, struct-pack, grep-binary, utf-16le, strings-el, read-only, filler, decoy, outlier, pcap-walker, tshark-fields, dd-skip]
tools: [Wireshark]
manuals: ["Manuals/Wireshark/3. Contexto para Claude.md"]
title: "Gigabyte-scale artifacts: mmap, packed-needle search, streaming walkers and outlier hunting"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [sqlite-deleted-record-freeblock-carving, fat32-unallocated-cluster-recovery, registry-shimcache-appcompatcache, tcp-overlapping-segment-conflict, pcap-extract-credentials-files, file-carving-signature-repair]
---

## How to recognize this pattern

- The attachment is about 1 GB (database, disk image, registry hive, pcap) and most of it is
  synthetic filler: repeated rows, padding files, thousands of near-identical entries.
- GUI tools (DB browsers, registry viewers, Wireshark) stall or crash.
- Several decoys agree with each other; the real answer is the one record that breaks the pattern.

## Method

### 1. Cheap structure first, never a full load
```bash
ls -l f; file f; sha256sum f                 # hash once, before any tool can touch it
xxd -l 512 f                                  # header: declared sizes vs the real file size
xxd -s $((OFFSET)) -l 256 f                   # look at any offset without copying
dd if=f bs=1 skip=$((OFFSET)) count=4096 status=none > slice.bin
```
Check whether the size is real structure (declared length covers the file) or trailing padding.

### 2. Search for the packed value, in every encoding
```bash
strings -a -t x -n 6 f | grep -i key          # ASCII with hex offsets
strings -a -t x -el f | grep -i key           # UTF-16LE (Windows paths, FAT names, hidden text)
LC_ALL=C grep -obUaP '\x65\x53\xf1\x00' f     # raw bytes: integers, timestamps, magic values
```
```python
import mmap, struct, sys
f = open(sys.argv[1], 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
for needle in (struct.pack('>I', 1700000000), struct.pack('<I', 1700000000), 'C:\\Users'.encode('utf-16le')):
    i = m.find(needle)
    while i != -1:
        print(needle.hex(), hex(i), 'page', i // 4096 + 1); i = m.find(needle, i + 1)
```
Convert each hit offset into the format's unit (page, cluster, record, packet) and parse locally.

### 3. Stream the structure instead of loading it
- Walk records with offsets over the `mmap`, yielding one at a time; keep only counters or hashes.
- pcap: one field dump to TSV (`tshark -r f -T fields -e ...`), then work on the TSV. Or walk raw
  records (classic pcap only, not pcapng):
```python
f = open(sys.argv[1], 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
e = '<' if m[:4] == b'\xd4\xc3\xb2\xa1' else '>'; i = 24
while i + 16 <= len(m):
    sec, usec, incl, orig = struct.unpack(e + 'IIII', m[i:i + 16]); pkt = m[i + 16:i + 16 + incl]
    i += 16 + incl                              # parse Ethernet/IP/TCP from pkt here
```
- SQLite: `sqlite3 'file:f?mode=ro&immutable=1'` for SQL, `mmap` for page slack.
- Sorted data (timestamped logs, fixed-size records): binary search on the offset. Seek to the
  middle, resync to the next record boundary (newline, magic, fixed stride), compare the key, recurse.

### 4. Hunt the outlier
Filler is uniform, so count: `collections.Counter` on the key fields, then print the values with
count 1 (or exactly 2), the only non-numeric value, the only out-of-range timestamp, the only
cluster or entry outside the filler's folder. The target is whatever breaks the generator's pattern.

## Gotchas

- Read-only always: opening a SQLite DB read-write can checkpoint/vacuum, mounting an image can
  update metadata. Work from `mmap` with `ACCESS_READ`.
- `f.read()` on 1 GB doubles memory with every slice copy; `mmap` slices are cheap. Keep the file
  object alive while the map is used (do not `mmap(open(...).fileno())` inline).
- `strings` misses binary integers and UTF-16; grep for packed bytes in both endiannesses.
- When splitting work into chunks, overlap each chunk by `len(needle) - 1` bytes.
- Many agreeing decoys (metadata, live rows, slack, the most frequent value) are bait; verify which
  storage area the question actually names.

## Cross-reference

Format-specific entries: `sqlite-deleted-record-freeblock-carving`, `fat32-unallocated-cluster-recovery`,
`registry-shimcache-appcompatcache`, `tcp-overlapping-segment-conflict`. Tshark field export:
`Manuals/Wireshark/3. Contexto para Claude.md`.

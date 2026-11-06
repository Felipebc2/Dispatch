---
id: fat32-unallocated-cluster-recovery
category: FOR
tags: [forensics, fat32, fat, vfat, disk-image, filesystem, unallocated-cluster, free-cluster, unclaimed, file-slack, slack-space, deleted-file, fsinfo, cluster-chain, sleuthkit, blkls, fls, utf-16le, strings-el]
tools: []
manuals: []
title: "FAT32: find data in an unallocated (unclaimed) cluster, not in slack or live files"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [large-artifact-gigabyte-triage, file-carving-signature-repair]
---

## How to recognize this pattern

- A raw disk/volume image (`file` says `DOS/MBR boot sector ... FAT (32 bit)`), often large and
  stuffed with filler files that all repeat the same bait value.
- The prompt says the data is "where no file claims it", "erased", "left behind", or the live files
  plainly do not contain the answer.
- Key distinction: **slack** (bytes after EOF inside a cluster a file owns) is still claimed space.
  **Unallocated** means FAT entry = 0 and no directory entry chain covers the cluster.

## Method

### 1. Sleuthkit, if available
```bash
fsstat volume.img                         # cluster size, data area start, FSInfo
fls -r -d volume.img                      # deleted entries (0xE5) with their start cluster
blkls volume.img > unalloc.bin            # concatenation of every unallocated cluster
strings -a -t x unalloc.bin; strings -a -t x -el unalloc.bin   # ASCII and UTF-16LE
blkcalc -u $((0xOFFSET / 4096)) volume.img   # map an unalloc.bin unit back to the real cluster
blkls -s volume.img > slack.bin           # slack only, to rule it in or out separately
```
Add `-o <sector>` to every command when the image has a partition table (`mmls volume.img`).

### 2. Pure Python walker (no sleuthkit): claimed vs unclaimed non-zero clusters
```python
import mmap, struct, sys
f = open(sys.argv[1], 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
bps, spc, rsv, nf = struct.unpack('<HBHB', m[11:17]); tot, spf, root = struct.unpack('<II4xI', m[32:48])
cs, fat0 = bps * spc, rsv * bps; data = fat0 + nf * spf * bps; ncl = (tot * bps - data) // cs
fat = memoryview(m)[fat0:fat0 + spf * bps].cast('I')
off = lambda c: data + (c - 2) * cs
def chain(c):
    out = []
    while 2 <= c < 0x0FFFFFF8 and c not in out and len(out) <= ncl: out.append(c); c = fat[c] & 0x0FFFFFFF
    return out
claimed = set()
def walk(c, path):
    for cl in chain(c):
        claimed.add(cl)
        for i in range(off(cl), off(cl) + cs, 32):
            e = m[i:i + 32]
            if e[0] == 0: return
            if e[11] == 0x0F or e[11] & 8 or e[:2] in (b'. ', b'..'): continue
            sc = struct.unpack('<H', e[20:22])[0] << 16 | struct.unpack('<H', e[26:28])[0]
            print('DEL' if e[0] == 0xE5 else '   ', path + '/' + e[:11].decode('latin1'), 'cl', sc, 'sz', struct.unpack('<I', e[28:32])[0])
            if e[0] != 0xE5 and sc:
                claimed.update(chain(sc))
                if e[11] & 0x10: walk(sc, path + '/' + e[:11].decode('latin1').strip())
walk(root, '')
free = [c for c in range(2, ncl + 2) if c not in claimed and any(m[off(c):off(c) + cs])]
print('unclaimed non-zero clusters:', len(free), [(c, hex(off(c))) for c in free[:50]])
```
Then inspect each hit: `xxd -s $((OFF)) -l 256 volume.img`.

### 3. FSInfo hint
FSInfo sector (BPB offset 48 gives its sector number): free count at +488, **next free cluster at
+492**. After a delete the hint often points at the most recently freed cluster.
```bash
python3 -c 'import struct,sys;d=open(sys.argv[1],"rb").read(1024);s=struct.unpack("<H",d[48:50])[0]*512;print(struct.unpack("<II",d[s+488:s+496]))' volume.img
```

## Gotchas

- `strings` defaults to ASCII. Hidden text is often UTF-16LE: always also run `strings -el`.
- Slack words and repeated "posted" values in live files are classic decoys. Decide which space the
  question means (live / slack / deleted entry / unallocated) and search only that.
- Deleted directory entries (`0xE5`) keep the start cluster and size but the FAT chain is zeroed:
  recover by reading `size` bytes contiguously from the start cluster.
- Check both FAT copies (`nf`=2): a differing second FAT can reveal a chain that was cut.
- Check the gap after the filesystem end (`tot * bps` vs image size) and reserved sectors for data too.
- NOT this pattern: NTFS/ext images (use `fls`/`icat`, `$MFT`, journal), or a file signature buried in
  a blob (see `file-carving-signature-repair`).

## Cross-reference

`large-artifact-gigabyte-triage` (mmap at 1 GB scale); `file-carving-signature-repair` for carving
whole files out of unallocated space.

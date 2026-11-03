---
id: file-carving-signature-repair
category: FOR
tags: [forensics, carving, binwalk, foremost, magic-bytes, file-signature, header-repair, polyglot, zip, pdf, png, pngcheck, hexedit]
tools: []
manuals: []
title: "File carving + magic byte repair (corrupted/embedded file)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [memory-dump-volatility, lsb-image-steganography]
---

## How to recognize this pattern

- A file that won't open: the extension lies, the header is corrupted on purpose, or it has **another
  file hidden inside** (data past the logical end, or a concatenation/polyglot).
- `file` says "data" or the wrong type; the "broken" image opens only partially; a ZIP/PDF refuses.

## Method

### 1. What it really is + what's inside
```bash
file sample ; xxd sample | head                 # real magic bytes (first 4-8 bytes)
binwalk sample                                   # embedded signatures (zip, png, gzip...)
binwalk -e sample                                # extract what it found (or foremost sample)
```

### 2. Repair the header (magic bytes) with hexedit
Swap the first bytes for the correct magic:
| Type | Magic (hex) |
|---|---|
| PNG | `89 50 4E 47 0D 0A 1A 0A` |
| JPG | `FF D8 FF` |
| GIF | `47 49 46 38` |
| ZIP/docx/jar | `50 4B 03 04` |
| PDF | `25 50 44 46` (`%PDF`) |
| ELF | `7F 45 4C 46` |
| GZIP | `1F 8B 08` |
```bash
# e.g. force PNG into the first 8 bytes
printf '\x89PNG\r\n\x1a\n' | dd of=sample bs=1 seek=0 conv=notrunc
pngcheck -v sample          # validate/point at the broken chunk (IHDR with zeroed dimensions, etc.)
```

### 3. Data past the logical end / polyglot
```bash
# the flag often comes AFTER the IEND (PNG) / %%EOF (PDF) / EOCD (zip):
binwalk sample ; tail -c 200 sample | xxd
# corrupted ZIP: repair
zip -FF quebrado.zip --out consertado.zip
```

## Gotchas

- PNG: beyond the magic, the **IHDR** carries width/height — if they were zeroed to "crop" the image,
  `pngcheck` flags it and you can restore the dimensions via hexedit (the flag hides in the "cropped" part).
- Not every "file inside" is carving: if it's LSB in an intact image → `lsb-image-steganography`,
  not binwalk.
- `binwalk -e` can fail on permissions/compression — `foremost`/manual `dd` (with binwalk's offset)
  is the plan B.
- Polyglot (e.g. a file that is both a valid ZIP **and** a valid PNG) — change the extension and open it both ways.

## Cross-reference

- `lsb-image-steganography` — when the image is intact and the data lives in the bits, not the header.
- `pcap-extract-credentials-files` — carving files transferred in a pcap (export objects).

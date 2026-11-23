---
id: lsb-image-steganography
category: CRYPTO
tags: [stego, steganography, lsb, least-significant-bit, png, bmp, zsteg, stegsolve, stegolsb, bit-plane, image, prng-dispersed, text-chunk, appended-zip, polyglot, webp]
tools: [LSB-Stego]
manuals: ["Manuals/LSB-Stego/3. Contexto para Claude.md"]
toolsets: [for/online-for]
title: "LSB image steganography (zsteg / stegsolve)"
difficulty: easy
created: 2026-10-04
updated: 2026-11-23
related: [jsteg-jpeg-dct-steganography, file-carving-signature-repair]
---

## How to recognize this pattern

- The attachment is a **lossless image** (PNG, BMP, GIF) with no obvious challenge ("just a photo").
  LSB lives in uncompressed/lossless formats; **JPEG is almost never LSB** (compression destroys the
  bits).
- The prompt mentions "look closer", "layers", "what you can't see", or hands you an image that's too
  large for its content.
- `strings`/`binwalk` on the image don't find the flag directly (otherwise it'd be trivial FOR, not
  stego).

## Method

### 1. Quick triage (always before LSB)
```bash
file img.png && binwalk img.png            # embedded file? (FOR, not LSB)
strings -n 6 img.png | grep -i hik_        # flag in plain text?
exiftool img.png                           # metadata/comment
```

### 2. Automatic LSB
```bash
zsteg -a img.png                           # PNG/BMP: sweeps all bit-planes/channels/orders
zsteg -E b1,rgb,lsb,xy img.png             # extract a specific channel that -a pointed to
```

### 3. Visual / manual
- **stegsolve** (Java GUI): browse bit-planes (Red 0, Green 0...), "Data Extract" to assemble the
  bit/channel order; good when `zsteg` finds nothing but there's a pattern visible in a plane.
- Python (custom LSB, known order):
```python
from PIL import Image
img = Image.open("img.png").convert("RGB")
bits = "".join(str(p & 1) for px in img.getdata() for p in px)   # LSB of R,G,B in xy order
data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits)//8*8, 8))
print(data[:200])
```

### 4. Variants zsteg won't catch

**LSB dispersed by a PRNG** — bits scattered over pixels in a seeded pseudo-random order (not
sequential), so `zsteg`'s linear scan finds nothing. The seed is usually given (`1337`, the year, a
word). Replay the same permutation:
```python
import numpy as np
from PIL import Image
flat = np.array(Image.open("img.png"))[:, :, 2].flatten()   # e.g. blue channel
order = np.random.default_rng(1337).permutation(len(flat))[:47*8]   # seed + bit count
bits = [flat[p] & 1 for p in order]
print(bytes(int("".join(map(str, bits[i:i+8])), 2) for i in range(0, len(bits), 8)))
```

**PNG `tEXt`/`zTXt` chunk** — a key/flag parked in a text chunk (not the pixels). Read with `exiftool`,
`strings`, or `pngcheck -t`. Often chained: the chunk holds a base64 key, and the real payload is
**appended after `IEND`** and XORed with it:
```python
import re, base64
d = open("img.png", "rb").read()
k = base64.b64decode(re.search(rb"tEXt\w+\x00([A-Za-z0-9+/=]+)", d).group(1))
tail = d[d.rfind(b"IEND") + 8:]                             # bytes glued after the PNG end
print(bytes(tail[i] ^ k[i % len(k)] for i in range(len(tail))))
```

**Format-lies polyglot** — a file named `.png` that's really a WebP/other with a **ZIP appended**
(`PK\x03\x04` after the image data). `file` reveals the true type; just unzip it:
```bash
file img.png          # "RIFF ... WebP" despite the .png name
unzip img.png         # extracts the hidden archive
```

## Gotchas

- Order matters: bit-plane (b1/b2...), channels (r/g/b/a), and scan order (xy vs yx). `zsteg -a`
  tests the combinations; if it finds something partial, pin the parameters with `-E`.
- The flag might be in **just one channel** (e.g. only blue) or need more than 1 bit per pixel.
- If it's JPEG, skip pixel-LSB → the payload is in the DCT coefficients. See
  `jsteg-jpeg-dct-steganography` (jsteg / steghide / stegseek).
- The image can be a decoy: the flag may be in metadata/an embedded file (step 1), not in the LSB.

## Cross-reference

- `Manuals/LSB-Stego/3. Contexto para Claude.md`: zsteg/stegsolve in detail.
- `jsteg-jpeg-dct-steganography`: the JPEG/DCT path when the carrier is lossy.
- `file-carving-signature-repair`: appended-archive / polyglot carving (the `file`-lies + unzip case).

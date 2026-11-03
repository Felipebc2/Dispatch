---
id: lsb-image-steganography
category: CRYPTO
tags: [stego, steganography, lsb, least-significant-bit, png, bmp, zsteg, stegsolve, stegolsb, bit-plane, image]
tools: [LSB-Stego]
manuals: ["Manuals/LSB-Stego/3. Contexto para Claude.md"]
title: "LSB image steganography (zsteg / stegsolve)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: []
---

## How to recognize this pattern

- The attachment is a **lossless image** (PNG, BMP, GIF) with no obvious challenge — "just a photo".
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

## Gotchas

- Order matters: bit-plane (b1/b2...), channels (r/g/b/a), and scan order (xy vs yx). `zsteg -a`
  tests the combinations; if it finds something partial, pin the parameters with `-E`.
- The flag might be in **just one channel** (e.g. only blue) or need more than 1 bit per pixel.
- If it's JPEG, skip LSB → try `steghide extract` (uses a password; try empty / the one from the
  prompt) or `stegseek` with a wordlist.
- The image can be a decoy: the flag may be in metadata/an embedded file (step 1), not in the LSB.

## Cross-reference

- `Manuals/LSB-Stego/3. Contexto para Claude.md` — zsteg/stegsolve in detail.
- Embedded file / carving → FOR category (`pcap-extract-credentials-files` has the binwalk/foremost
  reflex).

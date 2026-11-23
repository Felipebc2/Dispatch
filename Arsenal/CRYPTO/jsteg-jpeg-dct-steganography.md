---
id: jsteg-jpeg-dct-steganography
category: CRYPTO
tags: [stego, steganography, jsteg, jpeg, dct, dct-coefficients, f5, outguess, steghide, jphide, lsb-dct, stegoveritas, frequency-domain]
tools: []
manuals: []
title: "JPEG DCT steganography: data in coefficient LSBs (jsteg / F5 / steghide), not pixels"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [lsb-image-steganography, file-carving-signature-repair]
---

## How to recognize this pattern

- The carrier is a **JPEG** (`.jpg`/`.jpeg`), and **pixel-LSB tools find nothing** — `zsteg` only works
  on lossless formats (PNG/BMP/GIF), because JPEG re-quantizes pixels on save. For JPEG the payload
  hides in the **DCT coefficients**, the frequency data JPEG uses to compress.
- Prompt hints: "compression", "coefficients", "discrete", a JPEG that's suspiciously large for its
  visual content, or the pixel-stego path explicitly failing.
- Which tool depends on the embedder: **jsteg** (LSB of AC coefficients), **F5** (matrix encoding,
  decrements magnitude), **steghide** (passphrase, JPEG+WAV+BMP), **outguess**, **jphide/jphs**.

## Method

### 1. Try the passphrase-based embedders first (most common in CTF)
```bash
steghide extract -sf photo.jpg -p ''            # empty passphrase first
steghide info photo.jpg                           # confirms steghide + whether a pass is set
stegseek photo.jpg /usr/share/wordlists/rockyou.txt   # fast steghide passphrase cracker
```
`stegseek` brute-forces steghide passphrases far faster than `stegcracker`; it's the go-to.

### 2. jsteg — LSB of non-0/1 AC coefficients
```bash
jsteg reveal photo.jpg -           # prints the hidden bytes to stdout
```
jsteg hides one bit in the LSB of each AC coefficient ≠ 0 and ≠ 1. No passphrase. If `jsteg` isn't
installed: `go install github.com/lukechampine/jsteg@latest`.

### 3. F5 and outguess
```bash
# F5 (needs the Java reference impl, often as f5.jar):
java -jar f5.jar x -e out.bin photo.jpg
outguess -r photo.jpg out.txt
```

### 4. Shotgun with stegoveritas / zsteg-for-jpeg
```bash
stegoveritas photo.jpg       # runs steghide/jsteg/exif/strings/colour-planes and dumps results
```
Also always check the cheap wins JPEG still allows: `exiftool photo.jpg` (metadata, see
`image-geolocation-exif`), `binwalk photo.jpg` and trailing bytes after the `FFD9` EOI marker
(appended archive — see `file-carving-signature-repair`), and `strings`.

## Gotchas

- **`zsteg` on a JPEG is a dead end** — it silently reports nothing useful. That false negative is the
  #1 time sink; switch to DCT tools the moment the carrier is JPEG.
- steghide **re-saves** the JPEG; if a challenge gives you a JPEG that was clearly re-encoded, steghide
  is the likely embedder. F5 **shrinks** coefficient magnitudes, detectable as a histogram shrinkage.
- Empty passphrase is extremely common — always try `-p ''` before cracking.
- Don't confuse DCT-LSB with pixel-LSB: converting the JPEG to PNG and running `zsteg` destroys the
  DCT payload. Work on the original JPEG bytes.
- Multiple layers happen: jsteg → base64 → zip. Pipe the extracted bytes through `file -` to see
  what came out before assuming it's the flag.

## Cross-reference

- `lsb-image-steganography`: the **pixel**-domain sibling (PNG/BMP, zsteg/stegsolve, PRNG-dispersed and
  appended-chunk variants).
- `file-carving-signature-repair`: JPEGs with an archive glued after the `FFD9` EOI marker.
- `image-geolocation-exif`: EXIF/metadata is a separate, cheaper hiding spot in the same JPEG.

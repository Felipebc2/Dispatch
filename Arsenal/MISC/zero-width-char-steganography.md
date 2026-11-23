---
id: zero-width-char-steganography
category: MISC
tags: [stego, steganography, zero-width, zero-width-space, unicode, u200b, u200c, u200d, ufeff, invisible-characters, text-stego, whitespace, binary-encoding, homoglyph]
tools: []
manuals: []
title: "Zero-width steganography: bits hidden in invisible Unicode between visible text"
difficulty: easy
created: 2026-11-23
updated: 2026-11-23
related: [encoding-chain-magic, lsb-image-steganography]
---

## How to recognize this pattern

- A plain `.txt`/message looks innocent but is **heavier than its visible text** (file size ≫ characters
  you can see), or copy-pastes with odd spacing. The payload is **invisible Unicode** interleaved
  between the visible glyphs.
- Common carriers: a note, a chat log, a README, a tweet, an email body. Prompt hints: "workspaces",
  "invisible", "espaces", "between the lines", "zero width".
- The hidden alphabet is usually two code points for bits `0`/`1`, sometimes more:
  `U+200B` (zero-width space), `U+200C` (zero-width non-joiner), `U+200D` (joiner), `U+FEFF` (BOM),
  `U+2060` (word joiner).

## Method

### 1. See the invisibles
```bash
# make every byte visible — zero-width chars show as UTF-8 escapes
python3 -c "print(open('note.txt','rb').read())"
# or hex view; U+200B = e2 80 8b, U+200C = e2 80 8c, U+200D = e2 80 8d, U+FEFF = ef bb bf
xxd note.txt | grep -E 'e280(8b|8c|8d)|efbb bf'
```
Count how many distinct zero-width code points appear — that tells you the encoding (2 = binary).

### 2. Map the two symbols to bits and decode
```python
t = open("note.txt", encoding="utf-8").read()
ZERO, ONE = "​", "‌"                 # adjust to the pair actually present
bits = "".join("0" if c == ZERO else "1" for c in t if c in (ZERO, ONE))
out = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits) - 7, 8))
print(out.decode("utf-8", "replace"))
```
If the result is garbage, swap `ZERO`/`ONE`, or try 7-bit groups, or reverse the bit order.

### 3. Other zero-width schemes
- **More than two symbols** → base-3/4 or a direct value map; list the distinct invisibles first.
- **Zero-width + visible** interleave carrying one bit per *gap* (presence/absence of a ZWSP between
  words).
- Online: paste into a "zero-width detector" / `330k/zwsp-steg` decoder as a fallback.

## Gotchas

- Editors and terminals **hide** these characters by design — never eyeball the file; always go through
  bytes/hex. Copy-pasting into a form often **strips** them, destroying the payload.
- `strings` drops them too (non-printable); use raw byte reads.
- `U+FEFF` at the very start is a legitimate BOM, not payload — don't count the leading one.
- Normalize carefully: `unicodedata.normalize("NFKC", ...)` **deletes** zero-width chars — never run it
  before extracting.
- Watch for a different-but-related trick: **whitespace stego** using ordinary spaces vs tabs
  (`snow`/stegsnow) at line ends — same idea, visible-range bytes.

## Cross-reference

- `encoding-chain-magic`: the decoded bits are often another layer (base64/hex) — chain decoders.
- `lsb-image-steganography`: the image-domain analogue of "data hidden in a channel you don't look at".

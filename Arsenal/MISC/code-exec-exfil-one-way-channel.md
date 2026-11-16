---
id: code-exec-exfil-one-way-channel
category: MISC
tags: [exfiltration, one-way-channel, screen, livestream, twitch, no-stdout, qr-code, render, zbarimg, reed-solomon, permissions, chmod, owner, video-channel]
tools: []
manuals: []
title: "Code exec with output only over a one-way channel (screen/livestream)"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [setuid-path-hijack-relative-command, format-string-leak-write]
---

## How to recognize this pattern

- You are **handed arbitrary code execution** (submit a binary/script that runs on a box), but there is
  **no stdout back** — the only output is a **screen captured on a livestream** (Twitch/OBS) or a
  similar one-way medium. The puzzle is not a memory bug; it is *exfiltrating a file over video*.
- The flag is read-blocked by a twist: a `----------` file you nonetheless **own** (owner can `chmod`
  its own file), or a file owned by another service you reach via a setuid helper, or a **QR-code PNG**
  instead of text.

## Method

### 1. Recon via the only channel
Write findings to a file and open it in a **window that stays up** past the box's reset (~115 s of a
120 s TTL). For long dumps use an **auto-paging xterm** (mapfile the file, print ~40-line pages,
`sleep`, loop) since a one-way video can't scroll.
```c
system("{ id; ls -la /target; } > /tmp/o.txt 2>&1; "
       "xterm -fa Monospace -fs 22 -e 'cat /tmp/o.txt; sleep 115' & sleep 115");
```

### 2. Get the secret readable, then render it
- Owner of a `----------` file → `chmod u+r` it (chmod is gated by ownership, not the mode bits), then `cat`.
- Flag owned by another user → reach it through a setuid helper (see cross-ref).
- Flag is a **QR PNG** → copy it out, upscale nearest-neighbor (`convert -filter point`), show it
  **centered with a wide white quiet-zone border** (`-bordercolor white -border 160`) via `feh -F`.

### 3. Read it off the stream
Text: read directly. QR: scan with `zbarimg`/ZXing; if the player's control bar clips the bottom rows,
the centered+quiet-zone render clears the UI, and a clipped grid is still recoverable via Reed-Solomon.

## Gotchas

- **Test both forms in one run.** Flags in such a series alternate between **text** and **QR PNG** — do
  `file`/`ls`, then `cat` *and* render-as-image in the same submission; each target run costs ~120 s, so
  don't waste one assuming the wrong format.
- The streamed screen is the exfil — account for stream **delay** (hold the window long enough) and the
  **player UI** clipping the image (center it, add a quiet zone).
- Only ever read/copy **your own** flag file; never touch other teams'.
- A target may not exist until the organizers activate it (a root-owned list materializes dirs) — wait
  for activation, don't try to force a root-only write.

## Cross-reference

- `setuid-path-hijack-relative-command`: reach a flag owned by another user/service.
- `format-string-leak-write`: leak a flag already loaded in a setuid helper's memory (`%N$s`).

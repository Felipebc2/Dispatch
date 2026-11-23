---
id: audio-spectrogram-steganography
category: MISC
tags: [stego, steganography, audio, spectrogram, wav, sox, audacity, sonic-visualiser, frequency-domain, spectrum, dtmf, sstv, text-in-spectrogram]
tools: []
manuals: []
title: "Spectrogram steganography: text drawn in an audio file's frequency view"
difficulty: easy
created: 2026-11-23
updated: 2026-11-23
related: [afsk-bell202-audio-demodulation, voip-rtp-dtmf-extraction, lsb-image-steganography]
---

## How to recognize this pattern

- You get an audio file (`.wav`, `.mp3`, `.ogg`, `.flac`) that sounds like **noise, static, a whine, or
  a short screech** — nothing intelligible. The message isn't in the *sound*, it's **drawn in the
  spectrogram** (frequency vs time), so the flag is literally written across the frequency axis.
- Prompt hints: "hidden frequency", "listen closely", "spectre", "fréquence cachée", a waveform that's
  visually flat but spectrally busy.
- Distinguish from other audio tricks: tones = DTMF/modem (see cross-refs); a readable image = this.

## Method

### 1. Render the spectrogram
```bash
sox message.wav -n spectrogram -o spectro.png      # SoX: fast, scriptable
```
Open `spectro.png`; the flag text appears as drawn glyphs. If it's cramped, widen/extend:
```bash
sox message.wav -n spectrogram -x 2000 -y 1025 -o spectro.png   # more pixels
```

### 2. Interactive tools (better for faint or scrolling text)
- **Audacity**: open file → track dropdown → *Spectrogram* view; tune the window size and frequency
  range (Spectrogram Settings) until letters sharpen.
- **Sonic Visualiser**: add a *Spectrogram* layer; adjust scale (log), colour and window — best for
  low-contrast or wide-band hides.

### 3. Dig deeper if the plain spectrogram is empty
- Message may sit in a **narrow band** — zoom the frequency range (`-y`), or high/low-pass first:
  `sox in.wav out.wav highpass 1000`.
- Check **stereo channels separately** (`remix 1`, `remix 2`) and the **difference** of L−R.
- Reverse/speed changes: `sox in.wav out.wav reverse`.
- Also run the orthogonal audio checks: `steghide extract -sf file.wav` (steghide does WAV),
  LSB of samples, and `binwalk`/trailing bytes.

## Gotchas

- MP3/OGG re-encoding can blur faint spectrogram text — if given a lossy file, push contrast and window
  size; if given both WAV and MP3, work the WAV.
- Default SoX spectrogram size is small; low-res makes letters unreadable — always bump `-x`/`-y` before
  concluding it's empty.
- Text can be **upside down or mirrored** depending on how it was embedded; try `reverse` and flip the
  PNG.
- Don't confuse with **SSTV** (an image encoded as audio) — if the spectrogram shows scanlines rather
  than text, decode with `qsstv`.

## Cross-reference

- `afsk-bell202-audio-demodulation`: when the audio is a **modem tone** carrying data, not a drawn image.
- `voip-rtp-dtmf-extraction`: when the audio is **DTMF** key tones to decode into digits.
- `lsb-image-steganography`: the image-domain sibling once you've rendered a picture out of the audio.

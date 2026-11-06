---
id: afsk-bell202-audio-demodulation
category: MISC
tags: [audio, wav, signal, afsk, fsk, bell-202, bell202, 1200-baud, mark-space, 1200hz, 2200hz, modem, minimodem, multimon-ng, ax25, aprs, packet-radio, goertzel, spectrogram, sox, 8n1, uart]
tools: [Audio-Signals]
manuals: ["Manuals/Audio-Signals/3. Contexto para Claude.md"]
title: "Audio: demodulate an AFSK (Bell 202, 1200 baud) data burst hidden in a WAV"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [encoding-chain-magic]
---

## How to recognize this pattern

- A WAV/audio file with a short screechy or noise-like burst, often after speech or music.
- Hints: "tones", "modem", "radio", "packet", "pager", "1200".
- Spectrogram shows **two alternating tones**: 1200 Hz (mark, 1) and 2200 Hz (space, 0) at
  1200 baud = Bell 202 (also APRS / AX.25 and caller ID). Bell 103 is 300 baud with
  1070/1270 Hz and 2025/2225 Hz pairs.

## Method

### 1. Locate and measure the burst
```bash
sox in.wav -n spectrogram -o spec.png            # find start/end time and the two tones
sox in.wav -n stat                                # rate, length
sox in.wav burst.wav trim 9.7 0.8                 # cut start,length seconds
```
Symbol length in samples = sample_rate / baud (48000 / 1200 = 40).

### 2. Ready-made decoders
```bash
minimodem --rx -f burst.wav 1200                  # Bell 202, async 8N1 bytes (also: 300 = Bell 103)
sox burst.wav -t raw -r 22050 -e signed -b 16 -c 1 burst.raw
multimon-ng -t raw -a AFSK1200 burst.raw          # expects AX.25/APRS framing (NRZI, HDLC)
```
If `minimodem` prints garbage and `multimon-ng` prints nothing, decode by hand (below).

### 3. Hand demodulator (numpy + scipy)
```python
import sys, numpy as np
from scipy.io import wavfile
sr, x = wavfile.read(sys.argv[1]); x = x.astype(float)
x = x[:, 0] if x.ndim > 1 else x
t0 = int(float(sys.argv[2]) * sr) if len(sys.argv) > 2 else 0       # skip speech before the burst
start = t0 + int(np.argmax(np.abs(x[t0:]) > 0.1 * np.abs(x[t0:]).max()))
BAUD, MARK, SPACE = 1200, 1200, 2200
spb = sr / BAUD; t = np.arange(int(round(spb))) / sr
e = lambda s, f: abs(np.dot(s, np.exp(-2j * np.pi * f * t[:len(s)])))  # single-bin DFT
bits, k = [], 0
while start + (k + 1) * spb <= len(x):
    s = x[int(start + k * spb):int(start + (k + 1) * spb)]
    bits.append(1 if e(s, MARK) > e(s, SPACE) else 0); k += 1
out, i = bytearray(), 0                                # async 8N1: 0, 8 data bits LSB first, 1
while i + 10 <= len(bits):
    if bits[i] == 0 and bits[i + 9] == 1:
        out.append(int(''.join(map(str, bits[i + 1:i + 9][::-1])), 2)); i += 10
    else:
        i += 1
print(out)
```
Run: `python3 solve.py in.wav 9.5`.

## Gotchas

- Leading `0xFF` bytes are the idle-mark preamble, not data.
- Garbage output: try MSB-first, swap mark/space (inverted), or NRZI (bit = 1 if no tone change).
  AX.25 also uses bit stuffing (drop a 0 after five 1s) and HDLC `0x7E` flags.
- Long bursts drift: resync on each start bit (the scanner above does), or use a sample rate that is a
  multiple of the baud.
- Metadata (`LIST/INFO` `ICMT` chunk, `strings -n 8 in.wav`) and the spoken text often carry a
  consistent decoy; the modem layer is the authoritative one when the prompt mentions tones.
- NOT this pattern: DTMF (two tones **simultaneously**, short beeps: `multimon-ng -a DTMF`), SSTV
  (image, 1200 Hz sync plus 1500 to 2300 Hz sweep: `qsstv`), Morse (one tone on/off), RTTY
  (45.45 baud, 170 Hz shift), spectrogram-drawn text (just look at `spec.png`).
- After decoding, the payload may still be encoded: see `encoding-chain-magic`.

## Cross-reference

`encoding-chain-magic` for layered payload decoding after demodulation.

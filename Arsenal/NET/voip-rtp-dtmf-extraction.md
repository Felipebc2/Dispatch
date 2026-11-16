---
id: voip-rtp-dtmf-extraction
category: NET
tags: [voip, rtp, g711, pcmu, ulaw, dtmf, pcap, tshark, force-dissector, sox, spectrogram, zip-password, john, mask, no-sip]
tools: [Wireshark, Audio-Signals, Hash-Cracking]
manuals: ["Manuals/Wireshark/3. Contexto para Claude.md", "Manuals/Audio-Signals/3. Contexto para Claude.md", "Manuals/Hash-Cracking/3. Contexto para Claude.md"]
title: "VoIP in a pcap: RTP/G.711 → DTMF tones → password/secret"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [pcap-extract-credentials-files, afsk-bell202-audio-demodulation]
---

## How to recognize this pattern

- A pcap mixing HTTP flavor with a block of **undissected UDP** (Wireshark shows it as `data`). The
  payload starts `80 00 ...` (RTP v2, PT=0 = G.711 µ-law/PCMU), timestamp `+160`/packet (20 ms @ 8 kHz),
  and there is **no SIP/SDP** signaling, so Wireshark doesn't auto-recognize it as a call.
- The decoded audio is a sequence of **tone-pair beeps** (DTMF) that dictate a password, PIN or code —
  often the key to a password-protected zip/doc served over the HTTP side.

## Method

### 1. Force the RTP dissector and confirm the stream
```bash
tshark -r cap.pcap -d udp.port==5004,rtp -q -z rtp,streams    # SSRC, codec g711U, Lost 0%
```

### 2. Extract the RTP payload in order and decode µ-law to PCM
```bash
tshark -r cap.pcap -d udp.port==5004,rtp -Y rtp -T fields -e rtp.payload \
  | tr -d ':\n' | python3 -c 'import sys,binascii;sys.stdout.buffer.write(binascii.unhexlify(sys.stdin.read().strip()))' > call.ul
sox -t ul -r 8000 -c 1 call.ul -e signed -b 16 call_pcm.wav
sox call_pcm.wav -n spectrogram -o spec.png     # count the tone bursts, see the pairs
```

### 3. Read the DTMF, then crack what it protects
FFT each burst and snap the two frequencies to the DTMF grid (`697/770/852/941` × `1209/1336/1477`).
If some tones are **off-grid/ambiguous**, anchor the digits you *do* read and brute the gap with a mask:
```bash
zip2john backup.zip > h.txt
john --mask='482951?d?d?d?d4' h.txt      # known digits fixed, brute the ambiguous middle
```
Open with the recovered password and read the flag from the inner document.

## Gotchas

- No SIP/SDP is normal for these — the stream is pure RTP, so you must **force** `udp.port==N,rtp`.
- Keep packets in **sequence order** before concatenating µ-law bytes, or the audio garbles.
- Off-grid middle tones (~430/1010 Hz) can't be snapped by a naive decoder — don't try to decode them
  perfectly; anchor the clean digits and brute the few unknowns (ZipCrypto cracks in seconds).
- `multimon-ng -a DTMF` on the WAV is a faster first pass than hand-FFT when all tones are on-grid.
- The HTTP side (SVG icons, empty paginated JSON) is usually noise; the audio is the payload.

## Cross-reference

- `Manuals/Wireshark`: forcing dissectors, `-z rtp,streams`, exporting objects.
- `Manuals/Audio-Signals`: spectrogram reading and DTMF decoding (sox, multimon-ng, Audacity).
- `Manuals/Hash-Cracking`: `zip2john` + mask attacks for the anchored brute.
- `pcap-extract-credentials-files`: carving the file the password unlocks from the same pcap.

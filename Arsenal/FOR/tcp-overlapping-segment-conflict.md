---
id: tcp-overlapping-segment-conflict
category: FOR
tags: [forensics, pcap, tshark, wireshark, tcp, tcp-overlap, overlapping-segments, same-seq, sequence-number, retransmission, suspected-retransmission, reassembly, follow-stream, conflicting-data, ids-evasion, tcp-payload]
tools: [Wireshark]
manuals: ["Manuals/Wireshark/3. Contexto para Claude.md"]
title: "PCAP: overlapping TCP segments (same seq, different bytes) hidden by stream reassembly"
difficulty: hard
created: 2026-11-06
updated: 2026-11-06
related: [pcap-extract-credentials-files, large-artifact-gigabyte-triage]
---

## How to recognize this pattern

- Follow TCP Stream / Export Objects show a plausible answer, but the flag is rejected.
- Wireshark labels a segment `TCP Retransmission` / `Spurious Retransmission` on a stream that looks
  otherwise healthy, especially with a tiny gap (about 1 ms) after the original.
- The question hints at "the second copy", "what was really sent", "the version the server saw".
- A real retransmission repeats the **same bytes**. Same `seq` (or an overlapping range) with
  **different bytes** is the planted conflict: reassembly keeps one copy (usually the first) and hides
  the other.

## Method

### 1. Let Wireshark flag the conflicts
```bash
tshark -r cap.pcap -Y 'tcp.analysis.retransmission || tcp.analysis.spurious_retransmission || tcp.analysis.out_of_order' \
       -T fields -e frame.number -e tcp.stream -e tcp.seq -e tcp.len | head
tshark -r cap.pcap -Y 'tcp.segment.overlap.conflict' -T fields -e frame.number -e tcp.stream   # only when reassembly ran
```

### 2. Dump every segment and compare payloads per (stream, seq)
```bash
tshark -r cap.pcap -Y 'tcp.len>0' -T fields -e frame.number -e tcp.stream -e tcp.seq_raw -e tcp.payload > seg.tsv
```
```python
import hashlib, sys
first = {}
for line in open(sys.argv[1]):
    fr, st, seq, data = line.rstrip('\n').split('\t')
    key, h = (st, seq), hashlib.md5(data.encode()).digest()
    if key in first and first[key][1] != h:
        print(f'stream {st} seq {seq}: frame {first[key][0]} vs {fr} differ')
    first.setdefault(key, (fr, h))
```
Then print both sides:
```bash
tshark -r cap.pcap -Y 'frame.number in {A B}' -T fields -e frame.number -e tcp.payload \
  | while read n p; do echo "$n: $(echo "$p" | xxd -r -p | tr -c '[:print:]\n' '.')"; done
```

### 3. Partial overlaps
Same-seq checks miss a segment that starts inside an earlier one. Per stream, sort by `seq_raw` and
compare the overlapping byte range of `[seq, seq+len)` intervals instead of whole payloads.

## Gotchas

- Port reuse across many short connections makes Wireshark merge them or raise lots of "suspected
  retransmission" noise. The label alone means nothing; only differing bytes matter. Split on SYN if
  `tcp.stream` merges distinct connections.
- Use `tcp.seq_raw` (or `-o tcp.relative_sequence_numbers:FALSE`) when comparing across tools.
- Flags may be split between both copies: one field from the first-received copy, another from the
  conflicting one. Read the question clause by clause.
- Reassembly policy differs by OS and IDS (first-wins vs last-wins); that is exactly the evasion
  trick. The IP-layer analog is `ip.fragment.overlap.conflict`.
- On a 1 GB capture, run one field dump to TSV and work on that; avoid repeated full tshark passes.
- NOT this pattern: identical duplicate payloads (a real retransmission, or a mirrored capture point).

## Cross-reference

`Manuals/Wireshark/3. Contexto para Claude.md` (filters, field export); `pcap-extract-credentials-files`
for the general pcap sweep; `large-artifact-gigabyte-triage` for raw pcap walking at scale.

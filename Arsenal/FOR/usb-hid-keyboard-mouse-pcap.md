---
id: usb-hid-keyboard-mouse-pcap
category: FOR
tags: [forensics, pcap, pcapng, usb, usbpcap, usbmon, hid, keyboard, keystrokes, keylogger, mouse, tablet, usb-capdata, usbhid-data, scancode, tshark]
tools: [Wireshark]
manuals: ["Manuals/Wireshark/3. Contexto para Claude.md"]
title: "USB HID capture: rebuild typed keystrokes or the mouse drawing from usb.capdata"
difficulty: easy
created: 2026-11-17
updated: 2026-11-17
related: [pcap-extract-credentials-files, large-artifact-gigabyte-triage]
---

## How to recognize this pattern

- A pcap/pcapng with no IP traffic: protocol hierarchy shows only `usb` / `usbhid`
  (captured with USBPcap on Windows or usbmon on Linux).
- Lots of tiny interrupt-IN packets (`URB_INTERRUPT in`) carrying 4 to 9 data bytes.
- The story says "someone typed the password", "a keylogger", "they drew the flag".

## Method

### 1. Find the HID device and its report size
```bash
tshark -r c.pcap -q -z io,phs
tshark -r c.pcap -Y 'usb.bInterfaceClass == 3' -T fields -e usb.src -e usb.bInterfaceProtocol   # 1=keyboard 2=mouse
tshark -r c.pcap -Y 'usb.data_len > 0' -T fields -e usb.src -e usb.data_len | sort | uniq -c | sort -rn
```
8 bytes from one endpoint = boot keyboard; 3 to 8 bytes = mouse; a large odd size = tablet/gamepad.

### 2. Dump the reports
```bash
tshark -r c.pcap -Y 'usb.src == "1.5.1" && usb.data_len > 0' \
       -T fields -e usb.capdata -e usbhid.data | tr -d '\t' > hid.txt
```
Newer Wireshark puts the bytes in `usbhid.data`, older in `usb.capdata`; dumping both covers either.

### 3a. Keyboard: byte 0 = modifiers, bytes 2..7 = keycodes (HID Usage Table)
```python
import sys
K = dict(zip(range(4, 40), 'abcdefghijklmnopqrstuvwxyz1234567890'))
K.update({0x28: '\n', 0x2b: '\t', 0x2c: ' ', 0x2d: '-', 0x2e: '=', 0x2f: '[', 0x30: ']',
          0x31: '\\', 0x33: ';', 0x34: "'", 0x35: '`', 0x36: ',', 0x37: '.', 0x38: '/'})
S = dict(zip("1234567890-=[];'`,./\\", '!@#$%^&*()_+{}:"~<>?|'))
out, prev, caps = [], set(), False
for line in sys.stdin:
    b = bytes.fromhex(line.strip().replace(':', ''))
    if len(b) == 9: b = b[1:]                    # leading report ID
    if len(b) != 8: continue
    keys = [k for k in b[2:] if k]
    for k in keys:
        if k in prev: continue                   # still held from the previous report
        if k == 0x2a: out and out.pop(); continue          # Backspace
        if k == 0x39: caps = not caps; continue            # Caps Lock
        c = K.get(k, f'<{k:#04x}>')              # arrows/F-keys stay visible as <0x50>
        shift = bool(b[0] & 0x22)                # LShift 0x02, RShift 0x20
        c = (c.upper() if shift ^ caps else c) if c.isalpha() else (S.get(c, c) if shift else c)
        out.append(c)
    prev = set(keys)
print(''.join(out))
```
`python3 kbd.py < hid.txt`

### 3b. Mouse: byte 0 = buttons, byte 1 = dx, byte 2 = dy (signed int8); plot pen-down points
```python
import sys
x = y = 0; pts = set()
for line in sys.stdin:
    b = bytes.fromhex(line.strip().replace(':', ''))
    if len(b) < 3: continue
    x += int.from_bytes(b[1:2], 'little', signed=True)
    y += int.from_bytes(b[2:3], 'little', signed=True)
    if b[0] & 1: pts.add((x, y))                 # left button held = pen down
SX, SY = int(sys.argv[1]) if len(sys.argv) > 1 else 4, int(sys.argv[2]) if len(sys.argv) > 2 else 8
cells = {(px // SX, py // SY) for px, py in pts}
xs, ys = [c[0] for c in cells], [c[1] for c in cells]
for row in range(min(ys), max(ys) + 1):
    print(''.join('#' if (col, row) in cells else ' ' for col in range(min(xs), max(xs) + 1)))
```
`python3 mouse.py 4 8 < hid.txt` prints the drawing as ASCII; tune the X/Y scale until it reads.

## Gotchas

- Held keys repeat in every report until released: emit only keys not present in the previous
  report, or you get `ffffllaagg`.
- Arrow keys (`0x4f`-`0x52`), Home/End and Delete move the cursor; when `<0x50>` shows up, replay
  the edits by hand instead of trusting the linear string.
- Non-US layouts (AZERTY, ABNT2) map the same keycodes to different symbols: if the text is almost
  readable, remap with the target layout.
- Mouse layouts vary: a leading report-ID byte shifts everything by one; 6 to 8 byte reports often use
  16-bit little-endian deltas (`b[1:3]`, `b[3:5]`). Try the variants and check which one draws text.
- Nothing drawn with button 1? Try right button (`& 2`), or plot every point and look for the
  shape. If the result is mirrored, negate `y`.
- Tablets (Wacom etc.) send absolute X/Y (16-bit LE) plus pressure: plot points where pressure > 0.
- Several HID devices in one capture: filter by `usb.src` per device, never mix their reports.

## Cross-reference

Network pcaps: `pcap-extract-credentials-files`. Tshark field export:
`Manuals/Wireshark/3. Contexto para Claude.md`.

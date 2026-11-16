---
id: office-maldoc-vba-static-extraction
category: FOR
tags: [maldoc, office, vba, macro, olevba, oletools, xls, xlsm, docm, chr-obfuscation, static-analysis, ole, no-execute, ftp-carve]
tools: []
manuals: []
title: "Office maldoc: extract the VBA macro statically (olevba), never run it"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [pcap-extract-credentials-files, file-carving-signature-repair]
---

## How to recognize this pattern

- You recover an Office file (`.xls/.xlsm/.doc/.docm`) — often **carved from a pcap** (FTP/HTTP) or
  handed directly — and the prompt talks about a report, a spreadsheet, a "reconciliation", or asks
  you to run a routine before closing the books.
- `file x.xls` → `Composite Document File V2` (OLE) or a ZIP (`.xlsm/.docx`). The flag is built by the
  **macro**, commonly a function that concatenates `Chr()` calls.

## Method

### 1. Carve the file first if it came over the wire
```bash
tshark -r cap.pcap -q --export-objects ftp-data,out/    # or http,out/
file out/*.xls
```

### 2. Dump the macro statically — do not open in Office
```bash
olevba --decode out/report.xls > vba.txt      # oletools; shows all VBA modules + decoded strings
```
Read the routines; the flag is usually in an obfuscated helper:
```vb
Public Function CodigoDeValidacao() As String
    CodigoDeValidacao = Chr(73) & Chr(68) & Chr(80) & Chr(123) & ...
End Function
```

### 3. Decode without executing
```bash
python3 -I -c "import re;s=open('vba.txt').read();b=s[s.find('CodigoDeValidacao'):s.find('End Function',s.find('CodigoDeValidacao'))];print(''.join(chr(int(n)) for n in re.findall(r'Chr\((\d+)\)',b)))"
```

## Gotchas

- **Never run the macro** (no Office, no `AutoOpen`): static extraction is both safer and enough —
  the flag string is literal in the source.
- Use `xlrd`/`openpyxl` to read cell values without triggering macros if the sheet data matters; the
  prompt's "the numbers don't add up" is usually misdirection pointing you *to* the macro, not a
  computation you must reproduce.
- `olevba --decode` already resolves common obfuscation (Chr, StrReverse, hex); for custom schemes,
  lift the algorithm and reimplement it in Python.
- `oledump.py -s <stream> -v` is the alternative when `olevba` chokes on a malformed stream.
- The author/path often leaks in the OLE metadata (`strings`, `exiftool`) — handy for pivoting.

## Cross-reference

- `pcap-extract-credentials-files`: carving the maldoc out of the capture in the first place.
- `file-carving-signature-repair`: when the OLE/ZIP header is damaged and needs repair before parsing.

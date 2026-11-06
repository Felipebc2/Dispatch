---
id: wasm-module-static-analysis
category: REV
tags: [wasm, webassembly, wat, wabt, wasm2wat, wasm-objdump, wasm-decompile, wasm2c, wasm-tools, wasmtime, node, webassembly-instantiate, data-segment, linear-memory, exports, imports, leb128, i32, select, emscripten, rust-wasm, ghidra-wasm, decoy]
tools: [WebAssembly, chrome-devtools]
manuals: ["Manuals/WebAssembly/3. Contexto para Claude.md", "Manuals/chrome-devtools/3. Contexto para Claude.md"]
title: "REV: WebAssembly (.wasm) module analysis (exports, data segment, local instantiate)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [static-triage-strings-ltrace, flag-check-reverse-transform, decoy-vs-real-checker-what-actually-runs]
---

## How to recognize this pattern

- Attachment starts with `00 61 73 6d 01 00 00 00` (`\0asm`, version 1), or a web challenge
  loads `*.wasm` / has a base64 blob passed to `WebAssembly.instantiate`.
- `strings` shows export names (`check`, `verify`, `get_*`) and a data string.
- Typical trap: one export returns the obvious ("posted"/decoy) value, the real answers come
  from other exports that filter records in the data segment.

## Method

### 1. Structure first
```bash
wasm-objdump -x chall.wasm            # sections, imports, exports, data segments + offsets
wasm-objdump -s -j Data chall.wasm    # raw data segment (records, strings)
wasm2wat chall.wasm -o chall.wat      # full text format
wasm-decompile chall.wasm -o chall.dcmp   # C-like pseudocode, easiest to read
```
Bigger modules (Rust/Emscripten/Go): `wasm2c` then compile/read C, or Ghidra with the
`ghidra-wasm-plugin`. Start from the exports, not from `_start`.

### 2. Just call the exports (no imports = safe to instantiate)
```bash
node -e '
const m = new WebAssembly.Module(require("fs").readFileSync(process.argv[1]));
console.log("imports", WebAssembly.Module.imports(m), "exports", WebAssembly.Module.exports(m));
const i = new WebAssembly.Instance(m, {});
for (const [k, f] of Object.entries(i.exports)) if (typeof f === "function" && f.length === 0) console.log(k, f());
' chall.wasm
```
With imports: stub them (`{env: {print: x => console.log(x), memory: new WebAssembly.Memory({initial: 1})}}`).
Python alternative: `pip install wasmtime`.

### 3. No wabt: walk sections by hand
```python
d = open('chall.wasm', 'rb').read(); assert d[:4] == b'\0asm'
def leb(p):
    v = s = 0
    while True:
        b = d[p]; p += 1; v |= (b & 0x7f) << s; s += 7
        if b < 0x80: return v, p
i = 8
while i < len(d):
    sid = d[i]; size, body = leb(i + 1)
    print('section', sid, 'size', size, 'at', hex(body))   # 2=import 7=export 10=code 11=data
    i = body + size
```
Data segment (MVP, active, memory 0): `count, 0x00, i32.const <off> (41 xx), end (0b), len, bytes`.
Map the bytes to memory address `off`, then apply the filter you read from the code.

## Gotchas

- **Every size/index is LEB128**: a section of 0x80+ bytes has a 2-byte size (`91 02` = 273).
  A "1-byte size" walker silently breaks before reaching the data section.
- `select(a, b, cond)` returns `a` when `cond != 0`. Unrolled loops of `select` + `i32.add`
  are a count/sum over records.
- `i32.load8_u offset=N` adds the static `offset` to the address on the stack.
- A `start` function or an init export can rewrite memory before the checks: reading the static
  data segment alone may be stale; instantiating settles it.
- `i32` results from Node are signed; `>>> 0` for unsigned.
- NOT purely a REV task if the wasm comes from a web page and the flag is validated
  server-side: then grab the request in DevTools (`Manuals/chrome-devtools/3. Contexto para Claude.md`).

## Cross-reference

- `static-triage-strings-ltrace`: same first-pass mindset (strings, then structure).
- `flag-check-reverse-transform`: when an export checks input through an invertible transform.
- `Manuals/chrome-devtools/3. Contexto para Claude.md`: debugging wasm loaded by a web page.

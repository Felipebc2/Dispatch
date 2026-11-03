---
id: pyc-bytecode-decompile
category: REV
tags: [pyc, python-bytecode, bytecode, pyinstaller, decompile, decompyle3, uncompyle6, pycdc, pydisasm, marshal, magic]
tools: []
manuals: []
title: "REV — decompile Python bytecode (.pyc / PyInstaller)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [static-triage-strings-ltrace]
---

## How to recognize this pattern

- A `.pyc` attachment, or a large ELF/EXE where `strings` shows `PyInstaller`, `python3X`,
  `_MEIPASS`, `.py` module names. It's not a native binary — it's packaged Python.
- `file` says "data" on a small file whose start looks like magic bytes + a timestamp.

## Method

### 1. PyInstaller → extract the .pyc
```bash
python3 pyinstxtractor.py ./chall         # produces chall_extracted/
# the logic is in the .pyc named after the main script (no .py extension in the listing)
```

### 2. Fix the header (if extracted without magic)
The `.pyc` needs a valid header (version magic + flags + timestamp). Copy the first bytes from a
known module's `.pyc` (e.g. `struct.pyc`) of the same Python version if the decompiler complains
about the magic.

### 3. Decompile
```bash
decompyle3 file.pyc             # Python 3.7–3.8
# Python 3.9+: pycdc (C++, handles newer versions)
pycdc file.pyc                  # approximate source
pycdas file.pyc                 # bytecode disassembly (always works, even without source)
```

### 4. If the decompiler fails (version too new)
Read the **disassembly** directly — the flag/logic shows up in the constants:
```bash
python3 -c "import dis,marshal,importlib.util as u; \
f=open('file.pyc','rb'); f.read(16); \
dis.dis(marshal.load(f))"
# or extract just the constants (co_consts) where the flag is usually hardcoded
```

## Gotchas

- Matching the **decompiler version to the Python version** that produced the `.pyc` is the most
  annoying part: `decompyle3`/`uncompyle6` cover up to ~3.8; from 3.9 onward use `pycdc`.
- Always have the **disassembly** (`pycdas`/`dis`) as a fallback — it never fails, even when source
  decompilation breaks, and the flag is often raw in `co_consts`.
- PyInstaller: the main file usually has no header magic after extraction — step 2 fixes that.
- If it's `.pyo`/optimized or obfuscated (pyarmor), direct decompilation fails — then it's
  disassembly + reading by hand, or running it in a sandbox and inspecting.

## Cross-reference

- `static-triage-strings-ltrace` — `strings` on the EXE is what reveals it's PyInstaller.

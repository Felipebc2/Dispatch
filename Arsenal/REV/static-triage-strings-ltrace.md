---
id: static-triage-strings-ltrace
category: REV
tags: [strings, ltrace, strace, triage, triagem, hardcoded-flag, strcmp, nm, objdump, file, quick-win]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: static triage (quick wins before decompiling)"
difficulty: easy
created: 2026-10-04
updated: 2026-10-04
related: [flag-check-reverse-transform]
---

## How to recognize this pattern

- Any REV binary. **This is always the first step**: half of the easy REVs die here, without ever
  opening Ghidra. Only escalate to decompilation if triage comes up empty.

## Method

### 1. What the file is
```bash
file ./chall                      # ELF/PE, 32/64, stripped?, interpreter
```

### 2. Flag/secret in plaintext
```bash
strings -n 6 ./chall | grep -iE 'hik_|flag|ctf|secret'
strings -e l ./chall              # UTF-16 strings (common in Windows binaries)
```

### 3. Input comparison at runtime (without reading assembly)
```bash
ltrace ./chall                    # watch strcmp/strncmp/memcmp; the flag often shows up as the 2nd arg
# type a guess; if it calls strcmp("guess","REAL_FLAG") the flag leaks in the trace
strace -f ./chall 2>&1 | grep -iE 'open|read'   # which file does it read? (flag in an external file)
```

### 4. Symbols / quick flow
```bash
nm ./chall 2>/dev/null | grep -iE 'win|flag|check|secret'   # suspicious functions (if not stripped)
objdump -d -M intel ./chall | less                          # quick flow, no GUI
```

### 5. Only then: decompile
If nothing above delivered, now open it in Ghidra (see the Manual) and read the logic: the flag is
probably computed/transformed (see `flag-check-reverse-transform`).

## Gotchas

- A **stripped** binary kills `nm` and function names, but `strings`/`ltrace` still apply.
- If statically linked, `ltrace` may not catch the libc calls (no PLT), so fall back to
  `strace`/Ghidra.
- `ltrace` won't run on a different-architecture binary without `qemu-user`; and it can be useless if
  the check is inline (no strcmp call), and then it's Ghidra.
- **Be careful running an unknown binary**: even in an authorized CTF, run it in a disposable
  directory; `strace` reveals whether it touches the network/files before you trust it.

## Cross-reference

- `flag-check-reverse-transform`: when the flag is transformed and checked, not hardcoded.
- `Manuals/Ghidra/3. Contexto para Claude.md`: assisted decompilation when triage isn't enough.
- `.pyc`/PyInstaller → `pyc-bytecode-decompile` (not a native binary).

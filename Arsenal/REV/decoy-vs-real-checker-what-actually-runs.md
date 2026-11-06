---
id: decoy-vs-real-checker-what-actually-runs
category: REV
tags: [decoy, decoy-build, two-builds, posted-build, bindiff, init-array, preinit-array, ctors, constructor, attribute-constructor, before-main, go-init, main-init, shared-library, soname, needed, runpath, rpath, origin, ld-library-path, ld-preload, readelf, ldd, ld-debug, tls-callback, which-binary-runs]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: decoy vs real checker (which build, library or pre-main constructor actually runs)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [hidden-check-off-main-path, self-modifying-code-mprotect-xor-decrypt, static-triage-strings-ltrace, flag-check-reverse-transform]
---

## How to recognize this pattern

- Several attachments that look alike: two builds of "the same" program, a binary plus two
  `.so` files exporting the same symbol, a "posted" build whose banner spells out every answer.
- Prompt/hint wording: "the build that runs", "the library it is linked against", "a constructor
  runs before the prompt", "init installs the checker", "the posted comparison is the other one".
- Strings carry a ready-made answer (`Posted ... Boat X. Total 240.`) that is too convenient.

## Method: answer "what code executes?" before reversing anything

### A. Two builds of the same program
```bash
sha256sum build*; cmp -l build1 build2 | wc -l          # how much differs
strings -n 5 build1 > a; strings -n 5 build2 > b; diff a b
objdump -d -M intel build1 > a.s; objdump -d -M intel build2 > b.s; diff a.s b.s | head -80
```
- Reverse the build the prompt names as the real one (e.g. the "desk"/internal build), not the one
  whose banner states the parameters. Same data table, different constants and filters
  (divisor, skipped records, kind byte) is typical.
- Verify any banner value against what the code computes: a banner total that the code does not
  produce is a decoy.

### B. Which shared library is actually loaded
```bash
readelf -d ./main | grep -E 'NEEDED|RPATH|RUNPATH'       # soname wanted + search path
readelf -d lib*.so* | grep SONAME                         # which file carries that soname
LD_DEBUG=libs ./main 2>&1 | grep -E 'trying|calling init'  # loader's real choice (sandbox)
ldd ./main
```
- The loader matches the `NEEDED` soname (e.g. `libx.so.1`), resolved via `RUNPATH`/`RPATH`
  (`$ORIGIN` = binary's own dir), `LD_LIBRARY_PATH`, then system paths. A `libx.so` with the same
  exported symbols is never loaded: it is the decoy.
- Reverse the exported function in the loaded library only; answers are whatever it fills in.

### C. Checker installed before `main` (constructors / init)
```bash
readelf -SW ./chall | grep -E 'init_array|preinit_array|ctors|\.init '
objdump -s -j .init_array ./chall             # pointers (little-endian); map each to a symbol
objdump -s -j .preinit_array ./chall 2>/dev/null
nm -n ./chall | grep -iE 'init|ctor|frame_dummy'
```
- Every `.init_array` entry other than `frame_dummy` is a user constructor
  (`__attribute__((constructor))`); also check `DT_INIT` (`readelf -d | grep INIT`) and, on PE,
  TLS callbacks (`IMAGE_TLS_DIRECTORY`) and static initializers called from the CRT.
- Go: package `init()` functions run before `main.main`; look for `main.init`, `main.init.0`,
  `*.init.N` in symbols (`go tool nm` or Ghidra with Go analyzers) and anything assigned to a
  function variable there (the "installed" checker).
- Confirm dynamically: what did the constructor change?
```bash
gdb -q ./chall -ex 'starti' -ex 'x/16xb <target>' \
  -ex 'break main' -ex 'continue' -ex 'x/16xb <target>'   # bytes before vs after init
```
  Also `catch syscall mprotect` and `rwatch`/`watch *<addr>` on the comparison table or a function
  pointer to see who rewrites it.

## Gotchas

- A constructor hint can be a red herring: if `.init_array` holds only `frame_dummy`, `DT_INIT`
  is stock and memory at `main` equals the on-disk bytes, the static values are valid.
- The reverse case: a hint says an init-installed checker exists, but the shipped file has none
  (only stock init, data untouched at `main`). Then the attachment is probably the decoy-only
  build: the real answer is not derivable. Re-download, compare hashes, ask support; do not burn
  attempts submitting the decoy answer.
- A decryptable function in `main` can itself be the decoy when a hint says another checker is
  installed: see `self-modifying-code-mprotect-xor-decrypt`.
- `LD_PRELOAD`/`LD_LIBRARY_PATH` in your shell changes resolution: run `env -i ./main` to match the
  intended environment.
- Neither build may print the result (output gated on an impossible branch): solve statically by
  replaying the loop over the data table.
- NOT this pattern: one binary whose `main` never reaches the visible compare (trap, exception,
  pivot) is `hidden-check-off-main-path`.

## Cross-reference

- `hidden-check-off-main-path`: real check reached through a signal/exception/pivot.
- `self-modifying-code-mprotect-xor-decrypt`: encrypted function decrypted at runtime.
- `flag-check-reverse-transform`: inverting the real check once found.
- `Manuals/Ghidra/3. Contexto para Claude.md`: decompiling the chosen build/library.

---
id: carcarapack-dynamic-hbreak
category: REV
tags: [packer, self-extracting, memfd-create, fexecve, carcarapack, anti-debug, hardware-breakpoint, hbreak, bwrap, ld-preload, ptrace, rdtsc, dynamic-unpack, reverse04, reverse05, reverse06, reverse07]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "CarcaraPack: dynamic fast-path (hook fexecve + hbreak before the anti-debug)"
difficulty: medium
created: 2026-10-08
updated: 2026-11-06
related: [self-extracting-packer-memfd-unpack, self-modifying-code-mprotect-xor-decrypt]
---

## How to recognize this pattern

The CarcaraPack family (`reverseNN`): a stripped ELF stub with `memfd_create` + `fexecve` +
`/proc/self/exe`, a `CPKX` footer in the last 40 bytes. The inner ELF = a `--check <hex 32B>`
validator that prints `profile N` (= the `reverseNN` slug). The flag comes from the server via
challenge-response. After 01/02/03 (reversed statically), the inner skeleton stabilizes and you can
extract the secret WITHOUT reversing the logic.

## Method (fast-path, ~3 min per challenge)

### 1. Dynamic unpack via a hook on `fexecve`
```c
int fexecve(int fd, char*const a[], char*const e[]){ dumpfd(fd,"fexecve"); _exit(0); }
```
```bash
bwrap --ro-bind /usr /usr --symlink usr/lib64 /lib64 --symlink usr/lib /lib \
  --symlink usr/bin /bin --proc /proc --dev /dev --tmpfs /tmp \
  --bind out /out --ro-bind hook.so /hook.so --unshare-all --die-with-parent \
  --setenv LD_PRELOAD /hook.so /out/s.bin     # dump matches orig_size from the CPKX footer
```

### 2. Read the secret BEFORE the anti-debug: hardware breakpoint
The inner binary computes the 32B secret on the stack and THEN runs the anti-debug (TracerPid,
PPid/comm, `LD_PRELOAD`, `.text` integrity via `dl_iterate_phdr`, `rdtsc`/`0xdeadbeef`). If it fires,
it diverts to the **`CPK-POISON`** path and the secret turns FALSE.

→ **an int3 breakpoint POISONS it.** Use `hbreak` right before `fopen("/proc/self/status")`, at the
`cmp QWORD PTR [rsp+X],0x20`, and dump the buffer (`lea r14/r15,[rsp+OFF]` right after the `rdtsc`
block):
```gdb
set startup-with-shell off
starti --check 0000...0000
hbreak *<addr_cmp>
continue
python print(bytes(gdb.selected_inferior().read_memory(int(gdb.parse_and_eval("$rsp"))+OFF,32)).hex())
```

Confirmed values (find them per build: `cmp [rsp+X],0x20` before the `fopen status`; buffer = `lea`
after the `rdtsc`):

| # | hbreak | OFF |
|---|---|---|
| 04 | `0x401487` | `0x100` |
| 05 | `0x401490` | `0x100` |
| 06 | `0x401490` | `0xe0` |
| 07 | `0x40147f` | `0xe0` |

### 3. Confirm and submit
`./inner --check <hex>` → `accepted`. Then: `proof=sha256(secret.hex())`, `GET /ticket`,
`token=sha256("ticket:proof")`, `POST /flag`.

## Gotchas

- **int3 poisons**: use only `hbreak`. (If the target has no hardware breakpoint, try `starti` +
  `hbreak`; some gdb/targets only enable hbreak after `starti`.)
- ALWAYS run it isolated (`bwrap --unshare-all`, no network): memfd+fexecve executes arbitrary code.
- Stage-1 constants vary per build, but the dynamic fast-path ignores this (you don't need stage-1).

## Related

- `Arsenal/REV/self-extracting-packer-memfd-unpack.md`: the full static method + footer/stages.
- `Arsenal/REV/self-modifying-code-mprotect-xor-decrypt.md`: shares the rule that a normal
  breakpoint corrupts code that rewrites itself; use hardware breakpoints.

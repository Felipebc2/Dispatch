---
id: vm-bytecode-keygen-z3
category: REV
tags: [keygen, serial, vm, bytecode, virtual-machine, z3, smt, simd, hash, big-endian, oracle, license, symbolic-execution]
tools: []
manuals: []
title: "REV: keygen with a bytecode VM (model it in z3, key-schedule as a black box)"
difficulty: hard
created: 2026-10-08
updated: 2026-10-08
related: [arx-keygen-invert-license-check, flag-check-reverse-transform]
---

## How to recognize this pattern

A keygen (`<LICENSE> <SERIAL>` → VALID/INVALID) where the check is a **bytecode VM**: a dispatcher
with `add rdi,<size>` per instruction, registers in an array on the stack (`[rsp+idx*4]`), arithmetic
opcodes (add/sub/xor/mul/rol/ror/and/or), and a CMP opcode that sets an "invalid" flag. It may come
with a heavy **SIMD key-schedule** (pmuludq/pshufd with `0x9e3779b1`) deriving constants from the
license.

## Method

1. Find the final check (e.g. `esi==0 && edx==CONST && r14>=0`). Separate what's derived ONLY from
   the license (self-satisfied, e.g. `edx`/`r14`) from what depends on the input, and target only the
   CMP equalities.
2. Decode the VM opcodes: the instruction format (`[op][dst][src][b3][imm]`), the semantics of each
   op, where the input and the constant arrays come in. Dump the **program** and the **arrays** from
   memory with the binary running under gdb (break at the 1st fetch).
3. **Model the VM in z3** with the input SYMBOLIC and the license constants CONCRETE (read from
   memory). You don't need to reverse the SIMD key-schedule: it's license→constants, and you read
   the result directly. `s.add(reg[b1]==reg[b2])` at each CMP; `solve()` → valid input.
4. If it's a network challenge-response (N rounds), automate it: receive the license, run the solver,
   send the serial.

```python
# A4[i] = int(license_hex[i*8:i*8+8],16)   # CHECK the endianness (it was BIG-ENDIAN in the real case)
# S[0..7] = z3.BitVec32 ; run the program ; s.add at each CMP ; m = s.model()
```

## Gotchas

- **Validate the concrete VM against a trace from the binary** (e.g. input=zeros, compare `exp`/`mine`
  at each CMP) BEFORE trusting z3. In the real case the first model came out INVALID due to the wrong
  license endianness (`<I` vs big-endian).
- Running `python3` with z3 needs the user's site-packages → do NOT use `-I` (it ignores the user
  site); run it from a directory with no planted files.
- Opcodes may have masks (`src&7`, `src&3`) selecting from different arrays (input vs constants).
  Check the `and` before the load.

## Related

- `Arsenal/REV/arx-keygen-invert-license-check.md`: when the keygen is an invertible ARX (no VM).

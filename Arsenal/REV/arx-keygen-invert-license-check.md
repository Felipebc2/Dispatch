---
id: arx-keygen-invert-license-check
category: REV
tags: [keygen, arx, cipher, invert, obfuscated-add, opaque-predicate, dead-code, ptrace-antidebug, fnv1a, murmur3, static-elf, license, nimbuslock]
tools: [objdump]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: keygen-me (invert the ARX cipher of a license-check validator)"
difficulty: hard
created: 2026-10-07
updated: 2026-10-07
related: [flag-check-reverse-transform, static-triage-strings-ltrace]
---

## How to recognize

- A **small static stripped ELF** (~8KB), used as `prog <ID> <SERIAL>` → `VALID`/`INVALID`, plus an
  nc server that sends N product ids and asks for a serial for each (a real keygen; patching doesn't
  help, since the server validates with its own copy).
- A prompt like "most of the control flow never runs" = **opaque predicate** + dead code. E.g.
  `(~x)*x` is ALWAYS even → `test cl,1` always 0 → a branch never runs (decoy). Find the one that
  runs.
- Anti-debug `ptrace(PTRACE_TRACEME)` (syscall 101) at the start; its result feeds the final verdict.
- Integrity: FNV-1a over a rodata blob compared against a fixed constant (anti-tamper).

## Method (all static via objdump, WITHOUT running)

1. **Map strings→code:** `vaddr = fileoff + rodata_base` (check it in `readelf -S`). Find where
   `VALID`/`INVALID` are chosen (usually `cmovne` + `sete al`; return !=0 = VALID).
2. **Keyschedule:** typically a fixed blob in rodata expanded into a **table K of N dwords**.
   NimbusLock case: `K[i] = fmix(u16[blob+0xa+2i]) ^ u32[blob+0x11a+4*w] ^ fmix`, where `fmix` =
   murmur3-ish (`*0x9e3779b1 ^0x29b8afed`, shr16, `*0x85ebca77`, shr13, `*0xc2b2ae3d`, shr16).
   **Golden anchor:** reproduce the **FNV-1a of the blob** and match the binary's constant (e.g.
   `0x3d1685e8` over `blob[0..0x33a)`). If it matches, you're reading the right bytes → K is
   trustworthy. Watch for an off-by-one in the range (`cmp rcx,LEN; rcx+=2` processes `LEN` bytes,
   not `LEN+1`).
3. **Identify the cipher.** Real case: an **8-round ARX** over a state of 8 dwords (= the serial),
   with subkeys derived from the product id. A state machine phased by `eax`; the order of the ops
   matters (here it was `A→B→D→C` per round):
   - **A (add):** `s_i += RC[round] + W_i`. **The idiom `(a^b)+2*(a&b)` is just an obfuscated
     `a+b`.**
   - **B (mul):** `s_i *= K_mul[i]` (odd → invertible with the inverse mod 2^32 via Newton).
   - **D (rot):** `s_i = rol(s_i, K_rot[i])`.
   - **C (diffusion):** `m_j = Σ_i Mat[j][i]*s_i (mod 2^32)`; then **permute** `s_j = m[perm[j]]`.
     Invertible if `det(Mat)` is odd (Gaussian elimination mod 2^32 with an odd pivot).
   - Product subkeys: `W_i = rol(K[..]^product[i%4], K[..])`.
4. **Finalize = target.** After the rounds, it compares the state against `T[j] = f_j(product) ^
   K[..]`, ORing the differences (`sete al`). VALID ⟺ final_state == T. Since the cipher is a
   **bijection**: `serial = cipher⁻¹(T)`. Invert round by round in reverse order
   (`C⁻¹→D⁻¹→B⁻¹→A⁻¹`, rounds 7..0).
5. **Parse endianness (common mistake):** the hex→dword is usually **big-endian per group**
   (`int(hex_group,16)`), NOT `struct.unpack("<I")`. Deduce it from the parser's shift/or and
   **confirm with the FNV anchor + self-consistency** (`fwd(inv(T))==T`) before spending an attempt
   on the server.

## Gotchas

- Self-consistency (`fwd∘inv==id`) does NOT prove K/the cipher are right, only that your inverse
  matches your forward. The real proof is the **FNV anchor** (right bytes) + the **server oracle**.
  Validate offline as much as possible before connecting (keygen servers sometimes rate-limit / allow
  1 connection).
- The flag comes from the server after you solve the N; the local binary never prints a flag (only
  VALID/INVALID).

## Related

- `Arsenal/REV/self-extracting-packer-memfd-unpack.md`: another REV challenge (CPKX unpack).
- `Arsenal/REV/flag-check-reverse-transform.md`: invert a validator's transform.

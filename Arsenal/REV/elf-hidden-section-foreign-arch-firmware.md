---
id: elf-hidden-section-foreign-arch-firmware
category: REV
tags: [elf, readelf, section-headers, custom-section, unreferenced-section, progbits, objcopy, only-section, carrier, decoy, embedded-firmware, firmware-blob, foreign-architecture, cross-arch, arm, thumb, cortex-m, vector-table, reset-vector, raw-binary, arm-none-eabi-objdump, radare2, capstone, unicorn, binwalk, cpu-rec, stm32]
tools: [Ghidra]
manuals: ["Manuals/Ghidra/3. Contexto para Claude.md"]
title: "REV: second program hidden in an unreferenced ELF section (foreign-arch firmware blob)"
difficulty: medium
created: 2026-11-06
updated: 2026-11-06
related: [static-triage-strings-ltrace, self-extracting-packer-memfd-unpack, self-modifying-code-mprotect-xor-decrypt, flag-check-reverse-transform]
---

## How to recognize this pattern

- The binary is trivial: `main` prints one line (often a plausible but wrong "decoy" answer) and
  exits. Few imports (just `puts`/`printf`), nothing reads its own file.
- `readelf -S` shows a **non-standard section name** (`.payload`, `.fw`, `.<challenge-word>`),
  usually small, `PROGBITS`, that no code references.
- The prompt talks about an "image", "firmware", "the file carries X", "device", "handset".
- The dumped bytes do not disassemble as x86 but have a recognizable layout for another CPU
  (see table below).

## Method

### 1. Find the odd section
```bash
readelf -S -W ./bin                      # look for names outside the usual set
readelf -S -W ./bin | grep -vE '\.(interp|note|gnu|dyn|rela|init|plt|text|fini|rodata|eh_frame|init_array|fini_array|data|bss|comment|symtab|strtab|shstrtab|got|tm_clone)'
objdump -d -M intel ./bin | grep -i '<section-vaddr>'   # confirm nothing references it
```

### 2. Dump it
```bash
objcopy -O binary --only-section=.payload ./bin blob.img
xxd blob.img | head
# no objcopy (or section is not ALLOC): use offset/size from readelf
dd if=./bin of=blob.img bs=1 skip=$((0x2029)) count=$((0x30))
```

### 3. Identify the architecture
| Signal in the first bytes | Likely target |
|---|---|
| word0 `0x2000xxxx` (SRAM top = initial SP), word1 `0x0800xxxx` odd | ARM Cortex-M (STM32-like), Thumb, flash base `0x08000000` |
| word1 `0x0000xxxx` odd, word0 `0x2000xxxx` | Cortex-M with flash at 0 |
| repeated `0c 94 xx xx` (jmp) | AVR interrupt vector table |
| `7f 45 4c 46` | a full ELF: just `file` / `readelf -h` it |
| `13 00 00 00`, `97 xx`/`37 xx` early | RISC-V |
```bash
binwalk -A blob.img                      # opcode signature scan
python3 cpu_rec.py blob.img              # statistical ISA guess (cpu_rec)
```

### 4. Disassemble at the right base
```bash
arm-none-eabi-objdump -D -b binary -marm -Mforce-thumb --adjust-vma=0x08000000 blob.img
r2 -a arm -b 16 -m 0x08000000 blob.img   # then: pd 40 @ 0x08000010
```
```python
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
img = open('blob.img','rb').read(); base = 0x08000000
reset = int.from_bytes(img[4:8], 'little') & ~1        # clear Thumb bit
for i in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(img[reset-base:], reset):
    print(hex(i.address), i.mnemonic, i.op_str)
```
Ghidra: import as Raw Binary, language `ARM:LE:32:Cortex`, base address `0x08000000`, then
disassemble at the reset vector (see the Manual).

### 5. Emulate if hand-decoding gets long
```python
from unicorn import *; from unicorn.arm_const import *
img = open('blob.img','rb').read(); base = 0x08000000
mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
mu.mem_map(base, 0x10000); mu.mem_map(0x20000000, 0x10000); mu.mem_write(base, img)
sp, reset = int.from_bytes(img[0:4],'little'), int.from_bytes(img[4:8],'little')
mu.reg_write(UC_ARM_REG_SP, sp)
mu.emu_start(reset, base + len(img), count=10000)      # stops on the b . spin via count
print(hex(mu.reg_read(UC_ARM_REG_R0)), mu.mem_read(base, len(img)))
```
The answer is usually what the firmware writes back into its own buffer (decode in place) or
leaves in `r0` before the final `b .` (infinite loop = "halt").

## Gotchas

- **Thumb bit**: vector entries are odd; the code is at `vector & ~1`. Disassembling in ARM
  (32-bit) mode gives garbage.
- `ldr rX, [pc, #imm]` reads from `((pc + 4) & ~3) + imm`; get this wrong and the literal pool
  points to the wrong buffer.
- The host's printed line is a decoy: often each decoy value maps one-to-one to a real answer
  (same field, different value). Do not submit it.
- NOT this pattern if the extra data is **appended after the last section** (overlay/footer) and
  the binary reads `/proc/self/exe`: that is `self-extracting-packer-memfd-unpack`.
- NOT this pattern if the odd section is referenced by `.text` (e.g. a lookup table read by the
  check): then it is ordinary data for `flag-check-reverse-transform`.
- NOT this pattern if the odd section is **executable** host-arch code that disassembles to
  garbage and `main` calls `mprotect` on it: that is `self-modifying-code-mprotect-xor-decrypt`.
- `.note.*`, `.gnu.*`, `.comment`, `.init_array` are standard; ignore them.

## Cross-reference

- `static-triage-strings-ltrace`: do the triage first; `readelf -S` belongs there.
- `self-extracting-packer-memfd-unpack`: payload in a footer, extracted at runtime.
- `Manuals/Ghidra/3. Contexto para Claude.md`: raw-binary import with a custom language/base.
- FOR `file-carving-signature-repair`: when the hidden blob is a file format, not code.

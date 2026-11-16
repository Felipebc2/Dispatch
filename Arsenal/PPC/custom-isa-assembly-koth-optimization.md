---
id: custom-isa-assembly-koth-optimization
category: PPC
tags: [koth, king-of-the-hill, custom-isa, assembly, tis-100, multi-core, cycles, instructions, local-simulator, optimization, pareto, unroll, parallel-cores]
tools: []
manuals: []
title: "Custom-ISA assembly (TIS-100-style) KotH: simulate locally, optimize the score"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [multiround-timed-service-harness]
---

## How to recognize this pattern

- A King-of-the-Hill round posts a small program spec for a **custom multi-core 8-bit assembly machine**
  (TIS-100-like: per-core `ACC`/`BAK`/ports, no shared memory, blocking I/O). You write a program, export
  it, and submit by a deadline; scoring rewards **fewest cycles** and **fewest instructions**.
- You get a manual for the ISA but have to **infer undocumented behavior** (does the program wrap to its
  first instruction? how are ties scored?).

## Method

### 1. Build a local simulator first
Parse and run the `.prog` against the round's test cases offline so you can iterate without spending the
official simulator / submission budget:
```bash
python3 sim.py machine.json solution.prog [--trace] [--no-wrap]   # reports instr/core, cycles, correct/WRONG
```
Use it to **confirm the undocumented rules** (e.g. an implicit wrap-around after the last instruction lets
you drop the final `JMP`; instruction counts sum across all cores; local cycles match the official count).

### 2. Pull both levers, build two versions
- **Fewer instructions:** rely on implicit wrap instead of `JMP`, reuse `BAK` (`SAV`/`SWP`) instead of an
  extra core, `ADD ACC` to double.
- **Fewer cycles:** unroll loops, split work across cores running in parallel, interleave reads of a shared
  input so two reads never land in the same cycle.
These usually conflict — build both and keep the higher combined score.

### 3. Beat the duplicate-scoring rule
Identical `(cycles, instructions)` pairs from different teams **lose value for all of them**; text-only
variation (`SUB -1` vs `ADD 1`, case, labels) does **not** count as different. Aim for a **Pareto point
nobody else is likely to hit** (spend a few instructions to win more cycles) rather than the obvious layout
several teams will tie on.

## Gotchas

- **Official cycles ≠ example cycles:** the ranking runs more/longer inputs than the sample; the *ordering*
  between layouts holds, so optimize on the simulator and only sanity-check the final version officially.
- Do **not reorder sections** — the official simulator assigns cores by position (first section = core 0).
- A no-submission round is the biggest score loss; always submit *something* correct before the deadline.
- Validate the final program in the official simulator before submitting (parser quirks, comma handling).

## Cross-reference

- `multiround-timed-service-harness`: scripting the per-round submit/evaluate loop against a timed service.

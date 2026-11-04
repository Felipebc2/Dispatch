---
id: move-sui-source-encoded-puzzle-input
category: WEB
tags: [blockchain, sui, move, not-evm, puzzle, source-reading, nested-if, satisfy-input, win-getter, spellbook, decoy, easy, justctf, otter-scrolls, ottersec, solve-module]
tools: [Sui]
manuals: ["Manuals/Sui/3. Contexto para Claude.md"]
title: "Move/Sui: the win is a puzzle encoded in the source; supply the input that satisfies it (not crypto)"
difficulty: easy
created: 2026-10-08
updated: 2026-10-08
related: [move-sui-validated-index-vs-consumed-element, web3-unprotected-beacon-proxy-upgrade]
---

> ⚠️ **Sui** / **Move** chain (non-EVM). Toolchain = Sui CLI + Move (a `solve` module published by the
> launcher). See the toolchain note in `Arsenal/WEB/move-sui-validated-index-vs-consumed-element.md`.
> (`Manuals/Sui/` pending).

## How to recognize this pattern

- The win condition is a `getter`/function that only returns the flag once an internal flag (`casted`,
  `solved`) flips to `true`, and that flag is set by a function full of **nested ifs / sequence
  checks** over an input you control.
- It looks like crypto/math but **isn't**: the correct values are **in the source itself** (word
  tables, constants, expected order). It's "read the code and supply the input that passes".

## Method

Reference case: justCTF 2024, The Otter Scrolls (Sui/Move, Easy). `cast_spell(spell_sequence, book)`
removes 5 "spells" from the table (fire=0, wind=1, water=2, earth=3, power=4), and each
`spell_sequence[i]` is the index of the word chosen for that spell. The nested ifs require the right
combination; get it right and `book.casted = true` and `check_if_spell_casted` returns the flag.

```move
module solve::solve {
    use challenge::theotterscrolls;
    public fun solve(_spellbook: &mut theotterscrolls::Spellbook, _ctx: &mut TxContext) {
        let spell_seq = vector[1, 0, 3, 3, 3];   // indices that satisfy the ifs (read from the source)
        theotterscrolls::cast_spell(spell_seq, _spellbook);
    }
}
```
Compile (`sui move build`) and submit via the client/launcher (`nc tos.nc.jctf.pro 31337`) → flag.

## Gotchas

- Don't waste time "solving" it as if it were crypto/ZK; trace the `if`/`assert` chain and extract the
  exact values/indices that make each branch pass.
- In Move, objects like `Spellbook` are **shared objects** passed by the launcher into your `solve`;
  you only operate on them, you don't create them.
- Same spirit as the "private input"/puzzle decoy in `web3-unprotected-beacon-proxy-upgrade`
  (commitPuzzle) and others: the "proof" is just the state in the source.

## Transferable lesson

When the win is a puzzle baked into the contract, the answer is in the contract. Read the logic, supply
the satisfying input, done. Don't design a crypto attack where it's just source reading.

## Related / Cross-reference

- `Arsenal/WEB/move-sui-state-machine-reclaim-reward.md` and
  `move-sui-validated-index-vs-consumed-element.md`: others from the same Sui/Move set (justCTF 2024).

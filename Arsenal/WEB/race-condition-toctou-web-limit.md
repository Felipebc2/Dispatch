---
id: race-condition-toctou-web-limit
category: WEB
tags: [race-condition, toctou, time-of-check-time-of-use, concurrency, parallel-requests, limit-overrun, double-spend, negative-balance, single-packet-attack, turbo-intruder, coupon-reuse]
tools: []
manuals: []
title: "Web race condition: beat a check-then-act limit with parallel requests"
difficulty: medium
created: 2026-11-23
updated: 2026-11-23
related: [toctou-decompression-overflow-validated-structure, client-side-enforced-control-bypass, jwt-alg-none]
---

## How to recognize this pattern

- An action reads a value, **checks** it, does something, then **writes** the updated value — with no
  lock/transaction between check and write. Fire several requests at once and multiple pass the check
  before any write lands.
- Targets: a balance/quota of **1** (leave days, credits, coupon, stock), "one redemption per user",
  "withdraw ≤ balance", gift-card apply, vote-once. The flag appears only in an **impossible state**
  (negative balance, item claimed twice, limit exceeded).
- Prompt hints: "race", "negative", a short artificial delay between check and deduct, a `/flag` route
  that fires only when a counter goes below zero.

## Method

### 1. Establish state, then flood with parallel requests
```bash
B=https://target
curl -s -c j -X POST $B/start          # get a session with balance = 1
seq 20 | xargs -P20 -I_ curl -s -b j -X POST $B/book >/dev/null   # 20 concurrent "spend"
curl -s -b j $B/flag                    # balance now negative → flag
```
`-P20` runs them in parallel; that parallelism is the whole attack. Tune the count up if one deduct
beats the rest.

### 2. Tighten the timing when `xargs` is too loose
- **Burp Turbo Intruder** with the single-packet attack (HTTP/2) lands ~20–30 requests in one TCP
  packet, eliminating network jitter — the strongest primitive for tight windows.
- Python `asyncio`/`aiohttp` or `httpx` with a barrier so all requests are released simultaneously:
  ```python
  import asyncio, httpx
  async def go(c, b): await c.post(b+"/book", cookies=COOKIES)
  async def main():
      async with httpx.AsyncClient(http2=True) as c:
          await asyncio.gather(*[go(c, B) for _ in range(30)])
  asyncio.run(main())
  ```

### 3. Confirm and read the impossible state
Check the balance/counter after the burst. If it only dropped by 1, the window was too wide or a lock
exists — raise concurrency, add the single-packet technique, or look elsewhere.

## Gotchas

- **Same session/token across all requests** — the race is on one account's shared row. Parallel
  requests with different sessions don't collide.
- Network jitter is the enemy: sequential-but-fast often loses. Prefer single-packet / one connection
  with many multiplexed streams over many separate connections.
- Some backends serialize via a DB transaction or `SELECT ... FOR UPDATE` — then no race; pivot to a
  different bug (IDOR, logic).
- The flag may be **per-session** and partly random; submit the exact flag your own session returns,
  not the one in a write-up.
- Don't hammer production-style targets blindly; a few dozen parallel requests is enough to prove it.

## Cross-reference

- `toctou-decompression-overflow-validated-structure`: the same check-vs-use gap in a binary/PWN
  setting (validator ↔ consumer).
- `client-side-enforced-control-bypass`: sibling "the server trusts something it shouldn't" logic flaw.

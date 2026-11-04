---
id: partial-clue-backtracking
category: MISC
tags: [backtracking, dfs, pruning, reconstrucao-de-string, pistas-parciais, ambiguidade]
tools: []
manuals: []
title: "Reconstruct a string/flag from partial, ambiguous clues"
difficulty: medium
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- The challenge gives N "positions" of a flag/message, but each position has **1+ candidate readings**
  instead of a single trustworthy value. For example: two overlaid images where each suggests a
  different character for the same slot, ambiguous OCR, noisy audio decoded two ways, a cipher with
  multiple candidate keys per position.
- Strong signal: you already know the flag format (a fixed prefix, allowed charset, presence of `}`/`_`
  at specific positions) but can't pin down each character with visual/auditory certainty.
- Unlike a single-position puzzle, here there's structural ambiguity, not missing data.

## Method

The technique is **DFS with pruning on the known valid prefix**, not blind brute force over the whole
alphabet. Steps:

1. **For each position `i` of the target string, build the set of candidates** `opts[i]`: the
   characters that position could be, coming from the multiple sources/clues available. If a position has
   no reliable reading at all, use a placeholder (e.g. `_`) rather than leaving it empty.
2. **Restrict the global charset** to what's plausible for the current CTF's flag format (uppercase
   letters, digits, `_`, `{`, `}`; adjust to the real format, see `CLAUDE.md`).
3. **Fix the positions you're absolutely sure of** (usually the flag prefix, like the first 3-4
   characters). This drastically cuts the search space.
4. **Define a prefix-validation function** (`looks_valid_prefix`) that rejects early any branch that
   already doesn't match the expected format (doesn't start with the right prefix, contains a character
   outside the allowed charset). This is the pruning that makes the backtracking viable instead of
   exponential forever.
5. **DFS position by position**, testing each candidate in `opts[i]`, cutting invalid branches
   immediately via `looks_valid_prefix`, and collecting the complete prefixes that match
   `looks_valid_full` (right prefix + right suffix/closing, e.g. contains `}`).
6. If more than one plausible final candidate remains, test each against the challenge's
   service/validator (or against the expected final MD5 hash format, if the flag format has that
   structure) until you find the correct one.

```python
def looks_valid_prefix(s, PREFIX, ALLOWED):
    if len(s) <= len(PREFIX):
        return PREFIX.startswith(s)
    if not s.startswith(PREFIX):
        return False
    return all(ch in ALLOWED for ch in s)

def looks_valid_full(s, PREFIX, ALLOWED):
    return s.startswith(PREFIX) and '}' in s and all(ch in ALLOWED for ch in s)

def solve(opts, fixed, PREFIX, ALLOWED, max_results=20):
    results = []
    N = len(opts)

    def dfs(pos, prefix):
        if not looks_valid_prefix(prefix, PREFIX, ALLOWED):
            return
        if pos == N:
            if looks_valid_full(prefix, PREFIX, ALLOWED):
                results.append(prefix)
            return
        candidates = [fixed[pos]] if pos in fixed else opts[pos]
        for ch in candidates:
            dfs(pos + 1, prefix + ch)
            if len(results) >= max_results:
                return

    dfs(0, "")
    return results
```

`opts`, `fixed`, `PREFIX` and `ALLOWED` are the only parameters specific to the current challenge. The
algorithm itself is generic.

## Gotchas

- If `opts[i]` has many candidates across many positions, the space can still explode even with pruning.
  In that case it's worth reducing ambiguity in the sources first (re-reading the image/audio more
  carefully) rather than trusting the algorithm alone.
- A wrong allowed charset (`ALLOWED`) is the most common cause of "no candidate found". Check that
  symbols like `_`/`{`/`}` are included before concluding the vector is wrong.
- Don't force a closing character (`}`) to appear only at the last position if the flag format allows
  variable-length content. Adjust `looks_valid_full` as needed.

## Related / Cross-reference

No cross-reference with `Manuals/`. It's pure algorithm technique, useful whenever there's
position-by-position ambiguity instead of a single clear clue.

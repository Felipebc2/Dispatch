---
name: ctf-solve
description: >-
  Shortcut for solving a CTF challenge. It identifies the category, pulls the matching entries from
  the Arsenal by search (never the whole folder), and routes into the /dispatch flow, which always
  stops at the human checkpoint before any attack runs. Use when the user pastes or describes a CTF
  challenge, mentions one of the 12 tags (CRYPTO, REV, PWN, FOR, JAIL, OSINT, NET, WEB, PPC, MISC,
  TRIVIA, LLM), or asks to attack or solve a challenge. Do not use it for trivial encoding, crypto,
  or web that is faster to solve by hand.
---

# ctf-solve: per-category shortcut into /dispatch

This skill does not solve or run attacks. It identifies the category, loads only the relevant
context, and hands off to the `/dispatch` orchestrator (`commands/dispatch.md`), which runs the full
flow: triage, Arsenal lookup, human checkpoint, then the matching `solver-<category>`.

The flag format is whatever the user configured (`${user_config.flag_format}` by default; override
at runtime with `/ctf-dispatch:setflag`).

## Permanent rule (do not bypass)

No `solver-*` runs without explicit user approval at the `/dispatch` checkpoint. This skill exists to
make the flow faster, never to skip the checkpoint. If the challenge is trivial (simple encoding,
easy crypto, OSINT, reversing, or web), say so: solving it by hand is faster than an AI round trip.

## How to use

1. **Identify the category** from what the user pasted: an explicit tag hint, or infer it from the
   prompt and attachment signals.
2. **Pull only the relevant Arsenal entries by search.** Do not read a whole `Arsenal/<CAT>/` folder
   (a large category would flood the context). Run the search and read only what it returns, plus any
   Manual it cites:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/arsenal_search.py "<3-8 technical keywords>" --category <CAT> --json --top 5
   ```
   Claude Code fills in `${CLAUDE_PLUGIN_ROOT}`. On Codex it does not resolve, so run
   `scripts/arsenal_search.py` from this plugin's install directory instead (locate it with
   `find ~ -name arsenal_search.py -path '*ctf-dispatch*' 2>/dev/null` if you are unsure).
3. **Route into `/dispatch`.** Follow `commands/dispatch.md` from step 2 onward (brainstormer,
   arsenal_search, checkpoint). Pass the identified category as a hint so triage starts warm.
4. **Stop at the checkpoint** and wait for accept, reject, redirect, refine, or ask.

## Playbook by category

The table maps each category to its reference manuals and solver. Use it to know which Manual to read
when a search result cites a tool, and which solver `/dispatch` will route to after you accept.

| Tag | Arsenal | Reference manuals | Solver agent |
|---|---|---|---|
| CRYPTO | `Arsenal/CRYPTO/` | RsaCtfTool, CyberChef, Hash-Cracking | `solver-crypto` |
| REV | `Arsenal/REV/` | Ghidra | `solver-rev` |
| PWN | `Arsenal/PWN/` | pwntools, Ghidra | `solver-pwn` |
| FOR | `Arsenal/FOR/` | Wireshark, LSB-Stego | `solver-for` |
| JAIL | `Arsenal/JAIL/` | (none) | `solver-jail` |
| OSINT | `Arsenal/OSINT/` | (none) | `solver-osint` |
| NET | `Arsenal/NET/` | pwntools (socket) | `solver-net` |
| WEB | `Arsenal/WEB/` | sqlmap, JWT | `solver-web` |
| PPC | `Arsenal/PPC/` | (none) | `solver-ppc` |
| MISC | `Arsenal/MISC/` | CyberChef, LSB-Stego | `solver-misc` |
| TRIVIA | `Arsenal/TRIVIA/` | (none) | `solver-trivia` |
| LLM | `Arsenal/LLM/` | CyberChef (decode output) | `solver-llm` |

A cited Manual lives at `${CLAUDE_PLUGIN_ROOT}/Manuals/<Tool>/3. Contexto para Claude.md`.

## When the category is ambiguous

Do not force it. Let the `brainstormer` (step 2 of `/dispatch`) infer it from the raw context and
attachments. The table above is for loading the playbook after the category is clear, not for
guessing before triage.

---
name: ctf-solve
description: >-
  Shortcut for solving a CTF challenge: preloads the category playbook (Arsenal entries +
  Manuals + the right solver agent) and routes into the /dispatch flow, always stopping at the
  human checkpoint before any attack runs. Use when the user pastes/describes a CTF challenge,
  mentions one of the 12 tags (CRYPTO, REV, PWN, FOR, JAIL, OSINT, NET, WEB, PPC, MISC, TRIVIA,
  LLM), or asks to attack/solve a challenge. Do NOT use for trivial encoding/crypto/web that is
  faster to solve by hand.
---

# ctf-solve — per-category shortcut into the /dispatch flow

This skill **does not solve or run attacks**. It preloads the right category context and hands off
to the `/dispatch` orchestrator (`commands/dispatch.md`), which does triage → Arsenal lookup →
**human checkpoint** → and only then invokes the matching `solver-<category>`.

The flag format is whatever the user configured (`${user_config.flag_format}` by default; override
at runtime with `/ctf-dispatch:setflag "<format>"`).

## Permanent rule (do not bypass)

No `solver-*` runs without explicit user approval at the `/dispatch` checkpoint. This skill exists
to make the flow faster, **never** to skip the checkpoint. If the challenge is trivial (simple
encoding, easy crypto/OSINT/reversing/web), say so — solving it by hand is faster than an AI
round-trip.

## How to use

1. **Identify the category** from what the user pasted (an explicit tag hint, or infer it from the
   prompt/attachment signals).
2. **Load the category playbook** from the table below: read the `Arsenal/<CAT>/` entries and the
   `Manuals/<Tool>/3. Contexto para Claude.md` file(s) listed — that is the context the solver needs.
3. **Route into `/dispatch`**: follow `commands/dispatch.md` from step 2 onward (brainstormer →
   arsenal_search → checkpoint). Pass the already-identified category as a hint.
4. **Stop at the checkpoint** and wait for accept/reject/redirect/refine/ask.

Arsenal lookup: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/arsenal_search.py "<3-8 technical keywords>"`.

## Playbook by category

| Tag | Arsenal | Reference manuals | Solver agent |
|---|---|---|---|
| CRYPTO | `Arsenal/CRYPTO/` | RsaCtfTool · CyberChef · Hash-Cracking | `solver-crypto` |
| REV | `Arsenal/REV/` | Ghidra | `solver-rev` |
| PWN | `Arsenal/PWN/` | pwntools · Ghidra | `solver-pwn` |
| FOR | `Arsenal/FOR/` | Wireshark · LSB-Stego | `solver-for` |
| JAIL | `Arsenal/JAIL/` | — | `solver-jail` |
| OSINT | `Arsenal/OSINT/` | — | `solver-osint` |
| NET | `Arsenal/NET/` | pwntools (socket) | `solver-net` |
| WEB | `Arsenal/WEB/` | sqlmap · JWT | `solver-web` |
| PPC | `Arsenal/PPC/` | — | `solver-ppc` |
| MISC | `Arsenal/MISC/` | CyberChef · LSB-Stego | `solver-misc` |
| TRIVIA | `Arsenal/TRIVIA/` | — | `solver-trivia` |
| LLM | `Arsenal/LLM/` | CyberChef (decode output) | `solver-llm` |

Full manual path: `${CLAUDE_PLUGIN_ROOT}/Manuals/<Tool>/3. Contexto para Claude.md`.

## When the category is ambiguous

Don't force it. Let the `brainstormer` (step 2 of `/dispatch`) infer it — it reads the raw context
and attachments. The table above is for preloading the playbook **after** the category is clear, not
for guessing before triage.

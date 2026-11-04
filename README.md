<!--
PRE-PUBLISH CHECKLIST (do before submitting to the marketplace):
  BRANDING (decided): primary banner = dark soft-3D hero; primary icon = retro
  red-square head; secondary = monoline emblem (favicon/sticker) + isometric
  blueprint (how-it-works figure). One art to be chosen later for a LinkedIn post.

  Assets (done):
  [x] assets/banner.png          <- dark hero banner (R2-S6-cel-wordmark)
  [x] .claude-plugin/icon.png    <- retro red-square head (R2-S5-riso-icon, PNG8 < 2MB)
  [x] assets/emblem.png          <- monoline emblem (favicon/sticker)
  [x] assets/how-it-works.png    <- isometric blueprint diagram
  [ ] (optional) assets/social-linkedin.png <- whichever art you pick for the LinkedIn post
  Still to do:
  [ ] Set homepage/repository URLs in .claude-plugin/plugin.json to the real repo.
  [ ] Update the install line below with the real repo slug.
  [ ] Publish to the marketplace.
-->

<p align="center">
  <img src="assets/banner.png" alt="CTF Dispatch" width="100%">
</p>

# CTF Dispatch

A Claude Code plugin for **triage-first CTF solving**. Dispatch classifies a challenge, retrieves a
documented method from a bundled **Arsenal** of problem-pattern → method notes, and **stops at a
human checkpoint** before any category solver runs. Nothing offensive executes without your explicit
approval.

> Use this only against targets you are authorized to attack — a CTF, a lab, or a competition you are
> playing.

## What's inside

- **`/dispatch`** — the orchestrator. Triage (via the `brainstormer` agent) → Arsenal lookup →
  human checkpoint → the matching `solver-<category>`.
- **`/ctf-dispatch:ctf-solve`** — a per-category shortcut that preloads the right playbook and routes
  into `/dispatch`.
- **`/ctf-dispatch:setflag`** — set the flag format your CTF uses (see below).
- **13 agents** — `brainstormer` (triage) + 12 category solvers: CRYPTO, REV, PWN, FOR, JAIL, OSINT,
  NET, WEB, PPC, MISC, TRIVIA, LLM.
- **Arsenal** — ~75 problem-pattern → method entries across the 12 categories, searched with a
  stdlib-only SQLite FTS5 index (`scripts/arsenal_search.py`).
- **Manuals** — per-tool references (Ghidra, CyberChef, JWT, pwntools, Wireshark, sqlmap, …).

## How it works

Dispatch runs one challenge through a fixed pipeline:

1. **Triage** — the `brainstormer` agent reads the raw challenge (text + any attachments) and infers the likely category and attack vectors.
2. **Arsenal lookup** — it searches the bundled Arsenal (SQLite FTS5) for a documented method matching that pattern, and cross-references the relevant tool manual.
3. **Human checkpoint** — it presents the category, the triage summary, the matching Arsenal entry, and a recommended approach, then **stops and waits** for your call (accept / reject / redirect / refine / ask).
4. **Dispatch** — only after you accept does it hand the challenge to the matching `solver-<category>` agent, which validates any flag it finds against your configured flag format.

<p align="center">
  <img src="assets/how-it-works.png" alt="CTF Dispatch — triage, Arsenal lookup, human checkpoint, dispatch to a solver" width="90%">
</p>

## Install

```
/plugin marketplace add Felipebc2/Dispatch
/plugin install ctf-dispatch@dispatch
```

(You can also develop locally with `claude --plugin-dir /path/to/this/repo`.)

## Flag format

Solvers validate a found flag against your CTF's flag format. Set it either way:

- **At install:** the `flag_format` plugin option (default `flag{...}`).
- **At runtime:** `/ctf-dispatch:setflag "HTB{...}"` — persists across plugin updates and overrides
  the install default. Run `/ctf-dispatch:setflag` with no argument to see the current value.

## The checkpoint (safety model)

`/dispatch` always pauses after triage + Arsenal lookup and presents a recommendation. No
`solver-*` agent runs until you answer **accept / reject / redirect / refine / ask**. This is a
process rule, not a suggestion — the orchestrator and solvers are written to never skip it.

## Optional MCP servers

`solver-pwn` and `solver-rev` can use the `ghidra` and `pwndbg` MCP servers if you have them
configured. They are **optional** — configure them yourself; the solvers degrade to plain Bash
tooling when the MCP servers aren't present.

## Extending the Arsenal

Add a `Arsenal/<CATEGORY>/<slug>.md` file following the frontmatter schema in
[`Arsenal/README.md`](Arsenal/README.md). The search index rebuilds incrementally on the next
`arsenal_search.py` call — no manual reindex needed.

## License

MIT — see [LICENSE](LICENSE).

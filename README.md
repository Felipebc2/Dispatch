<!--
PRE-PUBLISH CHECKLIST (do before submitting to the marketplace):
  [ ] Add a banner image at the top of this README.
  [ ] Add .claude-plugin/icon.png (square PNG, 512-2048px, < 2MB) for the directory listing.
  [ ] Set homepage/repository URLs in .claude-plugin/plugin.json to the real repo.
  [ ] Update the install line below with the real repo slug.
  [ ] Then: publish to the marketplace.
-->

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

## Install

```
/plugin marketplace add your-username/ctf-dispatch
/plugin install ctf-dispatch@dispatch
```

(Replace `your-username/ctf-dispatch` with this repository once you push it to a git host. You can
also develop locally with `claude --plugin-dir /path/to/this/repo`.)

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

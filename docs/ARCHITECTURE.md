# Architecture

How CTF Dispatch is organized, and why its context stays small as the Arsenal grows.

## Two layers

The repository is split into what the model reads and what it never reads.

**Model-facing (loaded on demand, into the model's context):**

| Path | What | When it loads |
|---|---|---|
| `commands/` | Slash commands (`/dispatch`, `setflag`) | When the command runs |
| `agents/` | `brainstormer` + 12 `solver-*` | Each agent loads only inside its own subagent run, one at a time |
| `skills/` | `ctf-solve` shortcut | When the skill triggers |
| `Arsenal/` | Problem-pattern to method entries | Never whole; pulled by search, one entry at a time |
| `Manuals/` | Per-tool references | Only the manual a search result cites |
| `scripts/arsenal_search.py` | Search and catalog tooling | Runs as a process; its output is small |

**Infra (never enters the model's context):**

| Path | What |
|---|---|
| `.claude-plugin/`, `.codex-plugin/` | Per-host plugin manifests (thin) |
| `.github/` | CI workflows |
| `docs/` | This file, contributing guide |
| `assets/` | Logo, banner, diagrams |
| `tests/` | Script tests |

## The context rule

The model never loads the whole Arsenal. It:

1. Searches with `arsenal_search.py` and gets the top few snippets (not full bodies).
2. Reads the single entry it decides is relevant.
3. Optionally navigates with the catalog, which returns ids and titles only, never bodies:
   - `--list` / `--tag <t>`: browse by tag.
   - `--graph <id>`: an entry's `related` neighbors and back-references.

Because navigation and search return lightweight records, the context cost is flat whether the
Arsenal holds 75 entries or 1500. Adding writeups does not grow what any single run loads.

Each `solver-*` is intentionally self-contained: it duplicates a short preamble rather than reading
a shared file at run time. Self-containment is the context-optimal choice here, since it avoids an
extra read inside every solver run.

## Per-host adapters

The core (commands, agents, skill, Arsenal, Manuals) is written once. Each host gets a thin adapter
that points at that core: `.claude-plugin/` for Claude Code, `.codex-plugin/` for Codex. The core
never duplicates per host.

## Regenerating the index

`Arsenal/INDEX.md` (the per-category listing plus the Mermaid relationship graph) is generated:

```bash
python3 scripts/arsenal_search.py --emit-index
```

Run it after adding or changing an entry. CI regenerates it on pull requests so it never drifts.

## Adding an Arsenal entry

See [`Arsenal/README.md`](../Arsenal/README.md) for the frontmatter schema. In short: one
`Arsenal/<CATEGORY>/<slug>.md` file, frontmatter with `id`, `category`, `tags`, `title`,
`difficulty`, and optional `related`, then a body that explains how to recognize the pattern and the
method that solves it.

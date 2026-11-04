# Arsenal: Problem-Pattern → Method Library

Unlike `Manuals/` (documentation per TOOL: Ghidra, JWT, CyberChef, Hash-Cracking), `Arsenal/` is
organized by CTF PROBLEM PATTERN: each file describes a way to recognize a kind of challenge and the
method that has already worked to solve it, cross-referencing `Manuals/<Tool>/` when a specific tool
is involved.

It's the library the `/dispatch` command consults (via `scripts/arsenal_search.py`) before proposing
an attack plan. Keep feeding it a new entry for every new pattern you solve.

## Structure

```
Arsenal/<CATEGORY>/<pattern-slug>.md
```

`<CATEGORY>` is one of these 12 codes (the folder must match the frontmatter `category` field):
`CRYPTO` (includes STEGO), `REV`, `PWN`, `FOR`, `JAIL`, `OSINT`, `NET`, `WEB`, `PPC`, `MISC`,
`TRIVIA`, `LLM`.

## Frontmatter (YAML at the top of the file)

```yaml
---
id: slug-kebab-case-unique-matching-the-filename
category: WEB
tags: [keyword, technique, tool]      # lowercase, no accents, flow-style list
tools: [JWT]                                     # name of the folder(s) under Manuals/, or []
manuals: ["Manuals/JWT/3. Contexto para Claude.md"]  # exact paths, or []
title: "Short descriptive title"
difficulty: easy|medium|hard
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: [another-arsenal-id]                   # optional, []
---
```

`tags` is the heaviest field in the FTS5 search. Use technical terms that tend to show up in real
prompts (e.g. `alg-none`, `small-n`, `lsb`, `format-string`), not just the pattern's pretty name.

## File body (suggested sections)

1. **How to recognize this pattern**: signals in the prompt/attachments that point to this vector.
2. **Method**: step by step with commands/code ready to paste.
3. **Gotchas**: common traps, signals that it is NOT this vector (saves contest time).
4. **Related / Cross-reference**: other Arsenal entries or files under `Manuals/`.

## Reindexing

The SQLite index (`Arsenal/.index/arsenal.db`, gitignored) is rebuilt incrementally on every call to
`scripts/arsenal_search.py`. You don't need to run anything manually after creating or editing an
entry. To force a full rebuild: `python3 scripts/arsenal_search.py --reindex --force`.

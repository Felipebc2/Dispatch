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
toolsets: [osint/username]                      # optional: toolsets this method uses
---
```

`tags` is the heaviest field in the FTS5 search. Use technical terms that tend to show up in real
prompts (e.g. `alg-none`, `small-n`, `lsb`, `format-string`), not just the pattern's pretty name.

## File body (suggested sections)

1. **How to recognize this pattern**: signals in the prompt/attachments that point to this vector.
2. **Method**: step by step with commands/code ready to paste.
3. **Gotchas**: common traps, signals that it is NOT this vector (saves contest time).
4. **Related / Cross-reference**: other Arsenal entries or files under `Manuals/`.

## Toolsets (`<CATEGORY>/tools/<type>.json`)

Entries teach the *how*; toolsets list *where*: external services and CLIs, one JSON file per
kind of tool (e.g. `OSINT/tools/username.json`, `NET/tools/vuln-db.json`). The agent never reads
these files. It asks the search script, which prints one line per tool:

```bash
python3 scripts/arsenal_search.py --tools "wifi ssid geolocation" --top 3   # BM25 over all tools
python3 scripts/arsenal_search.py --toolset osint/email --free              # one toolset
```

`--free` keeps tools usable with no payment and no account; `--offline` keeps CLI tools only.
File shape (`type` must equal the filename, `category` the folder):

```json
{
  "type": "username",
  "category": "OSINT",
  "description": "What this toolset covers, one line",
  "tools": [
    {"id": "sherlock", "name": "Sherlock", "url": "https://github.com/sherlock-project/sherlock",
     "desc": "One line, max 100 chars", "tags": ["username", "account-enumeration"],
     "access": "cli", "cost": "free", "auth": "none",
     "query": "sherlock {q}", "checked": "2026-11-13"}
  ]
}
```

- `access`: `web` | `cli` | `api`. `cost`: `free` | `freemium` | `paid`. `auth`: `none` | `account` | `key`.
- `query` (optional): URL template (web/api) or command template (cli) with a `{q}` placeholder,
  so the agent makes one targeted request instead of browsing a homepage.
- `checked`: the date the URL was last confirmed alive. Tool `id`s are unique across all toolsets.
- Only add tools that work today: dead services cost the agent a wasted request.

## Reindexing

The SQLite index (`Arsenal/.index/arsenal.db`, gitignored) is rebuilt incrementally on every call to
`scripts/arsenal_search.py`. You don't need to run anything manually after creating or editing an
entry. To force a full rebuild: `python3 scripts/arsenal_search.py --reindex --force`.

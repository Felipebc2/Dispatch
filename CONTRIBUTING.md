# Contributing to CTF Dispatch

The Arsenal is meant to grow. The most useful contribution is a new **Arsenal entry**: a
problem-pattern to method note for a technique that is not covered yet. Manuals (per-tool references)
are welcome too.

Keep contributions **generic**: reusable technique knowledge, not writeups tied to one event or one
challenge. And only for authorized settings (CTFs, labs, competitions you are playing).

## Add an Arsenal entry

1. Create `Arsenal/<CATEGORY>/<slug>.md`, where `<CATEGORY>` is one of the 12 tags
   (CRYPTO, REV, PWN, FOR, JAIL, OSINT, NET, WEB, PPC, MISC, TRIVIA, LLM) and `<slug>` is a
   kebab-case name that also becomes the frontmatter `id`.
2. Fill the YAML frontmatter following the schema in [`Arsenal/README.md`](Arsenal/README.md).
   Required keys: `id`, `category`, `tags`, `title`, `difficulty` (`easy` / `medium` / `hard`).
   Optional: `tools`, `manuals`, `created`, `updated`, `related`.
3. Write the body: how to recognize the pattern, the method (commands ready to paste), gotchas, and
   cross-references.
4. Run the checks (below), then regenerate the index.

## Add a Manual

Create `Manuals/<Tool>/` with the tool reference. The file `3. Contexto para Claude.md` is the quick
execution reference an Arsenal entry can cite through its `manuals` field.

## Local checks (the same ones CI runs)

```bash
python3 scripts/validate_arsenal.py          # frontmatter schema, id/category/related, manuals paths
python3 scripts/arsenal_search.py --emit-index   # regenerate Arsenal/INDEX.md (commit the result)
python3 scripts/arsenal_search.py "<keywords>" --json   # sanity-check your entry is searchable
```

CI also rejects em-dashes and en-dashes in Markdown. Recompose them with a colon, a comma,
parentheses, or two sentences.

## Open a pull request

1. Fork, then branch: `git checkout -b arsenal/<slug>`.
2. Commit with a [Conventional Commits](https://www.conventionalcommits.org/) message, for example
   `feat(arsenal): add <slug> entry`.
3. Make sure the local checks pass and `Arsenal/INDEX.md` is regenerated.
4. Open the PR against `main` and fill the checklist.

Thanks for growing the Arsenal.

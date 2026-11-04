# Changelog

All notable changes to CTF Dispatch are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] (2026-11-04)

Architecture and polish pass. No breaking changes.

### Added
- Arsenal navigation that scales without loading the corpus: `--tag`, `--graph`, `--list` and `--emit-index` in `arsenal_search.py`.
- `Arsenal/INDEX.md`: a per-category listing plus a Mermaid relationship graph, regenerated from the entries.
- Codex plugin adapter (`.codex-plugin/plugin.json`).
- `docs/ARCHITECTURE.md`: the model-facing vs infra split and the context rule.
- Vector logo (`assets/logo.svg`).

### Changed
- `ctf-solve` now routes through search instead of reading a whole category folder, keeping context small.
- README rewritten with a hero, badges, how-it-works, a Codex install section, and an FAQ.
- Removed em-dashes repo-wide, recomposed for natural reading.

## [0.1.0] (2026-11-04)

First public release.

### Added
- **`/dispatch`** orchestrator: triage → Arsenal lookup → human checkpoint → solver.
- **13 agents**: `brainstormer` (triage) + 12 category solvers (CRYPTO, REV, PWN, FOR, JAIL,
  OSINT, NET, WEB, PPC, MISC, TRIVIA, LLM).
- **`/ctf-dispatch:ctf-solve`** skill: per-category shortcut into the dispatch flow.
- **`/ctf-dispatch:setflag`**: configure the flag format at runtime; also settable at install
  via the `flag_format` plugin option.
- **Arsenal**: ~75 problem-pattern → method entries across the 12 categories, searched with a
  stdlib-only SQLite FTS5 index (`scripts/arsenal_search.py`).
- **Manuals**: per-tool references (Ghidra, CyberChef, JWT, pwntools, Wireshark, sqlmap, …).
- Human-checkpoint safety model: no solver runs without explicit user approval.
- Plugin + marketplace manifests, brand assets (banner, icon, emblem, diagram).

[0.2.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.2.0
[0.1.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.1.0

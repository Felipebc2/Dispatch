# Changelog

All notable changes to CTF Dispatch are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-11-04

First public release.

### Added
- **`/dispatch`** orchestrator — triage → Arsenal lookup → human checkpoint → solver.
- **13 agents** — `brainstormer` (triage) + 12 category solvers (CRYPTO, REV, PWN, FOR, JAIL,
  OSINT, NET, WEB, PPC, MISC, TRIVIA, LLM).
- **`/ctf-dispatch:ctf-solve`** skill — per-category shortcut into the dispatch flow.
- **`/ctf-dispatch:setflag`** — configure the flag format at runtime; also settable at install
  via the `flag_format` plugin option.
- **Arsenal** — ~75 problem-pattern → method entries across the 12 categories, searched with a
  stdlib-only SQLite FTS5 index (`scripts/arsenal_search.py`).
- **Manuals** — per-tool references (Ghidra, CyberChef, JWT, pwntools, Wireshark, sqlmap, …).
- Human-checkpoint safety model: no solver runs without explicit user approval.
- Plugin + marketplace manifests, brand assets (banner, icon, emblem, diagram).

[0.1.0]: https://github.com/Felipebc2/Dispatch/releases/tag/v0.1.0

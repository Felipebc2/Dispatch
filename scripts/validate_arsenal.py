#!/usr/bin/env python3
"""Validate every Arsenal entry's frontmatter against the schema. Stdlib only.

Run locally or in CI:
    python3 scripts/validate_arsenal.py

Exits non-zero and prints one line per problem if any entry is malformed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arsenal_search import ARSENAL_DIR, REPO_ROOT, _entry_files, parse_frontmatter  # noqa: E402

CATEGORIES = {"CRYPTO", "REV", "PWN", "FOR", "JAIL", "OSINT", "NET", "WEB", "PPC", "MISC", "TRIVIA", "LLM"}
DIFFICULTIES = {"easy", "medium", "hard"}
REQUIRED = ("id", "category", "tags", "title", "difficulty")


def validate() -> list[str]:
    files = _entry_files()
    ids = set()
    for p in files:
        meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        if meta.get("id"):
            ids.add(meta["id"])

    errors: list[str] = []
    for p in files:
        rel = p.relative_to(REPO_ROOT)
        meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))

        def err(msg: str) -> None:
            errors.append(f"{rel}: {msg}")

        if not meta:
            err("missing YAML frontmatter")
            continue
        for key in REQUIRED:
            if not meta.get(key):
                err(f"missing or empty required key `{key}`")

        folder = p.parent.name
        if meta.get("id") and meta["id"] != p.stem:
            err(f"id `{meta['id']}` does not match filename `{p.stem}`")
        cat = str(meta.get("category", "")).upper()
        if cat and cat not in CATEGORIES:
            err(f"category `{cat}` is not one of the 12")
        if cat and cat != folder.upper():
            err(f"category `{cat}` does not match folder `{folder}`")
        if "tags" in meta and not isinstance(meta["tags"], list):
            err("tags must be a flow-style list, e.g. [a, b, c]")
        diff = meta.get("difficulty", "")
        if diff and diff not in DIFFICULTIES:
            err(f"difficulty `{diff}` must be one of {sorted(DIFFICULTIES)}")
        for rid in (meta.get("related") or []):
            if isinstance(meta.get("related"), list) and rid not in ids:
                err(f"related id `{rid}` has no matching entry")
        for mp in (meta.get("manuals") or []):
            if isinstance(meta.get("manuals"), list) and not (REPO_ROOT / mp).exists():
                err(f"manuals path `{mp}` does not exist")
        if not body.strip():
            err("empty body")
    return errors


def main() -> None:
    errors = validate()
    total = len(_entry_files())
    if errors:
        for e in errors:
            print(e)
        print(f"\n{len(errors)} problem(s) across {total} entries.")
        sys.exit(1)
    print(f"All {total} Arsenal entries are valid.")


if __name__ == "__main__":
    main()

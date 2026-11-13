#!/usr/bin/env python3
"""Validate every Arsenal entry's frontmatter against the schema. Stdlib only.

Run locally or in CI:
    python3 scripts/validate_arsenal.py

Exits non-zero and prints one line per problem if any entry is malformed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import json  # noqa: E402
import re  # noqa: E402

from arsenal_search import (  # noqa: E402
    REPO_ROOT, _entry_files, _toolset_files, parse_frontmatter, toolset_name,
)

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

    toolsets = {toolset_name(p) for p in _toolset_files()}
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
        for ts in (meta.get("toolsets") or []):
            if isinstance(meta.get("toolsets"), list) and ts not in toolsets:
                err(f"toolset `{ts}` has no matching Arsenal/<CAT>/tools/<name>.json")
        if not body.strip():
            err("empty body")
    return errors


TOOL_REQUIRED = ("id", "name", "url", "desc", "tags", "access", "cost", "auth", "checked")
TOOL_ENUMS = {"access": {"web", "cli", "api"}, "cost": {"free", "freemium", "paid"},
              "auth": {"none", "account", "key"}}
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DESC_MAX = 100


def validate_toolsets() -> tuple[list[str], int]:
    """Check every Arsenal/<CAT>/tools/<type>.json. Returns (errors, tool count)."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    count = 0
    for p in _toolset_files():
        rel = p.relative_to(REPO_ROOT)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{rel}: invalid JSON ({e})")
            continue
        if data.get("type") != p.stem:
            errors.append(f"{rel}: `type` must equal the filename `{p.stem}`")
        if str(data.get("category", "")).upper() != p.parent.parent.name.upper():
            errors.append(f"{rel}: `category` must match folder `{p.parent.parent.name}`")
        if not data.get("description"):
            errors.append(f"{rel}: missing `description`")
        tools = data.get("tools")
        if not isinstance(tools, list) or not tools:
            errors.append(f"{rel}: `tools` must be a non-empty list")
            continue
        for t in tools:
            count += 1
            tid = t.get("id", "?")

            def err(msg: str) -> None:
                errors.append(f"{rel}: tool `{tid}`: {msg}")

            for key in TOOL_REQUIRED:
                if not t.get(key):
                    err(f"missing `{key}`")
            if tid in seen:
                err(f"duplicate id (also in {seen[tid]})")
            seen[tid] = str(rel)
            if not str(t.get("url", "")).startswith(("https://", "http://")):
                err("`url` must start with http(s)://")
            if len(t.get("desc", "")) > DESC_MAX:
                err(f"`desc` longer than {DESC_MAX} chars")
            tags = t.get("tags", [])
            if not isinstance(tags, list) or not all(isinstance(x, str) and TAG_RE.match(x) for x in tags):
                err("`tags` must be a list of lowercase kebab-case strings")
            for key, allowed in TOOL_ENUMS.items():
                if t.get(key) and t[key] not in allowed:
                    err(f"`{key}` must be one of {sorted(allowed)}")
            q = t.get("query")
            if q is not None:
                if "{q}" not in q:
                    err("`query` must contain the {q} placeholder")
                if t.get("access") in ("web", "api") and not q.startswith(("https://", "http://")):
                    err("`query` of a web/api tool must be a URL template")
            if t.get("checked") and not DATE_RE.match(t["checked"]):
                err("`checked` must be YYYY-MM-DD")
    return errors, count


def main() -> None:
    tool_errors, n_tools = validate_toolsets()
    errors = validate() + tool_errors
    total = len(_entry_files())
    if errors:
        for e in errors:
            print(e)
        print(f"\n{len(errors)} problem(s) across {total} entries and {n_tools} tools.")
        sys.exit(1)
    print(f"All {total} Arsenal entries and {n_tools} tools in {len(_toolset_files())} toolsets are valid.")


if __name__ == "__main__":
    main()

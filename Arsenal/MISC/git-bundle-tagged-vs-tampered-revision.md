---
id: git-bundle-tagged-vs-tampered-revision
category: MISC
tags: [git, git-bundle, bundle, repository, version-control, annotated-tag, signed-tag, gpg, verify-tag, signed-commit, tampered-head, revision, git-show, git-log, for-each-ref, clone-mirror, refs, replace-refs, history, decoy]
tools: []
manuals: []
title: "Git bundle: read the signed/tagged revision, not the tampered HEAD"
difficulty: easy
created: 2026-11-06
updated: 2026-11-06
related: []
---

## How to recognize this pattern

- A `.bundle` attachment: `file` says `Git bundle`, the first line is `# v2 git bundle` or
  `# v3 git bundle`, followed by `<sha> <ref>` lines.
- The prompt qualifies **which** revision: "the one the officer signed", "approved", "original",
  "before it was changed", "as of <date>". HEAD carries plausible but wrong values (and often a
  README that "confirms" them).

## Method

### 1. List refs and clone every one of them
```bash
head -5 chall.bundle                       # refs are listed in plain text
git bundle list-heads chall.bundle
git clone --mirror chall.bundle repo.git   # all refs (tags, notes, odd namespaces), bare
cd repo.git
git for-each-ref                           # branches, tags (object type tag = annotated), notes
git log --all --graph --oneline --decorate
```
A plain `git clone` only checks out HEAD and may skip tags or refs outside `refs/heads`.
`git bundle verify` needs to run inside some repository (`git --git-dir repo.git bundle verify ...`).

### 2. Map the wording to a ref
```bash
git cat-file -p <tag>                      # tagger, date, message, PGP SIGNATURE block if signed
git verify-tag <tag>                       # needs the public key; a signature block alone still marks it
git log --all --format='%h %G? %an %ad %s' # %G? = commit signature status (G/B/U/N...)
git log --all --format='%h %ai %ci %an <%ae> %cn %s'   # author vs committer dates and identities
```
"Signed" usually means an annotated or GPG-signed tag, or a signed commit. "Original" means the
earliest commit touching the file (`git log --follow --diff-filter=A -- file`).

### 3. Read files at that revision and diff against HEAD
```bash
git show <tag>:path/file.txt
git ls-tree -r <tag>
git diff <tag> HEAD --stat; git diff <tag> HEAD -- path/file.txt
```
Everything changed after the signed point is suspect: totals, rules ("add every line"), unit
definitions. Recompute derived answers from the signed revision's own files and rules.

## Gotchas

- Read every file at the same revision: mixing a rule from HEAD with data from the tag gives a wrong
  total.
- `refs/replace/*` silently swaps objects in `log`/`show`. Check `git for-each-ref refs/replace` and
  use `git --no-replace-objects` when content looks inconsistent.
- Also inspect `refs/notes/*` (`git log --notes=*`), `refs/stash`, and dangling objects
  (`git fsck --lost-found`, mostly relevant for full `.git` dirs, not bundles).
- A bundle with prerequisite lines (`-<sha>`) is incomplete: it needs a base repo to unpack.
- Commit and tag dates are attacker-controlled; trust the ref the question names, not timestamps.
- NOT this pattern: a full `.git` directory leaked over HTTP (dump it with `git-dumper` first), or
  secrets removed from history (then `git log -p --all -S 'flag'` across all commits).

## Cross-reference

No tool manual. For history-wide secret search use `git log -p --all -S '<string>'` and
`git rev-list --all | xargs git grep '<string>'`.

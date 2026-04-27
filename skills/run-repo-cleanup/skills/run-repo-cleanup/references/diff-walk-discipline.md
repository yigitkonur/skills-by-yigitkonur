# Diff-Walk Discipline (Phase 1)

**Rule:** every commit is based on reading the actual diff. No exceptions. No `git commit -am`. No blind stage-everything.

## Why

Blind-stage-everything commits are the single biggest cause of:
- Committed `.env` / credentials.
- Committed session artifacts.
- Mixed-concern commits that are impossible to revert cleanly.
- "I don't remember why I changed this" questions months later.

Reading the diff before staging is a 30-second cost that saves hours. Always.

## The walk — per file

```bash
# 1. See ALL dirty files, grouped mentally
git status --short

# 2. For EACH file, read its diff
git diff <file>          # unstaged changes
git diff --cached <file> # already-staged changes, if any

# 3. Decide: which concern is this?
#    Write the concern down (out loud, in a note, anywhere).
#    If you can't name the concern in one sentence, you don't
#    understand the change. Read the surrounding code.

# 4. Stage only files that belong to this concern
git add <file-1> <file-2>

# 5. Re-read what you JUST staged
git diff --cached

# 6. Commit with a message that names the concern
git commit -m "<emoji> <type>(<scope>): <subject>"
```

The re-read at step 5 catches "oh, that hunk wasn't supposed to be here" — you can unstage with `git restore --staged <file>` and try again.

## Hunk-level splits (`git add -p`)

When one file has two unrelated changes (typo fix + refactor, for example), you want them in separate commits:

```bash
git add -p <file>
```

Keys during interactive stage:
- `y` — stage this hunk
- `n` — skip this hunk (leaves it unstaged)
- `s` — split this hunk into smaller pieces (then prompts again)
- `e` — edit the hunk manually (opens editor for the patch)
- `q` — quit without staging remaining

Then:

```bash
git diff --cached       # sanity check — only the concern you want
git commit -m "fix(typo): ..."

git add <file>          # stage what's left
git diff --cached       # verify
git commit -m "refactor(foo): ..."
```

## The "describe in one sentence" test

Before you type `git commit`, describe the change in one sentence. If the sentence is:

- ✅ "Rename the auth middleware function to match the new API contract."
- ✅ "Fix typo in README installation step."
- ✅ "Add `to-delete/` to `.gitignore`."

You're good. If it's:

- ❌ "Bunch of fixes and cleanup." → Split.
- ❌ "Update stuff and also the docs." → Split.
- ❌ "Various improvements." → Split.
- ❌ "WIP." → Not a commit. Stash or split further.

A vague sentence means a vague commit. Vague commits make the entire history harder to bisect, revert, and understand. Split until every commit has a crisp one-sentence name.

## Walking a 20-file dirty tree

Real example: you open the repo and `git status --short` shows 20 modified files. How to walk it:

1. **Scan once, group mentally.** Look at the paths, not the diffs:
   - `src/features/Foo/*` → feature work.
   - `docs/*` → documentation.
   - `scripts/*` → tooling.
   - Some root files (`index.html`, `package.json`) — which group?
2. **Read the root-file diffs first.** They're usually the glue. `git diff index.html` tells you if the root change belongs with the feature or the docs or neither.
3. **Pick the smallest obvious group.** Usually a docs-only or typo-only cluster. Commit it first — quick win, smaller dirty tree.
4. **Repeat.** Next-smallest group, commit, repeat.
5. **Last one or two files are the weird orphans.** These are the ones that nearly went into the wrong commit. Read carefully; sometimes the answer is "move to `to-delete/`".

Goal: end with `git status --short` empty or containing only `to-delete/` entries (ignored).

## Files you should NOT commit

Read them if present. Usually they belong in `.gitignore` or `to-delete/`:

- `.env*` — secrets.
- `*.pem`, `id_rsa*` — keys.
- `.continues-handoff.md`, `.claude-session*`, `.cursor-session*`, `.aider*` — AI session.
- `scratch/`, `tmp/`, `notes.local.md` — personal scratch.
- Large binary blobs you didn't author (caches, builds).

Phase 0 should have added these to `.gitignore` already. If they show up in `git status` as tracked, that's a previous-commit bug — untrack with `git rm --cached <file>` and add to `.gitignore` in a `chore(git): ...` commit.

## What a good commit looks like

```
git log --oneline -5
8516e69 ✨ feat(wope-lockdown): brand + behavior lockdown layer
ac3b45f 📝 docs(wope): document lockdown layer + GitHub policy in AGENTS.md
c4a5134 📝 docs(wope): add per-folder Wope Context blocks to 9 nested AGENTS.md
6c140c3 📝 docs(wope): Wope Context blocks for globalConfig + Analytics
```

Each line describes exactly one thing that changed and why. None says "various".

## Common mistakes

| Mistake | Fix |
|---|---|
| `git add .` on a 20-file tree | Stage per-concern |
| `git commit -am "…"` | Read diff first |
| Re-reading only subject, not diff | `git diff --cached` before commit |
| "I'll split it later" | Split now; "later" is never |
| Committing to rescue yourself from a merge conflict | Resolve the conflict, then do a clean diff-walk |
| Treating dirty tree as one unit | It's N units — find the N |

## Diff-walk red flags

- "It's easier to commit all of it and clean up in the PR." → No. You can't clean up history without force-push.
- "I know what's in there." → Read it anyway. Memory lies.
- "This hunk is unrelated but tiny, let me keep it here." → Split.
- "`git add -p` is too slow." → Faster than fixing a bad commit.

## The mindset

The diff is the *source of truth* for what you're committing. The sentence you'd say out loud is the test for whether the diff matches the concern. Everything else is ritual you skip at your own peril.

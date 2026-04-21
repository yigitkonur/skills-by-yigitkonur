# Understanding What Was Reviewed — The Fallback Chain

The reviewer evaluates *some* set of changes. Before you can judge their feedback, you need to reconstruct that set independently — do not trust the reviewer's description of "the changes" as the ground truth. Reviewers get the diff wrong constantly (stale PRs, edited commits, wrong base, bot confusion).

## The fallback chain

Try these in order. Stop at the first one that produces a complete picture.

### Layer 1: Git commits (gold standard)

If the branch has commits ahead of the base, the diff is the ground truth.

```bash
# What commits are in scope?
git log --oneline origin/main..HEAD

# The full diff
git diff origin/main...HEAD

# Per-file change stats
git diff --stat origin/main...HEAD

# Per-commit breakdown (useful for reviewing commit-by-commit feedback)
git log origin/main..HEAD --patch --stat
```

Record:
- list of changed files with net line deltas
- commit boundaries (one reviewer comment may apply to one specific commit)
- rename/move operations (`git log --follow` if a reviewer's line reference seems off)

If the base branch is not `main`, swap in the correct base (`--base` from `gh pr view` for PR mode).

### Layer 2: Edit/Write tool outputs from this session

If the changes haven't been committed yet (typical for in-session review: "you just did X, the reviewer said Y about it"), reconstruct from the session's tool-call history.

In Claude Code, walk back through the conversation and look for:

- **Edit tool calls** that returned success — each reveals `{file_path, old_string, new_string}`. The file was modified.
- **Write tool calls** that returned success — each reveals `{file_path, content}`. The file was created or overwritten.
- **NotebookEdit tool calls** (if any) — same principle for `.ipynb` files.

For each successful tool call, record:
```
{source: "Edit" | "Write", file: <absolute-path>, timestamp: <relative-order>}
```

A representative reconstruction output:

```
Ground-truth changes (from Edit/Write trail, no commits):
  Write: /path/to/new/file.ts (created, ~47 lines)
  Edit:  /path/to/existing.ts (3 edits — line-range indeterminate, use current file state vs. memory)
  Edit:  /path/to/config.json (1 edit)
```

**Caveat:** tool trail does not show you the *before* state. If a reviewer comments "line 42 is wrong", you know `line 42` *now* but not what it was pre-edit. If a before-state matters, read the git diff against HEAD (if there are no local commits, diff against the index or an earlier HEAD if the file was committed before the edits).

### Layer 3: Bash commands affecting files

File operations via Bash don't show in Edit/Write logs. Scan for:

- `rm <path>` / `rm -rf <dir>` — deletion
- `mv <src> <dst>` — rename/move
- `cp <src> <dst>` — copy (creates destination)
- `mkdir <dir>` — new directory
- `touch <file>` — new empty file
- `> <file>` or `>> <file>` (redirect) — overwrite/append
- `sed -i ... <file>` — in-place edit (some agents avoid this in favor of the Edit tool for auditability; still worth tracking as a file operation)
- `git mv`, `git rm` — tracked move/delete

Record these alongside the Edit/Write trail to get a full picture of file-level operations.

### Layer 4: Explicit uncertainty

If none of Layers 1-3 produce a complete picture, **say so**. Do not proceed to evaluate feedback against an uncertain ground truth.

```
"Ground truth uncertain — no commits ahead of main, no Edit/Write calls
 in this session's visible history, no obvious Bash file operations.
 Please clarify which files / changes the reviewer is commenting on."
```

## Reconciling reviewer references to ground truth

Once you have the ground-truth change set, check each feedback item's reference:

| Reviewer reference | Check |
|---|---|
| `path/foo.ts:L42` | Is `path/foo.ts` in the change set? Does L42 match something the change touched? |
| `path/foo.ts` (no line) | Is `path/foo.ts` in the change set? |
| "the retry loop" (no path) | What in the change set implements a retry loop? Find the matching path+line yourself. |
| "the whole change" | The entire diff — apply the feedback across the diff, flag items the reviewer might have missed |

If a reviewer reference points at code **not in the change set** — the reviewer is either commenting on the wrong PR, looking at a stale diff, or raising a pre-existing concern. Flag it: "Comment points to `path/bar.ts:L12` which is not in this change set. Out of scope or pre-existing?"

## Commit-boundary awareness

When the PR has multiple commits, reviewer comments sometimes pin to a specific commit. The `comment.commit_id` field on `gh api repos/{o}/{r}/pulls/{N}/comments` tells you which commit the reviewer was viewing.

If the commit_id is not `HEAD`, the reviewer was looking at an earlier state. Either:

1. Re-evaluate against the current HEAD (usual case — the author pushed more commits after the review)
2. Evaluate at the commit_id (if the reviewer explicitly said "this is the state I'm reviewing")

Record the `commit_id` for each comment so the verdict can reference it.

## Recipes

### Quick change-set extraction

```bash
# Summary block for any mode
echo "=== CHANGED FILES ==="
git diff --stat origin/main...HEAD 2>/dev/null || echo "(no commits ahead of main)"

echo "=== COMMITS ==="
git log --oneline origin/main..HEAD 2>/dev/null || echo "(no commits ahead of main)"

echo "=== WORKING-TREE STATUS ==="
git status --short
```

### Tool-trail reconstruction prompt

When walking back through the session, look for message patterns like:
- `"name": "Edit", "input": {"file_path": "..."}`
- `"name": "Write", "input": {"file_path": "..."}`

A scripted approach is overkill; a visual scan of the recent conversation is usually enough.

### Cross-checking a reviewer's line reference

```bash
# Does the reviewer's line reference match current file state?
sed -n '40,45p' path/foo.ts     # show lines 40-45 of current file

# Does it match the pre-change state?
git show HEAD:path/foo.ts | sed -n '40,45p'
```

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| "Trust the reviewer's description of what changed" | Reconstruct independently. Reviewers get diffs wrong. |
| "All feedback applies to the current HEAD" | Check `comment.commit_id` — reviewer may be on an older state. |
| "The changes are whatever the PR body says" | PR bodies describe *intent*, not the actual diff. Read the diff. |
| "I can skip the reconstruction if the reviewer cites line numbers" | Line numbers drift between revisions. Verify. |
| "No commits means no changes" | Edit/Write tool trail is valid ground truth in-session. |

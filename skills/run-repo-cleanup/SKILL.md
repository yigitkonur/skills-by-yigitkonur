---
name: run-repo-cleanup
description: "Use if finishing a project — review and merge every branch/worktree into main, retire dead branches."
---

# Run Repo Cleanup

You ran a project. You spawned branches and parallel worktrees. Now you are done and the repo is a mess: live branches, worktrees, a dirty tree, and AI/dev artifacts scattered around. This skill sweeps all of that into a clean end state:

- Every **live** branch and worktree is **reviewed like a human dev and merged into the main branch** — locally, with `git merge --no-ff`. **No PRs. No fork. No remote review process.**
- **Zero dangling branches** afterward — none local, none on the remote.
- Every **stale or conflicting** branch is **reported, never silently dropped**.
- Every **non-essential file** (including hidden ones) is moved to a gitignored `to-delete/` trash; docs are consolidated into a gitignored `docs/`.
- A **trustworthy report** tells you exactly what happened — and a re-run on an already-clean repo says "nothing to do."

This is a *finishing* tool. Run it when the work is done, not mid-feature.

## When To Use

Trigger on phrases and git states like:

- *"clean up this repo"*, *"tidy up — I'm done"*, *"sweep this before I move on"*
- *"merge my branches into main"*, *"I have N worktrees from parallel agents — merge them in"*
- *"retire the stale branches"*, *"no dangling branches left anywhere"*
- Git state: ≥1 unmerged branch, *or* `git worktree list` shows ≥2 entries, *or* a dirty working tree after a finished task.

Do **NOT** use this skill for:

- *Mid-feature work* — this finalizes; it assumes the work is done.
- *Opening pull requests* — this skill deliberately does not. If you want fork-PRs, that is a different tool.
- *Reviewing someone else's PR* — use `review-pr`.
- *Runtime debugging* — use `debug-runtime`.

## Pinned Defaults

Decided once; override per-project only if the repo says otherwise (`AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` win over this skill).

| Key | Default | Why |
|---|---|---|
| **main branch** | `main` (else `master` / repo convention) | merge target. |
| **stale cutoff** | **7 days** since last commit | older branches are reported, not auto-merged. See `references/merge-rules.md`. |
| **merge mode** | `git merge --no-ff` | keeps each branch's history as a revertable unit. |
| **"significant" change** | >300 changed lines **or** >10 files | triggers a review subagent before merging. |
| **conflict policy** | understand → resolve with reasoning, else **skip + report** | never blind-resolve. |
| **commit style** | Conventional Commits + gitmoji | for committing the dirty tree. See `references/conventional-commits.md`. |
| **keep at root** | `README*`, `AGENTS.md`, `CLAUDE.md`, `LICENSE*`, source + build/config | everything else is sweep-eligible. See `references/to-delete-and-docs.md`. |

## Non-Negotiable Safety Rails

1. **Read the diff and commit messages before merging any branch.** A merge is a decision, not a button. You must be able to say in one sentence what each branch does. See `references/merge-rules.md`.
2. **Never blind-resolve a conflict.** Read both sides, read the commit messages, understand intent. Resolve only when you understand it; otherwise abort the merge and report the branch as `skipped-conflict`. A skipped branch is a clean outcome; a wrongly-resolved conflict is silent data loss.
3. **Move, don't `rm`.** Anything non-essential goes to `to-delete/` (gitignored), never deleted outright. The owner reviews later. See `references/to-delete-and-docs.md`.
4. **Commit the dirty tree before merging anything.** You cannot merge into a dirty working tree. Diff-walk the dirty files into conventional commits first (Phase 1).
5. **Never force-push or rewrite published history** unless explicitly asked. This skill works locally; deletion of *merged* remote branches is the only remote mutation, and only after `git fetch --prune`.
6. **Stale ≠ delete.** A branch older than the cutoff is *reported and skipped by default*, not merged and not deleted, unless you confirm it is real work worth keeping. Old + disconnected from current code is the classic "ignore it" case.
7. **Every mutating script defaults to dry-run.** `--execute` is required to change state. Always read the dry-run first.

## The Six Phases

```
        live branches + worktrees + dirty tree + AI artifacts
                              │
   Phase 0 — Inventory: every branch w/ age + merged-status, worktrees, dirty files
                              │
   Phase 1 — Commit the dirty tree (diff-walk → conventional commits)
                              │
   Phase 2 — Merge plan: order live branches foundation→leaf; flag stale
                              │
   Phase 3 — Reviewed merge into main: read diff, subagent if big, --no-ff, skip-on-conflict
                              │
   Phase 4 — Aggressive sweep: non-essential → to-delete/, docs → docs/, both gitignored
                              │
   Phase 5 — Retire + verify + REPORT: prune merged branches local+remote, remove worktrees
                              │
        main holds all live work · zero dangling branches · clean tree · a report you trust
```

Each phase gates the next. If you are tempted to skip one, re-audit instead.

---

## Phase 0 — Inventory

**Think first:** *"What branches exist, how old is each, what's already merged, and what's genuinely live work?"*

Run the read-only inventory:

```bash
python3 scripts/audit-state.py --base main           # human report
python3 scripts/audit-state.py --base main --json    # machine-readable, for the report
```

It reports, per branch (local **and** remote-only):
- last-commit date + **age in days**
- commits ahead/behind `main`
- already merged into `main`? (these go straight to Phase 5 retirement)
- files touched, dirty status

…plus all worktrees (branch, dirty count, ahead-of-main) and the dirty working tree grouped by directory.

**Classification** (the script does this; you verify):
- **`already-merged`** → nothing to merge; retire in Phase 5.
- **`active`** (≤ 7 days) → merge in Phase 3.
- **`stale`** (> 7 days, unmerged) → **report and skip by default.** Merge only if you confirm it is real, still-relevant work. Old + philosophically disconnected from current code → leave it, note it in the report.

**Gate → Phase 1 when:** you have the branch inventory and no in-progress rebase/merge/cherry-pick (the script warns on mid-operation; finish or abort it first).

---

## Phase 1 — Commit the Dirty Tree

**Think first:** *"You can't merge into a dirty tree. What concern does each uncommitted hunk belong to?"*

For every modified file `git diff <file>`; for every untracked file read it. Then stage and commit **one concern at a time** — never `git commit -am`:

```bash
git diff <files-for-this-concern>
git add <files-for-this-concern>
git diff --cached
git commit -m "<emoji> <type>(<scope>): <imperative subject>"
```

Type/scope/gitmoji registry: `references/conventional-commits.md`. Uncertain files do **not** get committed — they get swept in Phase 4. 

**Gate → Phase 2 when:** `git status --short` is empty (the only remaining untracked items, if any, are headed for `to-delete/`).

---

## Phase 2 — Merge Plan

**Think first:** *"If I merge A before B, does B then conflict or rebase cleanly? Which branch is the foundation?"*

Skip to Phase 3 if there is exactly one live branch. With two or more (the parallel-worktree case — could be 25):

```bash
python3 scripts/plan-merge-order.py --base main --stale-days 7
python3 scripts/plan-merge-order.py --base main --stale-days 7 --json
```

The heuristic: a branch whose files are also touched by other branches is more **foundational** (merge it first so later branches merge onto a more-complete base); independent leaves merge last; **stale** branches are listed separately for skip-unless-confirmed. Recency is a factor — newer foundational work sorts ahead of older.

**You decide the final order.** The script suggests; override when semantics demand it (e.g. "tests for X must merge after X"). Reasoning model + the 25-worktree worked example: `references/merge-rules.md`.

**Gate → Phase 3 when:** you have an ordered list of `active` branches to merge and an explicit decision on each `stale` one.

---

## Phase 3 — Reviewed Merge Into Main

**Think first:** *"Would a human dev merge this branch as-is? What does it actually do?"*

Get on the main branch first, working tree clean. Then, **for each branch in the planned order**:

1. **Read it.** `git log --oneline main..<branch>` for the commit messages, `git diff main...<branch>` for the change. Name what the branch does in one sentence.
2. **Subagent-review if significant** (>300 lines or >10 files): dispatch a subagent to read the branch's diff and report whether it's safe to merge, what it touches, and any risk. Treat its report as a claim — spot-check before trusting.
3. **Merge with `--no-ff`:**

   ```bash
   # dry-run the whole set first to see which branches conflict
   python3 scripts/merge-branches.py --base main --branches feat/a feat/b docs/c

   # then merge for real, in your chosen order
   python3 scripts/merge-branches.py --base main --branches feat/a feat/b docs/c --execute
   ```

   The script merges each branch `--no-ff --no-commit` to detect conflicts *without* committing; clean merges it commits, conflicted merges it `git merge --abort`s and records as `skipped-conflict`. It **never resolves conflicts** — that's your judgment call.

4. **On a reported conflict:** do it by hand. Read both sides + the commit messages, understand the intent, resolve, `git diff --cached`, commit. If you can't resolve it confidently, leave the branch unmerged and let the report flag it. Do not guess.

**Gate → Phase 4 when:** every `active` branch is either merged into main or explicitly recorded as `skipped-conflict` / `skipped-stale`.

---

## Phase 4 — Aggressive Sweep

**Think first:** *"What in this tree is needed to run, build, or understand the project? Everything else is trash."*

Move aggressively — it's reversible (everything goes to a gitignored trash, nothing is deleted):

```bash
python3 scripts/sweep-artifacts.py            # dry-run: shows what moves where
python3 scripts/sweep-artifacts.py --execute  # move for real
```

The script:
1. Ensures `to-delete/` and `docs/` exist and are in `.gitignore` (adds them if missing).
2. **Moves non-essential files into `to-delete/`** — including hidden files/folders: handoff notes, `*.claude-session*`, `.aider*`, `derailment-notes/`, scratch scripts, stray plans, secrets, unknown binaries. Be aggressive.
3. **Consolidates docs into `docs/`** — stray `*.md` (outside the keep-list) and doc-like folders (`agent-docs/`, `notes/`) are merged into a single `docs/`. Multiple doc folders always unify into one `docs/`.
4. **Keeps at root:** `README*`, `AGENTS.md`, `CLAUDE.md`, `LICENSE*`, and everything required to run/build (source, `package.json`, lockfiles, configs).

Anything the script is unsure about it lists rather than moving — you make the call. Full keep/move rules + the rationale for gitignoring `docs/`: `references/to-delete-and-docs.md`.

**Gate → Phase 5 when:** the working tree contains only essential, tracked files (plus the gitignored `to-delete/` and `docs/`).

---

## Phase 5 — Retire, Verify, Report

**Think first:** *"Did I leave anything dangling? Can I prove the repo is clean?"*

### 5.1 Retire merged branches + worktrees

```bash
git fetch --all --prune                                          # accurate remote view first
python3 scripts/retire-merged-branches.py --base main            # dry-run
python3 scripts/retire-merged-branches.py --base main --execute  # delete merged local + remote + worktrees
```

The script refuses to delete the main branch, the current branch, or any branch **not** fully merged into `main`. It removes worktrees whose branch is merged. Stale, unmerged branches you chose to skip are **kept** and named in the report — they are not dangling, they are deliberately retained.

### 5.2 Verify — all must be true

- [ ] `git status --short` empty.
- [ ] `git worktree list` shows only the main worktree (or only deliberately-kept ones).
- [ ] `git branch -vv` shows only the main branch + deliberately-kept stale branches. No merged branch lingering.
- [ ] `git branch -r` (post-prune) shows no merged remote branch lingering.
- [ ] `python3 scripts/audit-state.py --base main` reports CLEAN (exit 0).

### 5.3 The report

Produce the report the owner actually wants — generate it from the JSON the scripts emit:

```bash
python3 scripts/audit-state.py --base main --json   # before/after states feed the report
```

The report must state, per branch:

| Branch | Age | What it did (from commits) | Disposition |
|---|---|---|---|
| `feat/x` | 2d | "add export endpoint" | **merged-now** → deleted local+remote |
| `fix/y` | 1d | "null-check in parser" | **already-merged** → deleted |
| `feat/z` | 40d | "old spike, conflicts" | **skipped-stale** → kept, review manually |
| `docs/w` | 3d | "rewrite README" | **skipped-conflict** → kept, conflicts with #… |

And the artifact summary: how many files moved to `to-delete/`, what got consolidated into `docs/`.

**Idempotency:** on a re-run of an already-clean repo, every branch is `already-merged` or absent, nothing moves, and the report says **"Repo is clean — nothing to do."** That is the success signal for "I ran it again and everything was fine."

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Merging a branch without reading its diff/commits | Read first. Name it in one sentence (Phase 3.1). |
| Blind-resolving a conflict to "make it merge" | Understand intent or skip + report. Never guess. |
| Merging a stale, disconnected branch by default | Stale = skip + report unless you confirm it's real. |
| Auto-merging 25 worktrees in finish-order | Plan the order foundation→leaf first (Phase 2). |
| `rm` an unknown file | Move to `to-delete/`. |
| Deleting an unmerged branch | The retire script refuses — don't `--force` it. Merge or keep. |
| Forgetting `git fetch --prune` before retiring | Stale refs → wrong merged-status. Always prune first. |
| Re-run produces a confusing diff | A clean re-run must say "nothing to do." If it doesn't, read the inventory. |

## Scripts

All Python 3 stdlib only — no deps, no `.env`, no secrets. Every mutating script defaults to dry-run.

| Script | Phase | Purpose | Mutates? |
|---|---|---|---|
| `scripts/audit-state.py` | 0 / 5 | Inventory: branches with age + merged-status, worktrees, dirty tree. JSON feeds the report. | No |
| `scripts/plan-merge-order.py` | 2 | Order live branches foundation→leaf; flag stale. | No |
| `scripts/merge-branches.py` | 3 | Merge branches into base `--no-ff`; abort + report conflicts (never resolves). | Yes (`--execute`) |
| `scripts/sweep-artifacts.py` | 4 | Move non-essential files → `to-delete/`; consolidate docs → `docs/`; manage `.gitignore`. | Yes (`--execute`) |
| `scripts/retire-merged-branches.py` | 5 | Delete merged local+remote branches + worktrees. Refuses unmerged. | Yes (`--execute`) |
| `scripts/list-worktrees.py` | 0 / 2 | Enumerate worktrees with branch + dirty + ahead-of-base. | No |

## References

- `references/merge-rules.md` — recency policy, foundation→leaf ordering, the 25-worktree example, conflict handling, when to dispatch a review subagent, `--no-ff` rationale.
- `references/to-delete-and-docs.md` — what's essential vs sweep-eligible (incl. hidden files), the `to-delete/` trash pattern, docs consolidation into a single gitignored `docs/`, `.gitignore` management.
- `references/conventional-commits.md` — type + scope registry, gitmoji, body/footer, breaking-change notation (for Phase 1).

## Bottom Line

Inventory by age → commit the dirty tree → plan the merge order → review each branch and merge it into main → sweep the trash → retire every merged branch local and remote, then report. Nothing dangling, nothing merged blindly, nothing deleted that you didn't see. Run it when you're done; run it again and it tells you you're clean.

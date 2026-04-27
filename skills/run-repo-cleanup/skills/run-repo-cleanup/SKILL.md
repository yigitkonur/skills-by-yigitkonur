---
name: run-repo-cleanup
description: Use skill if you are sweeping dirty working tree, unpushed commits, or multiple worktrees into conventional commits grouped into contextually separated private-fork pull requests with self-review bodies.
---

# Run Repo Cleanup

The job: turn a messy repo — dirty working tree, unpushed commits, possibly multiple worktrees from parallel subagents — into a small number of focused PRs on the **private fork only**, each with diff-read commits inside and a comprehensive self-review body outside. End state must be **tidy**: no stale branches local or remote, no stale worktrees, working tree clean.

## Pinned Defaults

Fill these once per project. If any cell is blank, ask — do not guess.

| Key | Value |
|---|---|
| **origin (private fork)** | `git@github.com:<owner>/<repo>.git` |
| **upstream (read-only)** | `git@github.com:<upstream-owner>/<upstream-repo>.git` |
| **default base branch** | `main` (or `canary` / repo-local convention) |
| **PR body soft cap** | 50,000 characters (GitHub hard limit: 65,536) |
| **commit style** | Conventional Commits + gitmoji prefix (e.g. `✨ feat(scope): ...`) |

If the repo has its own `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md`, those win over anything here. This skill is the fallback when the repo is silent.

## Non-Negotiable Safety Rails

1. **`origin` is the private fork. `upstream` is read-only.** Every mutating `gh` command takes `--repo <fork-owner>/<fork-repo>` explicitly. `gh` CLI defaults are wrong often enough that you never rely on them.
2. **No `.env`, no secrets, no session artifacts in git.** `.env`, `*.pem`, `id_rsa*`, `.continues-handoff.md`, `*.claude-session*`, `derailment-notes/`. If project policy forbids `.env`, hardcode values into the scripts that need them — only when the repo is confirmed private.
3. **Never commit without reading `git diff` first.** Diff → stage → `git diff --cached` → commit. No `git commit -am`. No blind stage-everything. (See `references/diff-walk-discipline.md`.)
4. **Never touch `main` directly.** Branch first, always.
5. **Never force-push or amend published commits** unless the user explicitly asks. A revert commit beats a history rewrite almost every time.
6. **One concern per commit. One intent per PR.** If you can't describe a commit in one sentence, split it. If you can't describe a PR in one line, split it.

## The Five Phases

```
                dirty tree / unpushed / N worktrees
                              │
       Phase 0 — pre-flight audit (.gitignore, worktrees, remotes, surprises)
                              │
       Phase 1 — diff-walk → conventional commits (+ to-delete/ for unsure files)
                              │
       Phase 2 — multi-worktree merge ordering (if N > 1)
                              │
       Phase 3 — commits → contextually separated PRs on the fork
                              │
       Phase 4 — PR body = self-review (≤ 50k chars)
                              │
       Phase 5 — post-PR verification + tidy: retire merged branches & worktrees
                              │
                   tidy repo, reviewable PRs, nothing stale
```

Each phase has a checkpoint. Do not skip forward. If you find yourself tempted to skip, that is a red flag — re-audit.

---

## Phase 0 — Pre-flight Audit

**Think first:** "What state am I actually in? What would surprise me?"

1. **Read `.gitignore`.** Know what's already ignored. Extend it (once) with session artifacts + `to-delete/`. See `references/pre-flight-audit.md` and `references/to-delete-folder.md`.
2. **Run `python3 scripts/audit-state.py`** — read-only state dump: current branch, remotes, dirty files grouped by domain, unpushed commit count, worktrees, open PRs on fork vs upstream. See `scripts/audit-state.md`.
3. **List worktrees** explicitly if the output above is unclear: `python3 scripts/list-worktrees.py`. See `scripts/list-worktrees.md`.
4. **Initialize the `to-delete/` pattern** if not present: `python3 scripts/init-to-delete.py`. Idempotent. See `scripts/init-to-delete.md` and `references/to-delete-folder.md`.
5. **Verify remotes.** `git remote -v` must show `origin` = private fork, `upstream` = read-only source. If not, stop and fix before anything else. See `references/fork-safety.md`.

**Gate:** enter Phase 1 only when (a) no in-progress rebase / merge / cherry-pick / bisect, (b) `origin` is verified as the fork, (c) `.gitignore` is up to date.

**Phase 0 red flags:**
- Surprise branch (you're on `main` instead of `feat/*`).
- Surprise remote (`origin` points at upstream).
- In-progress operation (rebase / merge / cherry-pick).
- Existing worktrees you didn't create — may be a parallel subagent's work.

---

## Phase 1 — Dirty Tree → Conventional Commits (Diff-Walk)

**Think first:** "For each hunk, which logical concern does it belong to? If I can't name the concern, I don't understand the change yet."

### 1.1 Read before you stage

For every modified file: `git diff <file>`. For every untracked file: `cat <file>` (or open it). Never stage a change you have not read.

### 1.2 Group by domain, not by file

Typical split for a feature branch:
- Feature code.
- Docs / README / AGENTS.md updates for the feature.
- Env / config / scripts scaffolding.
- Drive-by fixes unrelated to the feature → **separate branch/PR**.

If one file contains two unrelated concerns, split with `git add -p`. See `references/diff-walk-discipline.md`.

### 1.3 Move uncertain files to `to-delete/`

Instead of `rm`, move anything you're not sure should live in the repo (AI session artifacts, stray scratch scripts, orphan docs) into `to-delete/`. That folder is in `.gitignore` (step 0.4), so moved files disappear from `git status`. The owner can review later and either promote them back or delete for real.

**Do not** delete unknown files yourself. Move them. See `references/to-delete-folder.md`.

### 1.4 Stage + commit one concern at a time

```
git diff <files-for-this-concern>
git add <files-for-this-concern>
git diff --cached
git commit -m "<emoji> <type>(<scope>): <imperative subject>"
```

`git diff --cached` before commit catches "oops, that hunk wasn't supposed to be in this commit". See `references/conventional-commits.md` for the full type + scope registry.

### 1.5 Sweep loose scripts and docs into the project layout

If cleanup uncovered scripts or docs sitting outside the repo's conventions, relocate them before committing:
- **Scripts:** `scripts/<comprehensive-name>.<ext>` paired with `scripts/<comprehensive-name>.md` (same base name). Every script gets a doc.
- **Docs:** `docs/<context>/NN-title-slug.md` — numbered atomic docs per context. `NN` is a zero-padded integer enforcing read order.

See `references/scripts-and-docs-layout.md`.

**Phase 1 gate:** `git status --short` returns empty (or only deliberate untracked items under `to-delete/`). Every commit message passes "describe in one sentence".

**Phase 1 red flags:**
- `git diff` output you skimmed but didn't actually read.
- "Let me bundle these together, they're kinda related." → No. Split.
- Unknown files you're about to `rm`. → Move to `to-delete/`.
- A commit that touches `src/` and `docs/` and `scripts/` in one go. → Split.

---

## Phase 2 — Multi-Worktree Merge Ordering

**Think first:** "If I merge worktree A first, does worktree B need a rebase? Which worktree is the foundation?"

Skip to Phase 3 if you have only one worktree. If you have two or more (typical when parallel subagents have been at work):

1. **Enumerate** with `python3 scripts/list-worktrees.py` — shows each worktree's branch, HEAD, dirty status, unpushed commit count.
2. **Classify each worktree** by what it produces: feature code, docs, infra, tests, etc.
3. **Propose ordering** with `python3 scripts/suggest-merge-order.py --base main` — heuristic: worktree whose branch modifies files that other branches also modify goes first (foundation → leaves).
4. **Agent decides.** The script suggests; you verify against your understanding. Foundation-first means later branches can rebase on a more-complete base. Leaf-last means the last PR is the smallest and most isolated.
5. **Execute in order.** For each worktree, run Phases 1, 3, 4, 5 inside it. Push + PR the first before starting the second so reviewers see the stack in order.

See `references/multi-worktree-merge-order.md` for the full decomposition and the worked example.

**Phase 2 red flags:**
- "I'll just merge them in whatever order I finish." → No. Order matters when branches overlap.
- A worktree has unrelated commits mixed with the parallel subagent's work. → Isolate before proceeding.
- Two worktrees claim they're both the "foundation". → They overlap too much; audit and possibly re-split.

---

## Phase 3 — Commits → Contextually Separated PRs

**Think first:** "If the reviewer reads only the title and summary, do they know what to review?"

### 3.1 Boundaries by reviewer cognitive load

Split when commits touch different domains, have different risk profiles, or a single PR exceeds ~500 lines of meaningful diff. Don't split when two commits must ship together to keep the product working.

### 3.2 Flat or stacked

**Flat** (default): every PR branches off `main` independently. Simpler to review.

**Stacked** (only when PR N genuinely depends on PR N-1's content): child branch's base is the parent branch. Child PR body says "stacked on #N". See `references/worktree-and-stash.md`.

### 3.3 Push and open — fork only

```bash
git push -u origin <branch>

gh pr create \
  --repo <fork-owner>/<fork-repo>      # ALWAYS explicit
  --base <main-or-parent> \
  --head <branch> \
  --title "<emoji> <type>(<scope>): ..." \
  --body-file /tmp/pr-body.md          # from Phase 4
```

Verify immediately:
```bash
gh pr view <number> --repo <fork-owner>/<fork-repo> --json url,baseRefName
```
URL must point to the fork, not upstream. See `references/fork-safety.md`.

**Phase 3 red flags:**
- "One big PR is easier for me to track." → Split by reviewer load.
- `gh pr create` without `--repo`. → Stop.
- PR opened on upstream. → Close it immediately, reopen on fork. See `references/fork-safety.md`.

---

## Phase 4 — PR Body Is a Self-Review

**Think first:** "What would the reviewer ask? Answer it in the body now."

The PR body is not a changelog. It is you reviewing your own work for the reviewer — same tone, same rigor as a good external review. Make "LGTM" easier than "here are five questions".

### 4.1 Structure

Use `python3 scripts/draft-pr-body.py --base <base> --head <head>` to get a skeleton, then hand-edit.

```
# <title>

## Summary                       — 2-4 sentences, punch card
## Context / Why now              — the problem this solves
## The N items                    — per-item: files, rationale, verification
## Files touched                  — aggregate table
## Verification                   — automated + manual, checkbox list
## Risks / Open items             — what the reviewer would ask anyway
## Follow-ups                     — explicit "not in scope"
```

Stay under **50,000 characters**. See `references/pr-body-template.md` and the worked example there.

### 4.2 Self-review voice — receiving-code-review discipline inlined

**Forbidden anywhere in the body:** "You're absolutely right!", "Great point!", "Thanks for …", "Hope this helps", "Please feel free to …", any gratitude or hedging. Use instead: "Fixed. X."  "Pushed back because Y." "Can't verify without Z." Actions over words.

**Verify before you claim.** "Type-check passes" ≠ "tests pass" ≠ "production verified". Say exactly what you ran.

**YAGNI before expansion.** If a section feels like scope creep, grep the codebase for real callers. If unused, remove. PRs shrink by default.

**Pre-empt objections.** If you expect "why not X?", answer it in the body with evidence.

Full pattern set (what to verify before implementing external suggestions, how to gracefully correct your own pushback, GitHub thread replies vs top-level): see `references/receiving-review-patterns.md`. That file is a full inlining of the receiving-code-review discipline — no external skill required.

**Phase 4 red flags:**
- "Thanks for reviewing!" in the body. → Delete.
- Claiming tests passed when you ran only type-check. → Lie. Say exactly what you ran.
- Missing risks section. → Reviewer will wonder why.
- Body > 50,000 chars. → Split the PR.

---

## Phase 5 — Post-PR Verification + Tidy

**Think first:** "What state did I start in? Have I returned to it, plus the intended delta?"

### 5.1 Dispatch a subagent for an independent re-audit

After the last PR opens, launch a subagent to verify the repo is tidy. It reports pass/fail on each item. Brief the subagent with the checklist below and a short context paragraph naming the fork, upstream, and open-PR numbers. See `references/post-pr-verification.md` for the full subagent prompt.

### 5.2 Tidy checklist — all must be true

- [ ] `git status --short` is empty.
- [ ] `git worktree list` shows only the main worktree.
- [ ] `git branch -vv` shows only `main` and open-PR branches. No merged-local branches lingering.
- [ ] `git branch -r` (after `git fetch --prune`) shows only origin/main and remote PR branches. No merged-remote branches lingering.
- [ ] `python3 scripts/audit-state.py` exits 0.
- [ ] `gh pr list --repo <fork>/<repo> --state open` matches what you intended to open.
- [ ] `gh pr list --repo <upstream>/<upstream-repo> --author @me` is empty (nothing accidentally on upstream).

### 5.3 Retire merged branches + worktrees

```bash
# Fetch + prune so the remote list stays accurate
git fetch --all --prune

# Dry-run first: see what would be removed
python3 scripts/retire-merged-branches.py --base main --dry-run

# Execute when you're confident
python3 scripts/retire-merged-branches.py --base main --execute

# Remove worktrees for merged branches
git worktree list
git worktree remove <path-to-retired-worktree>
```

See `scripts/retire-merged-branches.md`. The script refuses to delete `main` / `master` / `default` and refuses to delete branches that are NOT merged to `--base`.

### 5.4 Final cleanliness probe

Re-run `scripts/audit-state.py`. If it says "state is CLEAN", you are done. If not, read the output and fix.

**Phase 5 red flags:**
- "The repo is mostly clean." → No. Tidy is binary. Finish or flag.
- Retire script errored; I ran it with `--force`. → Don't. Retire refuses for a reason.
- Open PR on upstream that wasn't there before. → See `references/fork-safety.md` recovery section.

---

## How To Think — meta-cognition per phase

- **Phase 0:** *What surprises me in this state? Does any of it block safe Phase 1 entry?*
- **Phase 1:** *For each hunk, which of the N concerns does it belong to? If I can't say, I don't understand the change yet — read the code.*
- **Phase 2:** *If I merge worktree A first, do B and C need rebase? The answer tells me which is the foundation.*
- **Phase 3:** *If the reviewer reads only the title + summary, do they know what to review and what to skip?*
- **Phase 4:** *What would the reviewer ask? Pre-empt every foreseeable question.*
- **Phase 5:** *What state did I start in? Have I returned to it plus the intended delta — nothing more, nothing less?*

See `references/agent-thinking-steering.md` for the full mental-model guide (decomposition, ordering, verification, when to stop, when to escalate).

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| `git commit -am "..."` without reading diff | Diff-walk; stage per-concern. |
| `rm` an unknown file | Move to `to-delete/` instead. |
| Opening PR on upstream by accident | `gh pr create` needs `--repo` explicit, every time. |
| Committing `.env` / session artifacts | Check `.gitignore` in Phase 0; extend it if needed. |
| Amending a published commit | New fix commit on top. Never amend. |
| Force-push on reviewed branch | No. Add a commit. |
| PR body says "various improvements" | Rewrite per-item. |
| "Thanks for the review!" in body | Delete. State the fix. |
| Skipping Phase 5 | Merge leaves debris. Retire it. |
| Merging worktrees in arbitrary order | Foundation → leaves. |
| Retiring a not-merged branch with `--force` | Refuse. Merge first. |

## Red Flags

If you catch yourself thinking any of these, stop and re-audit:

- "Let me just squash these together."
- "I'll open this on upstream as a courtesy."
- "This commit is close enough."
- "I'll amend real quick."
- "The reviewer will figure it out from the diff."
- "Thanks for the great PR template!"
- "I'll clean up the worktrees later."
- "The to-delete folder can wait."

## Scripts

Every script lives in `scripts/` and has a paired `<name>.md` doc next to it.

| Script | Purpose | Mutates? |
|---|---|---|
| `scripts/audit-state.py` | Phase 0 state dump: dirty files by domain, worktrees, branches, unpushed commits, fork-vs-upstream PR check. | No |
| `scripts/list-worktrees.py` | Phase 0 / 2: enumerate worktrees with branch + dirty + unpushed. | No |
| `scripts/init-to-delete.py` | Phase 0: create `to-delete/` + add to `.gitignore`. Idempotent. | Yes (one-time) |
| `scripts/suggest-merge-order.py` | Phase 2: propose foundation→leaf merge order for N branches. | No |
| `scripts/draft-pr-body.py` | Phase 4: PR body skeleton from a commit range. | No |
| `scripts/retire-merged-branches.py` | Phase 5: delete local + remote branches merged to `<base>`. Dry-run by default. | Yes (with `--execute`) |

All scripts are Python 3 stdlib only. No dependencies, no `.env`, no secrets. Per-script docs at `scripts/<name>.md`.

## References

- `references/pre-flight-audit.md` — Phase 0 mechanics, `.gitignore` hygiene, surprise-state triage.
- `references/diff-walk-discipline.md` — diff-first commit discipline, `git add -p` recipes, hunk-level splits.
- `references/multi-worktree-merge-order.md` — Phase 2: classify worktrees, compute ordering, execute sequentially.
- `references/to-delete-folder.md` — the `to-delete/` pattern: what goes there, how to flush it, never `rm`.
- `references/scripts-and-docs-layout.md` — `scripts/<name>.<ext>` + `.md` pair; `docs/<context>/NN-title-slug.md` numbered atomics.
- `references/post-pr-verification.md` — Phase 5 subagent dispatch: prompt, checklist, expected report.
- `references/agent-thinking-steering.md` — meta-cognition per phase: decomposition, ordering, verification, when to stop.
- `references/conventional-commits.md` — type + scope registry, gitmoji, body/footer, breaking-change notation.
- `references/pr-body-template.md` — the copy-paste PR body skeleton with worked example. Stay under 50k chars.
- `references/receiving-review-patterns.md` — full inlining of the receiving-code-review discipline (forbidden phrases, verification-first, YAGNI gate, pushback template, GitHub thread replies).
- `references/fork-safety.md` — origin vs upstream verification, `--repo` rule, accidental-upstream recovery, secrets checklist.
- `references/worktree-and-stash.md` — branch/stash/rebase recipes for switching between uncommitted work on different bases.

## Bottom Line

Audit → diff-walk commits → merge-order if multi-worktree → contextual PRs on the fork → self-review bodies → tidy up. Nothing stale, nothing on upstream, every commit read, every PR earned. One discipline, zero exceptions.
